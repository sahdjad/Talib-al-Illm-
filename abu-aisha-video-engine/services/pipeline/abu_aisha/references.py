"""Religious-content detection and verification flags (spec §12, §24).

Detection here is deliberately conservative and rule-based; it only raises
flags. A reference becomes VERIFIED only through a verification adapter
(Qurʾān text match, see quran.py) or explicit human approval. Nothing in this
module invents a source.
"""
from __future__ import annotations

import re

# Arabic cue phrases → span type. Matched on normalised text.
CUES: list[tuple[str, str, str]] = [
    (r"قال (الله )?تعالى|يقول (الله )?تعالى|قوله تعالى|قال الله|يقول الله|قال ربنا|﴿", "QURAN_QUOTE", "Qurʾān-Zitat möglich"),
    (r"قال (رسول الله|النبي)|يقول (رسول الله|النبي)|صلى الله عليه وسلم|عليه الصلاة والسلام|قوله ﷺ", "HADITH_QUOTE", "Ḥadīth-Zitat möglich"),
    (r"رواه|أخرجه|في الصحيحين|صحيح البخاري|صحيح مسلم|السنن|المسند", "HADITH_QUOTE", "Ḥadīth-Quellenangabe erwähnt"),
    (r"قال (الإمام|الشيخ|شيخ الإسلام|ابن |العلامة|الحافظ)|يقول (الإمام|الشيخ|شيخ الإسلام|ابن |العلامة|الحافظ)", "SCHOLAR_QUOTE", "Gelehrtenzitat"),
    (r"في كتاب|في كتابه|كتاب ", "BOOK_REFERENCE", "Buchnennung"),
    (r"سنة \d+|توفي|المتوفى|القرن", "HISTORICAL_FACT", "Historische Angabe"),
    (r"حفظه الله|رحمه الله|رضي الله عن|رحمهم الله", "HONORIFIC", "Ehrenformel"),
]

_DIACRITICS = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")


def normalize_ar(s: str) -> str:
    s = _DIACRITICS.sub("", s)
    s = re.sub("[إأآٱ]", "ا", s)
    s = s.replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")
    return re.sub(r"\s+", " ", s).strip()


def detect_spans(words: list[dict]) -> list[dict]:
    """Scan the reviewed transcript for cue phrases (word index ranges)."""
    text_words = [w["text"] for w in words]
    out = []
    joined = ""
    starts = []
    for i, t in enumerate(text_words):
        starts.append(len(joined))
        joined += t + " "
    for pattern, kind, label in CUES:
        for m in re.finditer(pattern, joined):
            wi = max(i for i, s in enumerate(starts) if s <= m.start())
            out.append({"type": kind, "word": wi, "match": m.group(0).strip(), "label": label})
    return out


def transcript_flags(words: list[dict]) -> list[dict]:
    """CHECK_TRANSCRIPT flags for spans ASR typically gets wrong (§10.3)."""
    flags = []
    for sp in detect_spans(words):
        if sp["type"] in ("QURAN_QUOTE", "HADITH_QUOTE", "SCHOLAR_QUOTE", "BOOK_REFERENCE", "HISTORICAL_FACT"):
            flags.append({"kind": "CHECK_TRANSCRIPT", "word": sp["word"], "reason": sp["label"] + " — Wortlaut prüfen",
                          "time": words[sp["word"]]["start"]})
    for w in words:
        if re.search(r"\d", w["text"]):
            flags.append({"kind": "CHECK_TRANSCRIPT", "word": w["i"], "reason": "Zahl im Transkript", "time": w["start"]})
    return flags


REFERENCE_STATES = ("VERIFIED_EXACT", "VERIFIED_GENERAL", "CHECK_REQUIRED", "UNVERIFIED")


def renderable(ref_or_note: dict) -> bool:
    return ref_or_note.get("status") in ("VERIFIED_EXACT", "VERIFIED_GENERAL", "APPROVED")
