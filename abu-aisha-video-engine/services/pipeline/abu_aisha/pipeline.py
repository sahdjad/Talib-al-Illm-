"""Stage orchestration with resume (spec §5 Workflow A–C, §29, §30.7).

Each stage reads/writes the project and saves. A failure records the error
and leaves the last successful state, so `run` can resume without redoing
media analysis or ASR.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from . import asr, layout, media, references, render_input, segmentation
from .paths import BRAND_ASSETS, FONTS_DIR, RENDERER_DIR
from .project import Project, now, text_hash


# ------------------------------------------------------------------ analyze

def analyze(p: Project) -> None:
    p.set_state("ANALYZING")
    src = p.source_path
    info = media.probe(src)
    p.data["source"]["probe"] = info
    if not info["has_audio"]:
        raise RuntimeError("source has no audio stream")
    t_in, t_out = p.trim
    vis = p.data["visual"]
    if info["has_video"]:
        frames = media.sample_frames(src, info["duration"], n=18)
        box = media.content_box(frames)
        subj = media.detect_subject(frames, box)
        texts = media.static_text_regions(frames, box)
        cw, ch = box[2] - box[0], box[3] - box[1]
        vis["analysis"] = {
            "content_box": {"x0": box[0], "y0": box[1], "x1": box[2], "y1": box[3]},
            "container_orientation": media.orientation(info["width"], info["height"]),
            "content_orientation": media.orientation(cw, ch),
            "letterboxed": (cw * ch) < 0.8 * info["width"] * info["height"],
            "subject": subj,
            "static_text_regions": texts,
        }
        plan = media.plan_stage(info, box, subj, texts, p.cfg)
        vis["stage"] = plan["stage"]
        vis["mask_auto"] = plan["mask"]
        vis["freeze_time"] = media.first_usable_frame_time(src, t_in, box)
        speaker_visible = subj["method"] == "face" and subj["hits"] >= max(3, subj["frames"] // 3)
        vis["speaker_visible"] = speaker_visible
    else:
        speaker_visible = False
    requested = p.data["settings"]["mode"]
    suggested = "video" if speaker_visible else "audio_visual"
    vis["mode_suggested"] = suggested
    vis["mode"] = suggested if requested == "auto" else requested  # explicit user choice always wins
    if vis["mode"] == "audio_visual":
        _plan_audio_visual(p)
    lv = media.audio_levels(src, t_in, t_out)
    p.data["source"]["audio_levels"] = lv
    p.save()


def _plan_audio_visual(p: Project) -> None:
    cfg = p.cfg
    H = cfg["video"]["height"]
    fade_end = cfg["mask"]["default_fade_end"]
    p.data["visual"].setdefault("stage", {"y": 0, "height": int(fade_end * H) + 40, "crop": None, "zoom": 1})
    p.data["visual"].setdefault("mask_auto", {"fade_start": cfg["mask"]["default_fade_start"], "fade_end": fade_end,
                                              "reasons": ["audio_visual default"]})
    # Slow Flow: a few percent over the clip, never aggressive (§22.2).
    p.data["visual"]["flow"] = {"zoomFrom": 1.0, "zoomTo": 1.06, "panX": -18, "panY": -10}


# --------------------------------------------------------------- transcribe

def transcribe(p: Project, asr_json: str | None = None) -> None:
    """Local ASR (or re-use of a stored ASR result) → raw transcript + word anchors."""
    p.set_state("TRANSCRIBING")
    t_in, t_out = 0.0, p.data["source"]["probe"]["duration"]  # whole file; trims only filter at render time
    wav = p.path("work", "audio16k.wav")
    if not wav.exists():
        asr.extract_wav(p.source_path, wav, t_in, None)
    if asr_json:
        res = json.loads(Path(asr_json).read_text())
        samples = asr.load_wav(wav)
        words, phrases = [], []
        for ph in res["phrases"]:
            a, b = int(ph["start"] * asr.SAMPLE_RATE), int(ph["end"] * asr.SAMPLE_RATE)
            ws = asr.place_words(ph["text"], ph["start"], ph["end"], samples[a:b], ph["i"], len(words))
            ph = dict(ph, words=[w.i for w in ws])
            phrases.append(ph)
            words.extend(ws)
        result = {"provider": res.get("provider"), "model": res.get("model"), "language": "ar",
                  "phrases": phrases, "words": [w.__dict__ for w in words]}
    else:
        result = asr.transcribe(wav).to_dict()
    tr = p.data["transcript"]
    tr["asr"] = {"provider": result["provider"], "model": result["model"], "at": now()}
    tr["arabic_verbatim_raw"] = result["phrases"]
    tr["word_timings"] = result["words"]
    tr["arabic_verbatim_reviewed"] = [dict(ph) for ph in result["phrases"]]
    tr["confidence_flags"] = references.transcript_flags(result["words"])
    p.save()
    samples = asr.load_wav(wav)
    (p.path("work", "waveform.json")).write_text(json.dumps(media.waveform(samples, asr.SAMPLE_RATE)))


def import_transcript(p: Project, text: str) -> None:
    """Imported Gemini/manual Arabic: aligned to audio, ASR kept as comparison (§10.4)."""
    wav = p.path("work", "audio16k.wav")
    if not wav.exists():
        asr.extract_wav(p.source_path, wav)
    ref = None
    if p.data["transcript"]["arabic_verbatim_raw"]:
        ref = asr.AsrResult("stored", "stored", "ar", [asr.Phrase(**{k: v for k, v in ph.items()})
                                                       for ph in p.data["transcript"]["arabic_verbatim_raw"]], [])
    res = asr.align_imported_text(text, wav, ref)
    tr = p.data["transcript"]
    tr["imported_text"] = text
    tr["asr_comparison"] = tr.get("arabic_verbatim_raw")
    tr["arabic_verbatim_reviewed"] = [ph.__dict__ for ph in res.phrases]
    tr["word_timings"] = [w.__dict__ for w in res.words]
    tr["confidence_flags"] = references.transcript_flags(tr["word_timings"])
    p.save()


# ---------------------------------------------------------------- editorial

def apply_editorial(p: Project, ed: dict) -> None:
    """Import an editorial package (from an LLM provider run or a human editor).

    Expected keys: provider, prompt_versions, speaker, arabic_corrections, segments,
    titles, references, editorial_notes, notes. Segments carry word ranges, DE and
    (optionally) EN. EN is only accepted as derived from the DE given alongside it.
    """
    p.set_state("TRANSLATING_DE")
    tr = p.data["transcript"]
    ws = tr["word_timings"]
    # 1. reviewed Arabic: word-level corrections with audit trail (§11)
    for c in ed.get("arabic_corrections", []):
        w = ws[c["word"]]
        if w["text"] != c["from"]:
            raise ValueError(f"correction mismatch at word {c['word']}: {w['text']} != {c['from']}")
        w["text_raw"] = w["text"]
        w["text"] = c["to"]
        tr["audit"].append({"word": c["word"], "from": c["from"], "to": c["to"], "reason": c["reason"],
                            "lexical_change": c.get("lexical_change", False), "at": now()})
    for ph in tr["arabic_verbatim_reviewed"]:
        ph["text"] = " ".join(ws[i]["text"] for i in ph["words"])
    for f in ed.get("transcript_flags", []):
        tr["confidence_flags"].append(f)
    # 2. speaker (user-supplied identity always wins; editorial only formats it)
    if ed.get("speaker"):
        p.data["speaker"].update({k: v for k, v in ed["speaker"].items() if v})
    # 3. timeline
    p.set_state("SEGMENTING")
    tl = []
    for i, s in enumerate(ed["segments"], 1):
        a, b = s["words"]
        seg = {
            "id": f"seg_{i:03d}",
            "source_word_start": a,
            "source_word_end": b,
            "type": s.get("type", "spoken"),
            "render_type": s.get("render_type", "spoken"),
            "ar": " ".join(ws[k]["text"] for k in range(a, b + 1)),
            "de_draft": s.get("de_draft", s["de"]),
            "de": s["de"],
            "en": s.get("en"),
            "en_from_de_hash": text_hash(s["de"]) if s.get("en") else None,
            "emphasis": s.get("emphasis", []),
            "accent": s.get("accent"),
            "reference_ids": s.get("reference_ids", []),
            "deliberate_fast": s.get("deliberate_fast", False),
            "notes": s.get("notes"),
        }
        tl.append(seg)
    p.data["timeline"] = tl
    segmentation.anchor_times(p)
    p.data["translations"]["de_draft"] = {s["id"]: s["de_draft"] for s in tl}
    p.data["translations"]["provenance"] = {
        "provider": ed.get("provider"), "prompt_versions": ed.get("prompt_versions"), "at": now(),
        "en_source": "de_final",
    }
    p.data["prompts"] = ed.get("prompt_versions", {})
    p.set_state("TRANSLATING_EN")
    # 4. titles, references, editorial context
    if ed.get("titles"):
        p.data["titles"]["suggestions"] = ed["titles"].get("suggestions", [])
        p.data["titles"]["chosen"] = ed["titles"].get("chosen", {})
    p.data["references"] = ed.get("references", [])
    p.data["editorial_notes"] = ed.get("editorial_notes", [])
    if ed.get("notes"):
        p.data["decisions"].extend({"at": now(), "what": n} for n in ed["notes"])
    if ed.get("trim_suggestion"):
        p.data["source"]["trim_suggestion"] = ed["trim_suggestion"]
    p.save()


# ------------------------------------------------------------------- layout

def do_layout(p: Project) -> None:
    p.set_state("COMPOSING")
    cfg = p.cfg
    mask = render_input.effective_mask(p)
    boxes = layout.canvas_boxes(cfg, mask)
    sb = boxes["subtitle"]
    bw, bh = sb["right"] - sb["left"], sb["bottom"] - sb["top"]
    for s in p.data["timeline"]:
        s["layout"] = {}
        for lang in p.data["settings"]["languages"]:
            if s.get(lang):
                s["layout"][lang] = layout.fit_block(s[lang], bw, bh, cfg["subtitles"], cfg["fonts"])
    p.data["titles"]["layout"] = {
        lang: layout.fit_title(t or "", bw, cfg) for lang, t in (p.data["titles"]["chosen"] or {}).items() if t
    }
    p.data["visual"]["boxes"] = boxes
    p.save()


# ---------------------------------------------------------- render assets

def prepare_assets(p: Project, force: bool = False) -> Path:
    """FFmpeg-side media for the renderer, cached by the parameters that produced it."""
    pub = p.root / "render_public"
    pub.mkdir(exist_ok=True)
    cfg = p.cfg
    vis = p.data["visual"]
    t_in, t_out = p.trim
    W, fps = cfg["video"]["width"], cfg["video"]["fps"]
    key = json.dumps({"stage": vis.get("stage"), "trim": [t_in, t_out], "mode": vis["mode"],
                      "freeze": vis.get("freeze_time"), "bg": p.data["settings"].get("background_image")}, sort_keys=True)
    prepared = vis.get("prepared") or {}
    if force or prepared.get("key") != key or not (pub / "audio.wav").exists():
        prepared = {"key": key}
        peak = (p.data["source"].get("audio_levels") or {}).get("max_volume", -99)
        limiter = peak > cfg["audio"]["limiter_if_peak_above_db"]
        media.prepare_audio(p.source_path, pub / "audio.wav", t_in, t_out, limiter)
        prepared["audio"] = "audio.wav"
        prepared["limiter"] = limiter
        st = vis["stage"]
        if vis["mode"] == "video":
            media.prepare_stage_video(p.source_path, pub / "stage.mp4", st["crop"], W, st["height"], fps, t_in, t_out,
                                      cfg["stage"]["sharpen"])
            prepared["stage_video"] = "stage.mp4"
            freeze_t = max(t_in, vis.get("freeze_time") or t_in)
            media.prepare_freeze(p.source_path, pub / "freeze.png", freeze_t, st["crop"], W, st["height"], cfg["stage"]["sharpen"])
            prepared["freeze"] = "freeze.png"
        else:
            bg = p.data["settings"].get("background_image")
            if bg:
                shutil.copy2(bg, pub / ("still" + Path(bg).suffix))
                prepared["still"] = "still" + Path(bg).suffix
            else:
                box = vis.get("analysis", {}).get("content_box")
                crop = st.get("crop") or ({"x": box["x0"], "y": box["y0"], "w": box["x1"] - box["x0"], "h": box["y1"] - box["y0"]} if box else None)
                if crop is None:
                    raise RuntimeError("audio_visual mode needs a background image (no video frame available)")
                media.prepare_freeze(p.source_path, pub / "still.png", vis.get("freeze_time") or t_in, crop, W, st["height"])
                prepared["still"] = "still.png"
            prepared["freeze"] = None
        vis["prepared"] = prepared
    # fonts + brand (always refreshed, cheap)
    (pub / "fonts").mkdir(exist_ok=True)
    for f in FONTS_DIR.glob("*.ttf"):
        if not (pub / "fonts" / f.name).exists():
            shutil.copy2(f, pub / "fonts" / f.name)
    (pub / "brand").mkdir(exist_ok=True)
    for f in BRAND_ASSETS.glob("*.png"):
        shutil.copy2(f, pub / "brand" / f.name)
    p.save()
    return pub


# ------------------------------------------------------------------- render

def render(p: Project, lang: str, *, preview: bool = False, debug: bool = False, stills: list[int] | None = None,
           out: Path | None = None) -> Path:
    pub = prepare_assets(p)
    ri = render_input.build(p, lang, debug=debug)
    inp = p.path("work", f"render_input_{lang}.json")
    inp.write_text(json.dumps(ri, ensure_ascii=False, indent=1))
    if stills:
        out = out or p.path("previews", f"still_{lang}")
        cmd = ["node", str(RENDERER_DIR / "render.mjs"), str(inp), str(pub), str(out), "--still=" + ",".join(map(str, stills))]
        subprocess.run(cmd, check=True, cwd=RENDERER_DIR)
        return out
    name = f"{lang}_preview.mp4" if preview else f"AbuAisha_{lang.upper()}_1080x1920.mp4"
    out = out or p.path("previews" if preview else "renders", name)
    p.set_state("RENDERING")
    p.save()
    cmd = ["node", str(RENDERER_DIR / "render.mjs"), str(inp), str(pub), str(out)] + (["--preview"] if preview else [])
    t0 = time.time()
    entry = {"at": now(), "lang": lang, "preview": preview, "output": str(out.relative_to(p.root)), "command": cmd,
             "prompt_versions": p.data.get("prompts"), "render_input": str(inp.relative_to(p.root))}
    try:
        subprocess.run(cmd, check=True, cwd=RENDERER_DIR)
    except subprocess.CalledProcessError as e:
        entry["status"] = "FAILED"
        _record_render(p, entry, error=str(e))
        raise
    mux_original_audio(p, out)
    entry["seconds"] = round(time.time() - t0, 1)
    entry["verify"] = verify_output(p, out, preview)
    entry["status"] = "OK" if entry["verify"]["ok"] else "CHECK"
    _record_render(p, entry, state="PREVIEW_READY" if preview else "REVIEW_REQUIRED")
    return out


def _record_render(p: Project, entry: dict, state: str | None = None, error: str | None = None) -> None:
    """Re-read project.json before writing: edits made in the UI while a render ran must not be lost."""
    fresh = Project.open(p.root)
    fresh.data["render_history"].append(entry)
    if error:
        fresh.fail("render", error)  # state stays at the last successful one
    elif state:
        fresh.set_state(state)
    fresh.save()
    p.data = fresh.data


def mux_original_audio(p: Project, video: Path) -> None:
    """FFmpeg owns the final audio (§9, §30.3): the Shaykh's original track, 0 dB, placed
    sample-exactly after the intro; AAC priming is handled by FFmpeg's edit list.
    Also moves the moov atom to the front (web fast-start)."""
    pub = p.root / "render_public"
    intro = p.data["settings"]["intro_duration"] if p.data["settings"]["intro"] else 0
    ms = int(round(intro * 1000))
    tmp = video.with_suffix(".mux.mp4")
    af = (f"[1:a]adelay=delays={ms}:all=1," if ms else "[1:a]") + "apad[a]"
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(pub / "audio.wav"), "-filter_complex", af,
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-shortest",
        "-movflags", "+faststart", str(tmp),
    ], check=True)
    tmp.replace(video)


def faststart(path: Path) -> None:
    tmp = path.with_suffix(".fs.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-c", "copy", "-movflags", "+faststart", str(tmp)], check=True)
    tmp.replace(path)


def verify_output(p: Project, out: Path, preview: bool) -> dict:
    info = media.probe(out)
    cfg = p.cfg
    t_in, t_out = p.trim
    intro = p.data["settings"]["intro_duration"] if p.data["settings"]["intro"] else 0
    expected = intro + (t_out - t_in)
    scale = cfg["render"]["preview_scale"] if preview else 1
    checks = {
        "opens": True,
        "has_audio": info["has_audio"],
        "size_ok": (info.get("width"), info.get("height")) == (round(cfg["video"]["width"] * scale), round(cfg["video"]["height"] * scale)),
        "fps_ok": abs(info.get("fps", 0) - cfg["video"]["fps"]) < 0.01,
        "duration_ok": abs(info["duration"] - expected) < 0.1,
    }
    return {"ok": all(checks.values()), **checks, "duration": info["duration"], "expected": round(expected, 3)}


# ------------------------------------------------------------ verification

def verify_references(p: Project) -> list[dict]:
    """Rule-based span detection + Qurʾān text matching (§12). Adds references,
    never removes editorial decisions. Unverifiable spans stay CHECK_REQUIRED."""
    from . import quran

    ws = p.data["transcript"]["word_timings"]
    refs = p.data["references"]
    known = {(r.get("type"), r.get("word_start")) for r in refs}
    found = []
    for sp in references.detect_spans(ws):
        if sp["type"] == "HONORIFIC":
            continue
        key = (sp["type"], sp["word"])
        if key in known:
            continue
        found.append({"id": f"ref_auto_{len(refs) + len(found) + 1:03d}", "type": sp["type"], "word_start": sp["word"],
                      "label": f"{sp['label']}: „{sp['match']}“ @ {ws[sp['word']]['start']:.1f}s",
                      "status": "CHECK_REQUIRED", "evidence": "Stichwort-Erkennung (regelbasiert)", "segments": []})
    idx = quran.default_index()
    qa_note = {"quran_index": bool(idx)}
    if idx:
        for h in idx.scan(ws):
            if ("QURAN_QUOTE", h["word_start"]) in known:
                continue
            ref = {"id": f"ref_q_{h['sura']}_{h['aya_from']}", "type": "QURAN_QUOTE", "word_start": h["word_start"],
                   "word_end": h["word_end"], "label": h["label"], "status": h["status"], "canonical_ar": h["canonical_ar"],
                   "coverage": h["coverage"], "partial_recitation": h["partial_recitation"],
                   "evidence": "Textabgleich mit konfiguriertem Qurʾān-Text", "segments": []}
            found.append(ref)
            p.data["editorial_notes"].append({
                "id": f"ed_{ref['id']}", "kind": "quran_ref", "text": {"all": ref["label"]}, "dir": "ltr",
                "start": ws[h["word_start"]]["start"], "end": ws[h["word_end"]]["end"] + 1.5,
                "status": h["status"], "enabled": h["status"].startswith("VERIFIED"), "reference_id": ref["id"],
                "provenance": "Automatische Qurʾān-Referenz (Textabgleich)",
            })
    refs.extend(found)
    for r in refs:
        if r.get("word_start") is None:
            continue
        for s in p.data["timeline"]:
            if s["source_word_start"] <= r["word_start"] <= s["source_word_end"] and r["id"] not in s.get("reference_ids", []):
                s.setdefault("reference_ids", []).append(r["id"])
    p.data["verification"] = dict(qa_note, at=now(), new_references=len(found))
    p.save()
    return found


def stage_status(p: Project) -> dict:
    d = p.data
    return {
        "analyzed": bool(d["source"].get("probe") and d["visual"].get("stage")),
        "transcribed": bool(d["transcript"]["word_timings"]),
        "editorial": bool(d["timeline"]),
        "layout": bool(d["timeline"]) and all(s.get("layout") for s in d["timeline"]),
        "verified": bool(d.get("verification")),
        "qa": bool(d.get("qa")),
        "rendered": sorted({r["lang"] for r in d["render_history"] if not r["preview"] and r.get("status") == "OK"}),
    }


def run_all(p: Project, *, provider=None, langs: list[str] | None = None, preview: bool = False, render_final: bool = True) -> None:
    """Resume from the last successful stage (§29 'LLM unavailable', 'Render crash')."""
    from . import exports, qa

    st = stage_status(p)
    stage = "analyze"
    try:
        if not st["analyzed"]:
            analyze(p)
        stage = "transcribe"
        if not st["transcribed"]:
            transcribe(p)
        stage = "editorial"
        if not st["editorial"]:
            if provider is None:
                raise RuntimeError("no editorial yet: pass --provider (claude model id or file:editorial.json)")
            apply_editorial(p, provider.editorial(p))
        stage = "verify"
        if not st["verified"]:
            verify_references(p)
        stage = "layout"
        do_layout(p)
        stage = "assets"
        prepare_assets(p)
        stage = "qa"
        qa.run(p)
        stage = "render"
        for lang in langs or p.data["settings"]["languages"]:
            if preview:
                render(p, lang, preview=True)
            if render_final:
                render(p, lang)
        stage = "qa"
        qa.run(p)
        exports.export_all(p)
    except Exception as e:  # keep last good state, record error, re-raise
        p.fail(stage, repr(e))
        p.save()
        raise
