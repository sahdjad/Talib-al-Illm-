"""Project package: the single source of truth (spec §7, §26, §30.7).

A project lives in data/projects/<name>/ with project.json plus derived files.
Every UI/CLI change goes through this module; renderers only read.
"""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import shutil
import uuid
from pathlib import Path

from .paths import PROJECTS_DIR, SCHEMA_DIR

SCHEMA_VERSION = 1

STATES = [
    "UPLOADED", "ANALYZING", "TRANSCRIBING", "TRANSLATING_DE", "SEGMENTING", "TRANSLATING_EN", "VERIFYING",
    "COMPOSING", "PREVIEW_READY", "REVIEW_REQUIRED", "RENDERING", "READY", "APPROVED",
]


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load_defaults() -> dict:
    return json.loads((SCHEMA_DIR / "defaults.json").read_text())


def text_hash(s: str | None) -> str:
    return hashlib.sha1((s or "").strip().encode()).hexdigest()[:10]


class Project:
    def __init__(self, root: Path, data: dict):
        self.root = Path(root)
        self.data = data

    # ------------------------------------------------------------ lifecycle
    @classmethod
    def create(cls, name: str, media_file: str | Path, speaker_name: str, *, projects_dir: Path | None = None,
               copy_media: bool = True, **settings) -> "Project":
        root = (projects_dir or PROJECTS_DIR) / name
        if (root / "project.json").exists():
            raise FileExistsError(f"project {name} already exists")
        (root / "source").mkdir(parents=True, exist_ok=True)
        media_file = Path(media_file)
        dst = root / "source" / ("source" + media_file.suffix.lower())
        if copy_media:
            shutil.copy2(media_file, dst)
        else:
            dst.symlink_to(media_file.resolve())
        cfg = load_defaults()
        data = {
            "schema_version": SCHEMA_VERSION,
            "project_id": str(uuid.uuid4()),
            "name": name,
            "created_at": now(),
            "updated_at": now(),
            "state": "UPLOADED",
            "state_history": [{"state": "UPLOADED", "at": now()}],
            "config": cfg,
            "speaker": {
                "user_supplied_name": speaker_name,
                "arabic_display": None,
                "honorific": None,
                "latin_display": None,
                "identity_source": "user",
            },
            "source": {
                "file": str(dst.relative_to(root)),
                "original_filename": media_file.name,
                "source_url": settings.pop("source_url", None),
                "original_account": settings.pop("original_account", None),
                "rights_note": settings.pop("rights_note", None),
                "trim_in": float(settings.pop("trim_in", 0.0) or 0.0),
                "trim_out": settings.pop("trim_out", None),
                "probe": None,
            },
            "settings": {
                "mode": settings.pop("mode", "auto"),
                "theme": "classic",
                "intro": settings.pop("intro", cfg["intro"]["enabled"]),
                "intro_duration": cfg["intro"]["duration_seconds"],
                "content_profile": settings.pop("content_profile", "general"),
                "mask": {"mode": "auto", "fade_start": None, "fade_end": None},
                "languages": cfg["project"]["languages"],
                "editorial_context": settings.pop("editorial_context", "suggest"),
                "background_image": settings.pop("background_image", None),
                "instructions": settings.pop("instructions", None),
                "review_required": True,
                "audio_policy": "original_only",
            },
            "transcript": {
                "arabic_verbatim_raw": [],
                "arabic_verbatim_reviewed": [],
                "word_timings": [],
                "confidence_flags": [],
                "audit": [],
                "asr": None,
                "imported_text": None,
            },
            "translations": {"de_draft": {}, "de_final": [], "en_final": [], "provenance": {}},
            "timeline": [],
            "references": [],
            "editorial_notes": [],
            "titles": {"suggestions": [], "chosen": {"de": None, "en": None}},
            "visual": {},
            "qa": {},
            "prompts": {},
            "render_history": [],
            "decisions": [],
        }
        p = cls(root, data)
        p.save()
        return p

    @classmethod
    def open(cls, name_or_path: str | Path) -> "Project":
        p = Path(name_or_path)
        if not (p / "project.json").exists():
            p = PROJECTS_DIR / str(name_or_path)
        data = json.loads((p / "project.json").read_text())
        return cls(p, data)

    def save(self) -> None:
        self.data["updated_at"] = now()
        self._derive_views()
        tmp = self.root / "project.json.tmp"
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2))
        tmp.replace(self.root / "project.json")

    def clone(self, new_name: str, **source_overrides) -> "Project":
        root = self.root.parent / new_name
        if root.exists():
            raise FileExistsError(new_name)
        (root / "source").mkdir(parents=True)
        src = self.root / self.data["source"]["file"]
        (root / self.data["source"]["file"]).symlink_to(src.resolve())
        data = copy.deepcopy(self.data)
        data.update(project_id=str(uuid.uuid4()), name=new_name, created_at=now(), render_history=[], qa={})
        data["source"].update(source_overrides)
        data["visual"].pop("prepared", None)
        data["decisions"].append({"at": now(), "what": f"cloned from {self.data['name']}", "overrides": source_overrides})
        p = Project(root, data)
        p.set_state("COMPOSING", note=f"clone of {self.data['name']}")
        p.save()
        return p

    # --------------------------------------------------------------- helpers
    @property
    def cfg(self) -> dict:
        return self.data["config"]

    def path(self, *parts: str) -> Path:
        q = self.root.joinpath(*parts)
        q.parent.mkdir(parents=True, exist_ok=True)
        return q

    @property
    def source_path(self) -> Path:
        return self.root / self.data["source"]["file"]

    @property
    def trim(self) -> tuple[float, float]:
        s = self.data["source"]
        dur = (s.get("probe") or {}).get("duration")
        out = s.get("trim_out") or dur
        return float(s.get("trim_in") or 0.0), float(out)

    def set_state(self, state: str, note: str | None = None) -> None:
        assert state in STATES or state.endswith("_FAILED"), state
        self.data["state"] = state
        self.data["state_history"].append({"state": state, "at": now(), **({"note": note} if note else {})})

    def fail(self, stage: str, err: str) -> None:
        """Failures keep the last successful state (spec §30.7) and record the error."""
        self.data.setdefault("errors", []).append({"stage": stage, "at": now(), "error": err[-4000:]})

    def segment(self, seg_id: str) -> dict:
        for s in self.data["timeline"]:
            if s["id"] == seg_id:
                return s
        raise KeyError(seg_id)

    def en_status(self, seg: dict) -> str:
        if not seg.get("en"):
            return "MISSING_EN"
        if seg.get("en_from_de_hash") != text_hash(seg.get("de")):
            return "STALE_EN"
        return "OK"

    def _derive_views(self) -> None:
        """translations.de_final / en_final are read-only views of the timeline."""
        tl = self.data.get("timeline", [])
        self.data["translations"]["de_final"] = [{"id": s["id"], "text": s.get("de")} for s in tl if s["type"] != "pause"]
        self.data["translations"]["en_final"] = [
            {"id": s["id"], "text": s.get("en"), "status": self.en_status(s)} for s in tl if s["type"] != "pause"
        ]
