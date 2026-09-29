"""Semantic timeline: word-anchored blocks, timing policy and edit operations (spec §15).

Block boundaries are *decided* editorially (LLM or human) by meaning; this
module only anchors them to word timings and enforces the readability
safeguards, which produce warnings — never meaning-breaking splits.
"""
from __future__ import annotations

from .project import Project, text_hash

LEAD = 0.06        # subtitle appears slightly before the first word
TAIL = 0.30        # linger after the last word when a real pause follows


def words(p: Project) -> list[dict]:
    return p.data["transcript"]["word_timings"]


def anchor_times(p: Project) -> None:
    """(Re)derive start/end of every block from its word range + timing policy."""
    ws = words(p)
    sub = p.cfg["subtitles"]
    tl = [s for s in p.data["timeline"] if s["type"] != "pause"]
    for s in tl:
        if s.get("timing_locked"):
            continue
        a, b = s["source_word_start"], s["source_word_end"]
        s["speech_start"] = ws[a]["start"]
        s["speech_end"] = ws[b]["end"]
        s["start"] = round(max(0.0, ws[a]["start"] - LEAD), 3)
        s["end"] = round(ws[b]["end"] + TAIL, 3)
    tl.sort(key=lambda s: s["start"])
    # Close small gaps: prefer lingering over flashing to black (§15.6, QA gate 11).
    for cur, nxt in zip(tl, tl[1:]):
        gap = nxt["start"] - cur.get("speech_end", cur["end"])
        if gap <= sub["linger_gap_seconds"] + TAIL or cur["end"] > nxt["start"]:
            cur["end"] = nxt["start"]
    p.data["timeline"] = tl


def ar_text(p: Project, a: int, b: int) -> str:
    return " ".join(w["text"] for w in words(p)[a : b + 1])


def readability(p: Project) -> list[dict]:
    sub = p.cfg["subtitles"]
    out = []
    for s in p.data["timeline"]:
        dur = s["end"] - s["start"]
        for lang in ("de", "en"):
            t = (s.get(lang) or "").replace("\n", " ")
            cps = len(t) / dur if dur > 0 else 99
            if cps > sub["max_cps_warning"] and not s.get("deliberate_fast"):
                out.append({"segment": s["id"], "lang": lang, "kind": "READING_SPEED", "cps": round(cps, 1),
                            "message": f"{lang.upper()} {s['id']}: {cps:.1f} Zeichen/s bei {dur:.2f}s"})
        if dur < sub["min_block_seconds"] and not s.get("deliberate_fast"):
            out.append({"segment": s["id"], "kind": "SHORT_BLOCK", "seconds": round(dur, 2),
                        "message": f"{s['id']}: nur {dur:.2f}s sichtbar"})
    return out


# ------------------------------------------------------------------ edits

def _renumber(p: Project) -> None:
    for i, s in enumerate(p.data["timeline"], 1):
        s["id"] = f"seg_{i:03d}"


def set_de(p: Project, seg_id: str, text: str) -> None:
    s = p.segment(seg_id)
    if text != s.get("de"):
        s["de"] = text
        s.pop("layout", None)
        # English is now STALE_EN (hash mismatch) until regenerated/confirmed (§13.5).
        p.data["decisions"].append({"what": "edit_de", "segment": seg_id})


def set_en(p: Project, seg_id: str, text: str, confirm: bool = True) -> None:
    s = p.segment(seg_id)
    s["en"] = text
    s.pop("layout", None)
    if confirm:
        s["en_from_de_hash"] = text_hash(s.get("de"))


def confirm_en(p: Project, seg_id: str) -> None:
    s = p.segment(seg_id)
    s["en_from_de_hash"] = text_hash(s.get("de"))


def split(p: Project, seg_id: str, at_word: int, de: tuple[str, str], en: tuple[str, str] | None) -> None:
    """Paired split at a word anchor (§14.3): DE and EN split at the same point."""
    s = p.segment(seg_id)
    if not (s["source_word_start"] < at_word <= s["source_word_end"]):
        raise ValueError("split point must be inside the block")
    a = dict(s, source_word_end=at_word - 1, de=de[0], timing_locked=False)
    b = dict(s, source_word_start=at_word, de=de[1], timing_locked=False)
    for x in (a, b):
        x.pop("layout", None)
    if en:
        a["en"], b["en"] = en
        a["en_from_de_hash"], b["en_from_de_hash"] = text_hash(de[0]), text_hash(de[1])
    else:
        a["en_from_de_hash"] = b["en_from_de_hash"] = None
    a["ar"] = ar_text(p, a["source_word_start"], a["source_word_end"])
    b["ar"] = ar_text(p, b["source_word_start"], b["source_word_end"])
    i = p.data["timeline"].index(s)
    p.data["timeline"][i : i + 1] = [a, b]
    _renumber(p)
    anchor_times(p)


def merge(p: Project, first_id: str, second_id: str, joiner: str = "\n") -> None:
    a, b = p.segment(first_id), p.segment(second_id)
    if p.data["timeline"].index(b) != p.data["timeline"].index(a) + 1:
        raise ValueError("only neighbouring blocks can be merged")
    stale_en = p.en_status(a) != "OK" or p.en_status(b) != "OK"
    m = dict(a, source_word_end=b["source_word_end"], de=a["de"] + joiner + b["de"],
             en=(a.get("en") or "") + joiner + (b.get("en") or ""), timing_locked=False)
    m["ar"] = ar_text(p, m["source_word_start"], m["source_word_end"])
    m["reference_ids"] = sorted(set(a.get("reference_ids", []) + b.get("reference_ids", [])))
    m.pop("layout", None)
    m["en_from_de_hash"] = None if stale_en else text_hash(m["de"])
    i = p.data["timeline"].index(a)
    p.data["timeline"][i : i + 2] = [m]
    _renumber(p)
    anchor_times(p)


def move_boundary(p: Project, first_id: str, to_word: int) -> None:
    """Drag the boundary between a block and its successor to another word anchor."""
    a = p.segment(first_id)
    i = p.data["timeline"].index(a)
    b = p.data["timeline"][i + 1]
    if not (a["source_word_start"] <= to_word - 1 < b["source_word_end"]):
        raise ValueError("boundary out of range")
    a["source_word_end"], b["source_word_start"] = to_word - 1, to_word
    for s in (a, b):
        s["ar"] = ar_text(p, s["source_word_start"], s["source_word_end"])
        s["timing_locked"] = False
    anchor_times(p)


def set_times(p: Project, seg_id: str, start: float, end: float) -> None:
    s = p.segment(seg_id)
    s["start"], s["end"], s["timing_locked"] = round(start, 3), round(end, 3), True
