"""Arabic ASR adapter (spec §10).

Default provider: Whisper large-v3 (ONNX, int8) through sherpa-onnx, local and
offline, with Silero VAD so non-speech is never sent to the decoder (reduces
hallucination). Whisper-ONNX does not emit word timestamps, so word anchors are
derived in two steps:

1. VAD phrases give hard anchors at every real pause of the speaker.
2. Inside a phrase, words are placed by an energy-aware proportional model:
   micro-pauses (short low-energy dips) are snapped to the nearest word gap.

The result is good enough to hang semantic subtitle blocks on, and every
boundary stays editable in the review step. A forced aligner (WhisperX, MMS)
can replace step 2 behind the same interface (``AsrResult``).

Imported transcripts (Gemini, manual) go through ``align_imported_text`` which
re-uses the same phrase anchors instead of discarding the user's text.
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field, asdict
from pathlib import Path

import numpy as np

SAMPLE_RATE = 16000


@dataclass
class Word:
    i: int
    text: str
    start: float
    end: float
    phrase: int
    confidence: float = 1.0


@dataclass
class Phrase:
    i: int
    start: float
    end: float
    text: str
    words: list[int] = field(default_factory=list)


@dataclass
class AsrResult:
    provider: str
    model: str
    language: str
    phrases: list[Phrase]
    words: list[Word]

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "language": self.language,
            "phrases": [asdict(p) for p in self.phrases],
            "words": [asdict(w) for w in self.words],
        }


def extract_wav(src: str | Path, dst: str | Path, trim_in: float = 0.0, trim_out: float | None = None) -> Path:
    cmd = ["ffmpeg", "-v", "error", "-y"]
    if trim_in:
        cmd += ["-ss", f"{trim_in:.3f}"]
    cmd += ["-i", str(src)]
    if trim_out is not None:
        cmd += ["-t", f"{trim_out - trim_in:.3f}"]
    cmd += ["-vn", "-ac", "1", "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(dst)]
    subprocess.run(cmd, check=True)
    return Path(dst)


def load_wav(path: str | Path) -> np.ndarray:
    import soundfile as sf

    data, sr = sf.read(str(path), dtype="float32")
    if data.ndim > 1:
        data = data.mean(axis=1)
    assert sr == SAMPLE_RATE, sr
    return data


def model_dir() -> Path:
    d = os.environ.get("ABU_AISHA_ASR_MODEL_DIR")
    if not d:
        raise RuntimeError(
            "ABU_AISHA_ASR_MODEL_DIR is not set. Point it at a sherpa-onnx Whisper model "
            "directory (see services/pipeline/README.md → ASR models)."
        )
    return Path(d)


def _find(d: Path, pattern: str) -> str:
    hits = sorted(d.glob(pattern))
    if not hits:
        raise FileNotFoundError(f"{pattern} not found in {d}")
    return str(hits[0])


def vad_phrases(samples: np.ndarray, min_silence: float = 0.25, max_speech: float = 25.0) -> list[tuple[float, float]]:
    """Speech regions as (start, end) seconds using Silero VAD."""
    import sherpa_onnx

    vad_model = os.environ.get("ABU_AISHA_VAD_MODEL") or str(model_dir().parent / "silero_vad.onnx")
    cfg = sherpa_onnx.VadModelConfig()
    cfg.silero_vad.model = vad_model
    cfg.silero_vad.min_silence_duration = min_silence
    cfg.silero_vad.min_speech_duration = 0.2
    cfg.silero_vad.max_speech_duration = max_speech
    cfg.silero_vad.threshold = 0.45
    cfg.sample_rate = SAMPLE_RATE
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=120)
    win = cfg.silero_vad.window_size
    out: list[tuple[float, float]] = []
    padded = np.concatenate([samples, np.zeros(SAMPLE_RATE, dtype=np.float32)])
    for k in range(0, len(padded) - win + 1, win):
        vad.accept_waveform(padded[k : k + win])
        while not vad.empty():
            seg = vad.front
            s = seg.start / SAMPLE_RATE
            out.append((s, s + len(seg.samples) / SAMPLE_RATE))
            vad.pop()
    vad.flush()
    while not vad.empty():
        seg = vad.front
        s = seg.start / SAMPLE_RATE
        out.append((s, s + len(seg.samples) / SAMPLE_RATE))
        vad.pop()
    return out


def _hex_tokens_file(tokens_path: str) -> str:
    """sherpa-onnx decodes every BPE token to text on its own, which silently drops
    Arabic letters whose UTF-8 bytes are split across two tokens (e.g. الزوج → الوج).
    We hand it a tokens file whose symbols are the hex of the original bytes and
    join the bytes ourselves (see ``_decode_tokens``)."""
    import base64
    import hashlib

    cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "abu-aisha"
    cache.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(Path(tokens_path).read_bytes()).hexdigest()[:12]
    out = cache / f"hex-tokens-{digest}.txt"
    if not out.exists():
        lines = []
        for raw in Path(tokens_path).read_bytes().splitlines():
            parts = raw.rsplit(b" ", 1)
            if len(parts) != 2:
                continue
            sym = base64.b64decode(parts[0]).hex() + "|"
            lines.append(base64.b64encode(sym.encode()).decode() + " " + parts[1].decode())
        out.write_text("\n".join(lines) + "\n")
    return str(out)


def _decode_tokens(tokens: list[str]) -> str:
    buf = bytearray()
    for t in tokens:
        for piece in t.strip().split("|"):
            if piece:
                try:
                    buf += bytes.fromhex(piece)
                except ValueError:
                    buf += piece.encode()
    return re.sub(r"\s+", " ", buf.decode("utf-8", errors="replace")).strip()


def _recognizer():
    import sherpa_onnx

    d = model_dir()
    return sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=_find(d, "*encoder*.onnx"),
        decoder=_find(d, "*decoder*.onnx"),
        tokens=_hex_tokens_file(_find(d, "*tokens.txt")),
        language="ar",
        task="transcribe",
        num_threads=max(1, (os.cpu_count() or 2)),
        tail_paddings=800,
    )


def _energy_dips(chunk: np.ndarray, hop: float = 0.01, min_len: float = 0.09) -> list[tuple[float, float]]:
    """Low-energy stretches (micro pauses) inside a phrase, in seconds relative to chunk."""
    h = int(hop * SAMPLE_RATE)
    if len(chunk) < h * 5:
        return []
    frames = len(chunk) // h
    rms = np.sqrt(np.mean(chunk[: frames * h].reshape(frames, h) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms)
    thr = np.percentile(db, 90) - 22
    low = db < thr
    dips = []
    k = 0
    while k < frames:
        if low[k]:
            j = k
            while j < frames and low[j]:
                j += 1
            if (j - k) * hop >= min_len and k > 0 and j < frames:
                dips.append((k * hop, j * hop))
            k = j
        else:
            k += 1
    return dips


_WORD_RE = re.compile(r"\S+")


def place_words(text: str, start: float, end: float, chunk: np.ndarray | None, phrase_i: int, first_i: int) -> list[Word]:
    toks = _WORD_RE.findall(text)
    if not toks:
        return []
    weights = np.array([max(1, len(t.replace("ـ", ""))) + 1.2 for t in toks], dtype=float)
    dur = end - start
    dips = _energy_dips(chunk) if chunk is not None else []
    # A dip touching the phrase edge is leading/trailing silence inside the VAD
    # region: shrink the phrase instead of treating it as a word gap.
    for a, b in list(dips):
        if a < 0.2 and a < dur * 0.2:
            start, dur = start + b, dur - b
            dips = [(x - b, y - b) for x, y in dips if (x, y) != (a, b)]
        elif b > dur - 0.2:
            dur = a
            dips = [(x, y) for x, y in dips if (x, y) != (a, b)]
            end = start + dur
    dips = [(a, b) for a, b in dips if 0 < a and b < dur]
    # Remove dip time from the speaking budget, then map proportional positions around dips.
    speak = dur - sum(b - a for a, b in dips)
    if speak <= 0.2:
        dips, speak = [], dur
    cum = np.concatenate([[0], np.cumsum(weights)]) / weights.sum() * speak

    def to_time(x: float) -> float:
        t = x
        for a, b in dips:  # push past pauses that precede this speaking position
            if t >= a:
                t += b - a
        return start + min(t, dur)

    bounds = [to_time(x) for x in cum]
    # Snap each dip to the nearest word boundary so words never straddle a pause.
    for a, b in dips:
        mid = start + (a + b) / 2
        k = int(np.argmin([abs(x - mid) for x in bounds[1:-1]])) + 1 if len(bounds) > 2 else None
        if k is not None and abs(bounds[k] - mid) < 0.6:
            bounds[k] = start + a  # word k-1 ends at dip start
    words = []
    for n, t in enumerate(toks):
        s = bounds[n]
        e = bounds[n + 1]
        # word after a snapped dip starts at the dip end
        for a, b in dips:
            if abs(s - (start + a)) < 1e-6 and n > 0:
                s = start + b
        words.append(Word(i=first_i + n, text=t, start=round(s, 3), end=round(max(e, s + 0.12), 3), phrase=phrase_i))
    return words


def transcribe(wav: str | Path) -> AsrResult:
    samples = load_wav(wav)
    regions = vad_phrases(samples)
    rec = _recognizer()
    phrases: list[Phrase] = []
    words: list[Word] = []
    for pi, (s, e) in enumerate(regions):
        a = max(0, int((s - 0.05) * SAMPLE_RATE))
        b = min(len(samples), int((e + 0.05) * SAMPLE_RATE))
        chunk = samples[a:b]
        st = rec.create_stream()
        st.accept_waveform(SAMPLE_RATE, chunk)
        rec.decode_stream(st)
        text = _decode_tokens(st.result.tokens)
        ph = Phrase(i=len(phrases), start=round(s, 3), end=round(e, 3), text=text)
        ws = place_words(text, s, e, samples[int(s * SAMPLE_RATE) : int(e * SAMPLE_RATE)], ph.i, len(words))
        ph.words = [w.i for w in ws]
        phrases.append(ph)
        words.extend(ws)
    return AsrResult(provider="sherpa-onnx", model=model_dir().name, language="ar", phrases=phrases, words=words)


def align_imported_text(text: str, wav: str | Path, reference: AsrResult | None = None) -> AsrResult:
    """Align an imported (Gemini/manual) Arabic transcript to the audio (spec §10.4).

    Uses VAD phrase anchors. If an ASR reference exists, imported words are
    distributed over phrases in proportion to the number of words ASR heard in
    each phrase (robust to small ASR errors); otherwise by phrase duration.
    """
    samples = load_wav(wav)
    regions = [(p.start, p.end) for p in reference.phrases] if reference else vad_phrases(samples)
    toks = _WORD_RE.findall(text)
    if reference:
        counts = np.array([max(1, len(p.words)) for p in reference.phrases], dtype=float)
    else:
        counts = np.array([e - s for s, e in regions])
    shares = np.round(np.cumsum(counts) / counts.sum() * len(toks)).astype(int)
    phrases, words, prev = [], [], 0
    for pi, ((s, e), cut) in enumerate(zip(regions, shares)):
        part = " ".join(toks[prev:cut])
        prev = cut
        ph = Phrase(i=pi, start=s, end=e, text=part)
        ws = place_words(part, s, e, samples[int(s * SAMPLE_RATE) : int(e * SAMPLE_RATE)], pi, len(words))
        ph.words = [w.i for w in ws]
        phrases.append(ph)
        words.extend(ws)
    return AsrResult(provider="import+align", model="vad-proportional", language="ar", phrases=phrases, words=words)


if __name__ == "__main__":  # pragma: no cover
    import json
    import sys

    src = sys.argv[1]
    with tempfile.TemporaryDirectory() as td:
        wav = extract_wav(src, Path(td) / "a.wav")
        res = transcribe(wav)
    json.dump(res.to_dict(), sys.stdout, ensure_ascii=False, indent=1)
