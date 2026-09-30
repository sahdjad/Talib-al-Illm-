"""Editorial LLM providers (spec §30.6, §32, §33).

All providers produce the same *editorial package* that
``pipeline.apply_editorial`` imports:

    {provider, prompt_versions, speaker, arabic_corrections, transcript_flags,
     segments[{words:[a,b], de, en, notes}], titles, references, editorial_notes,
     trim_suggestion, notes}

* ``ClaudeProvider``  – Claude API (Anthropic SDK), two passes:
  1. Arabic cleanup + German master + semantic segmentation + references + titles
  2. English from the FINAL German (separate call, Arabic only as drift guardrail)
* ``FileProvider``    – imports a package written by a human editor or an
  interactive session (this is how the example project was produced).

Prompts live in packages/prompts/*.md and are versioned by file name; the
versions used are stored in the project.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .paths import PROMPTS_DIR
from .project import Project

PROMPT_VERSIONS = {
    "arabic_cleanup": "arabic_cleanup_v1",
    "de_translation": "de_translation_v1",
    "semantic_segmentation": "semantic_segmentation_v1",
    "en_from_de": "en_from_de_v1",
    "religious_reference_detection": "religious_reference_detection_v1",
    "title_generation": "title_generation_v1",
    "integrity_check": "integrity_check_v1",
}

DEFAULT_MODEL = os.environ.get("ABU_AISHA_LLM_MODEL", "claude-opus-5-5")


def load_prompt(name: str) -> str:
    shared = (PROMPTS_DIR / "_shared_rules_v1.md").read_text()
    return (PROMPTS_DIR / f"{name}.md").read_text().replace("{{shared_rules}}", shared)


def transcript_payload(p: Project) -> dict:
    ws = p.data["transcript"]["word_timings"]
    return {
        "speaker_user_supplied": p.data["speaker"]["user_supplied_name"],
        "user_instructions": p.data["settings"].get("instructions"),
        "content_profile": p.data["settings"].get("content_profile"),
        "phrases": [
            {"phrase": ph["i"], "start": ph["start"], "end": ph["end"],
             "words": [{"i": i, "t": ws[i]["text"]} for i in ph["words"]]}
            for ph in p.data["transcript"]["arabic_verbatim_reviewed"]
        ],
    }


# ------------------------------------------------------------------ schemas

_STR = {"type": "string"}
_INT = {"type": "integer"}
_NUM = {"type": "number"}


def _obj(props: dict, required: list[str] | None = None) -> dict:
    return {"type": "object", "properties": props, "required": required or list(props), "additionalProperties": False}


PASS1_SCHEMA = _obj({
    "speaker": _obj({"arabic_display": _STR, "honorific": _STR, "latin_display": _STR, "intro_line": _STR}),
    "arabic_corrections": {"type": "array", "items": _obj({"word": _INT, "from": _STR, "to": _STR, "reason": _STR, "lexical_change": {"type": "boolean"}})},
    "transcript_flags": {"type": "array", "items": _obj({"kind": _STR, "word": _INT, "time": _NUM, "reason": _STR})},
    "segments": {"type": "array", "items": _obj({
        "words": {"type": "array", "items": _INT},
        "de": _STR, "notes": _STR, "deliberate_fast": {"type": "boolean"},
        "accent": {"type": "string", "enum": ["none", "red"]},
        "reference_ids": {"type": "array", "items": _STR},
    })},
    "titles": {"type": "array", "items": _obj({"category": _STR, "de": _STR, "grounding": _STR})},
    "references": {"type": "array", "items": _obj({
        "id": _STR, "type": _STR, "label": _STR, "arabic_span": _STR,
        "status": {"type": "string", "enum": ["CHECK_REQUIRED", "UNVERIFIED"]}, "evidence": _STR,
        "quran_candidate": _STR,
    })},
    "editorial_notes": {"type": "array", "items": _obj({
        "id": _STR, "kind": {"type": "string", "enum": ["source", "context", "quran_ref", "hadith_ref"]},
        "text_de": _STR, "text_ar": _STR, "start_word": _INT, "end_word": _INT, "provenance": _STR,
    })},
    "trim_suggestion": _obj({"applies": {"type": "boolean"}, "start_word": _INT, "end_word": _INT, "reason": _STR}),
})

PASS2_SCHEMA = _obj({
    "segments": {"type": "array", "items": _obj({"id": _STR, "en": _STR})},
    "titles": {"type": "array", "items": _obj({"de": _STR, "en": _STR})},
    "drift_warnings": {"type": "array", "items": _obj({"id": _STR, "detail": _STR})},
})

INTEGRITY_SCHEMA = _obj({"issues": {"type": "array", "items": _obj({"segment": _STR, "kind": _STR, "detail": _STR})}})


class LLMUnavailable(RuntimeError):
    pass


class ClaudeProvider:
    """Claude API provider (Anthropic Python SDK). Credentials are resolved by the SDK
    (ANTHROPIC_API_KEY, auth token or `ant auth login` profile)."""

    name = "claude-api"

    def __init__(self, model: str = DEFAULT_MODEL, effort: str = "high"):
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover
            raise LLMUnavailable("pip install anthropic") from e
        self.anthropic = anthropic
        self.client = anthropic.Anthropic()
        self.model = model
        self.effort = effort

    def _call(self, system: str, payload: dict, schema: dict) -> dict:
        a = self.anthropic
        try:
            with self.client.beta.messages.stream(
                model=self.model,
                max_tokens=64000,
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                system=system,
                output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": schema}},
                messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
            ) as stream:
                msg = stream.get_final_message()
        except a.AuthenticationError as e:
            raise LLMUnavailable("Anthropic credentials missing/invalid") from e
        except (a.RateLimitError, a.APIConnectionError, a.InternalServerError) as e:
            raise LLMUnavailable(f"LLM temporarily unavailable: {e}") from e
        if msg.stop_reason == "refusal":
            raise LLMUnavailable(f"request declined: {getattr(msg, 'stop_details', None)}")
        if msg.stop_reason == "max_tokens":
            raise LLMUnavailable("output truncated (max_tokens)")
        text = next(b.text for b in msg.content if b.type == "text")
        return json.loads(text)

    # ---------------------------------------------------------------- passes
    def editorial(self, p: Project) -> dict:
        system = "\n\n---\n\n".join(load_prompt(n) for n in (
            "arabic_cleanup_v1", "de_translation_v1", "semantic_segmentation_v1",
            "religious_reference_detection_v1", "title_generation_v1"))
        system += (
            "\n\n---\n\nYou are the editorial engine of the Abu Aisha al-Kumasi video workflow. Return ONE JSON object "
            "following the schema: Arabic corrections, the German master split into semantic subtitle blocks that cover "
            "every word exactly once and in order (each block `words` = [first, last] word index), references (status "
            "CHECK_REQUIRED unless the Shaykh names the source), editorial-context suggestions (never inside spoken text), "
            "and 3–5 German title suggestions. `accent` stays 'none' unless it is a numbered rebuttal heading."
        )
        r = self._call(system, transcript_payload(p), PASS1_SCHEMA)
        ws = p.data["transcript"]["word_timings"]
        segs = [{"words": s["words"][:2] if len(s["words"]) >= 2 else [s["words"][0]] * 2, "de": s["de"],
                 "notes": s.get("notes") or None, "deliberate_fast": s.get("deliberate_fast", False),
                 "accent": None if s.get("accent") in (None, "none") else s["accent"],
                 "reference_ids": s.get("reference_ids", [])} for s in r["segments"]]
        check_coverage(segs, len(ws))
        # pass 2 — English from the final German (German is the editorial master)
        en = self.english(p, segs, [t["de"] for t in r["titles"]])
        for s, e in zip(segs, en["segments"]):
            s["en"] = e["en"]
        titles = [dict(t, en=next((x["en"] for x in en["titles"] if x["de"] == t["de"]), None)) for t in r["titles"]]
        notes = []
        for n in r["editorial_notes"]:
            notes.append({
                "id": n["id"], "kind": n["kind"],
                "text": ({"all": n["text_ar"]} if n["kind"] == "source" and n["text_ar"] else {"de": n["text_de"]}),
                "dir": "rtl" if n["kind"] == "source" and n["text_ar"] else "ltr",
                "start": ws[n["start_word"]]["start"], "end": ws[n["end_word"]]["end"] + 2.0,
                "status": "CHECK_REQUIRED", "enabled": False, "provenance": n["provenance"],
            })
        ts = r["trim_suggestion"]
        return {
            "provider": f"{self.name}:{self.model}",
            "prompt_versions": PROMPT_VERSIONS,
            "speaker": r["speaker"],
            "arabic_corrections": r["arabic_corrections"],
            "transcript_flags": r["transcript_flags"],
            "segments": segs,
            "titles": {"suggestions": titles, "chosen": {"de": titles[0]["de"], "en": titles[0]["en"]} if titles else {}},
            "references": [dict(x, segments=[]) for x in r["references"]],
            "editorial_notes": notes,
            "trim_suggestion": ({"trim_in": max(0.0, ws[ts["start_word"]]["start"] - 0.6),
                                 "trim_out": ws[ts["end_word"]]["end"] + 0.3, "reason": ts["reason"]} if ts["applies"] else None),
            "notes": [f"EN drift warning {w['id']}: {w['detail']}" for w in en.get("drift_warnings", [])],
        }

    def english(self, p: Project, segs: list[dict], titles_de: list[str]) -> dict:
        ws = p.data["transcript"]["word_timings"]
        payload = {
            "segments": [{"id": f"seg_{i:03d}", "de_final": s["de"],
                          "arabic_guardrail": " ".join(ws[k]["text"] for k in range(s["words"][0], s["words"][1] + 1))}
                         for i, s in enumerate(segs, 1)],
            "titles_de": titles_de,
        }
        return self._call(load_prompt("en_from_de_v1"), payload, PASS2_SCHEMA)

    def regenerate_en(self, p: Project, seg_ids: list[str]) -> dict[str, str]:
        """Only the given (stale) blocks — used after a German edit (§13.5)."""
        segs = [p.segment(i) for i in seg_ids]
        payload = {"segments": [{"id": s["id"], "de_final": s["de"], "arabic_guardrail": s["ar"]} for s in segs], "titles_de": []}
        out = self._call(load_prompt("en_from_de_v1"), payload, PASS2_SCHEMA)
        return {x["id"]: x["en"] for x in out["segments"]}

    def integrity(self, p: Project) -> list[dict]:
        payload = {"segments": [{"id": s["id"], "ar": s["ar"], "de": s["de"], "en": s.get("en")} for s in p.data["timeline"]]}
        return self._call(load_prompt("integrity_check_v1"), payload, INTEGRITY_SCHEMA)["issues"]


class FileProvider:
    name = "file"

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def editorial(self, p: Project) -> dict:
        ed = json.loads(self.path.read_text())
        check_coverage(ed["segments"], len(p.data["transcript"]["word_timings"]))
        return ed


def check_coverage(segs: list[dict], n_words: int) -> None:
    """Blocks must cover every spoken word exactly once, in order (nothing added, nothing dropped)."""
    expected = 0
    for s in segs:
        a, b = s["words"]
        if a != expected or b < a:
            raise ValueError(f"segment word range {a}-{b} breaks coverage (expected start {expected})")
        expected = b + 1
    if expected != n_words:
        raise ValueError(f"segments cover {expected} of {n_words} words")


def get_provider(spec: str | None):
    if spec and spec.startswith("file:"):
        return FileProvider(spec[5:])
    return ClaudeProvider(model=spec or DEFAULT_MODEL)
