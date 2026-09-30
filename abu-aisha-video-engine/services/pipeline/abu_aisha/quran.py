"""Qurʾān verification adapter (spec §12.1).

Matches spoken Arabic against a canonical Qurʾān text using normalised word
trigrams. Only a text match can make a Qurʾān reference VERIFIED — the LLM may
only *propose* candidates.

The canonical text is configured, not bundled (licensing: e.g. Tanzil
"simple-clean", CC-BY 3.0, verbatim copies only). Supported files:

* Tanzil text export:   ``sura|aya|text`` per line
* JSON list of surahs:  ``[{"id", "name", "transliteration", "verses": [{"id", "text"}]}]``

Set ``ABU_AISHA_QURAN_TEXT=/path/to/file``. Without it every Qurʾān span stays
CHECK_REQUIRED (no guessing).
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from .references import normalize_ar

# Transliterated sūrah names for the shared DE/EN reference label (Sūrat al-… [s:a]).
SURAH_NAMES = [
    "al-Fātiḥah", "al-Baqarah", "Āl ʿImrān", "an-Nisāʾ", "al-Māʾidah", "al-Anʿām", "al-Aʿrāf", "al-Anfāl", "at-Tawbah",
    "Yūnus", "Hūd", "Yūsuf", "ar-Raʿd", "Ibrāhīm", "al-Ḥijr", "an-Naḥl", "al-Isrāʾ", "al-Kahf", "Maryam", "Ṭā Hā",
    "al-Anbiyāʾ", "al-Ḥajj", "al-Muʾminūn", "an-Nūr", "al-Furqān", "ash-Shuʿarāʾ", "an-Naml", "al-Qaṣaṣ", "al-ʿAnkabūt",
    "ar-Rūm", "Luqmān", "as-Sajdah", "al-Aḥzāb", "Sabaʾ", "Fāṭir", "Yā Sīn", "aṣ-Ṣāffāt", "Ṣād", "az-Zumar", "Ghāfir",
    "Fuṣṣilat", "ash-Shūrā", "az-Zukhruf", "ad-Dukhān", "al-Jāthiyah", "al-Aḥqāf", "Muḥammad", "al-Fatḥ", "al-Ḥujurāt",
    "Qāf", "adh-Dhāriyāt", "aṭ-Ṭūr", "an-Najm", "al-Qamar", "ar-Raḥmān", "al-Wāqiʿah", "al-Ḥadīd", "al-Mujādilah",
    "al-Ḥashr", "al-Mumtaḥanah", "aṣ-Ṣaff", "al-Jumuʿah", "al-Munāfiqūn", "at-Taghābun", "aṭ-Ṭalāq", "at-Taḥrīm",
    "al-Mulk", "al-Qalam", "al-Ḥāqqah", "al-Maʿārij", "Nūḥ", "al-Jinn", "al-Muzzammil", "al-Muddaththir", "al-Qiyāmah",
    "al-Insān", "al-Mursalāt", "an-Nabaʾ", "an-Nāziʿāt", "ʿAbasa", "at-Takwīr", "al-Infiṭār", "al-Muṭaffifīn",
    "al-Inshiqāq", "al-Burūj", "aṭ-Ṭāriq", "al-Aʿlā", "al-Ghāshiyah", "al-Fajr", "al-Balad", "ash-Shams", "al-Layl",
    "aḍ-Ḍuḥā", "ash-Sharḥ", "at-Tīn", "al-ʿAlaq", "al-Qadr", "al-Bayyinah", "az-Zalzalah", "al-ʿĀdiyāt", "al-Qāriʿah",
    "at-Takāthur", "al-ʿAṣr", "al-Humazah", "al-Fīl", "Quraysh", "al-Māʿūn", "al-Kawthar", "al-Kāfirūn", "an-Naṣr",
    "al-Masad", "al-Ikhlāṣ", "al-Falaq", "an-Nās",
]


def label(sura: int, aya_from: int, aya_to: int | None = None) -> str:
    ayas = f"{aya_from}" if not aya_to or aya_to == aya_from else f"{aya_from}–{aya_to}"
    return f"Sūrat {SURAH_NAMES[sura - 1]} [{sura}:{ayas}]"


def _norm_words(s: str) -> list[str]:
    """Rasm-like skeleton: robust to Uthmani vs. imlāʾī spelling (dagger alif, hamza seats, alif wasla)."""
    s = normalize_ar(s.replace("ٱ", "ا"))
    s = "".join(ch for ch in s if ch.isalpha() or ch.isspace())
    out = []
    for w in s.split():
        if w.startswith("ال") and len(w) > 3:
            w = w[2:]
        w = w.replace("ا", "").replace("ء", "")
        if w:
            out.append(w)
    return out


class QuranIndex:
    def __init__(self, verses: list[tuple[int, int, str]]):
        self.verses = verses
        self.words = [_norm_words(t) for _, _, t in verses]
        self.tri: dict[tuple, set[int]] = defaultdict(set)
        for vi, ws in enumerate(self.words):
            for k in range(len(ws) - 2):
                self.tri[tuple(ws[k : k + 3])].add(vi)

    @classmethod
    def load(cls, path: str | Path) -> "QuranIndex":
        path = Path(path)
        verses = []
        if path.suffix == ".json":
            for s in json.loads(path.read_text()):
                for v in s["verses"]:
                    verses.append((int(s["id"]), int(v["id"]), v["text"]))
        else:
            for line in path.read_text().splitlines():
                parts = line.split("|")
                if len(parts) == 3 and parts[0].isdigit():
                    verses.append((int(parts[0]), int(parts[1]), parts[2]))
        return cls(verses)

    def match(self, spoken: str) -> dict | None:
        """Best verse for a spoken span. coverage = share of spoken trigrams found in the verse."""
        ws = _norm_words(spoken)
        if len(ws) < 3:
            return None
        grams = [tuple(ws[k : k + 3]) for k in range(len(ws) - 2)]
        votes: dict[int, int] = defaultdict(int)
        for g in grams:
            for vi in self.tri.get(g, ()):
                votes[vi] += 1
        if not votes:
            return None
        # allow a quotation spanning two consecutive verses
        best_vi = max(votes, key=lambda v: (votes[v] + votes.get(v + 1, 0) * 0.5, -v))
        cov = votes[best_vi] / len(grams)
        span_to = best_vi
        nxt = best_vi + 1
        if nxt < len(self.verses) and votes.get(nxt) and self.verses[nxt][0] == self.verses[best_vi][0]:
            cov = min(1.0, (votes[best_vi] + votes[nxt]) / len(grams))
            span_to = nxt
        s, a, text = self.verses[best_vi]
        joined = " ".join(self.words[best_vi] + (self.words[span_to] if span_to != best_vi else []))
        exact = " ".join(ws) in joined
        status = "VERIFIED_EXACT" if exact else "VERIFIED_GENERAL" if cov >= 0.8 else "CHECK_REQUIRED"
        return {"sura": s, "aya_from": a, "aya_to": self.verses[span_to][1], "coverage": round(cov, 2),
                "canonical_ar": text if span_to == best_vi else text + " ۝ " + self.verses[span_to][2],
                "label": label(s, a, self.verses[span_to][1]), "status": status,
                "partial_recitation": not exact or len(ws) < len(self.words[best_vi]) * 0.9}

    def scan(self, words: list[dict], window: int = 5, min_cov: float = 0.8) -> list[dict]:
        """Find recited spans in a transcript without relying on cue phrases."""
        hits = []
        texts = [w["text"] for w in words]
        k = 0
        while k + window <= len(texts):
            m = self.match(" ".join(texts[k : k + window]))
            if m and m["coverage"] >= min_cov:
                j = k + window
                while j < len(texts):
                    m2 = self.match(" ".join(texts[k : j + 1]))
                    if not m2 or m2["coverage"] < min_cov:
                        break
                    m, j = m2, j + 1
                if hits and hits[-1]["sura"] == m["sura"] and hits[-1]["aya_to"] >= m["aya_from"] - 1 and hits[-1]["word_end"] >= k - 3:
                    merged = self.match(" ".join(texts[hits[-1]["word_start"] : j]))
                    if merged and merged["coverage"] >= min_cov:
                        hits[-1] = dict(merged, word_start=hits[-1]["word_start"], word_end=j - 1)
                        k = j
                        continue
                hits.append(dict(m, word_start=k, word_end=j - 1))
                k = j
            else:
                k += 1
        return hits


@lru_cache(maxsize=1)
def default_index() -> QuranIndex | None:
    p = os.environ.get("ABU_AISHA_QURAN_TEXT")
    return QuranIndex.load(p) if p and Path(p).exists() else None
