"""FastAPI service for the review UI (spec §25, §30.2).

Run:  uvicorn abu_aisha.api:app --port 8765   (from services/pipeline)
Then open http://localhost:8765/ .

Long stages (ASR, LLM, rendering) run in a background thread per project; the
UI polls /jobs. The project file stays the single source of truth.
"""
from __future__ import annotations

import shutil
import tempfile
import threading
import traceback
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from . import exports, pipeline, qa, segmentation
from .paths import ENGINE_ROOT, PROJECTS_DIR
from .project import Project, now

app = FastAPI(title="Abu Aisha Video Engine")
JOBS: dict[str, dict] = {}
LOCKS: dict[str, threading.Lock] = {}
WEB_DIR = ENGINE_ROOT / "apps" / "web"


def _open(name: str) -> Project:
    if not (PROJECTS_DIR / name / "project.json").exists():
        raise HTTPException(404, f"project {name} not found")
    return Project.open(name)


def _job(name: str, label: str, fn) -> dict:
    lock = LOCKS.setdefault(name, threading.Lock())
    if not lock.acquire(blocking=False):
        raise HTTPException(409, f"a job is already running for {name}: {JOBS.get(name, {}).get('label')}")
    JOBS[name] = {"label": label, "status": "running", "started": now(), "error": None}

    def runner():
        try:
            fn()
            JOBS[name].update(status="done", finished=now())
        except Exception as e:  # noqa: BLE001
            JOBS[name].update(status="failed", error=f"{e!r}\n{traceback.format_exc()[-2000:]}", finished=now())
        finally:
            lock.release()

    threading.Thread(target=runner, daemon=True).start()
    return JOBS[name]


def _view(p: Project) -> dict:
    d = dict(p.data)
    d["stage_status"] = pipeline.stage_status(p)
    d["job"] = JOBS.get(p.data["name"])
    d["timeline"] = [dict(s, en_status=p.en_status(s)) for s in p.data["timeline"]]
    d["trim_effective"] = p.trim
    return d


# ------------------------------------------------------------------ pages

@app.get("/", response_class=HTMLResponse)
def index():
    return (WEB_DIR / "index.html").read_text()


@app.get("/favicon.ico")
def favicon():
    return FileResponse(WEB_DIR / "logo.png")


@app.get("/static/{path:path}")
def static(path: str):
    f = (WEB_DIR / path).resolve()
    if WEB_DIR.resolve() not in f.parents or not f.exists():
        raise HTTPException(404)
    return FileResponse(f)


# --------------------------------------------------------------- projects

@app.get("/api/projects")
def list_projects():
    out = []
    for d in sorted(PROJECTS_DIR.glob("*/project.json")):
        p = Project.open(d.parent)
        out.append({"name": p.data["name"], "state": p.data["state"], "speaker": p.data["speaker"]["user_supplied_name"],
                    "updated_at": p.data["updated_at"], "title": (p.data["titles"]["chosen"] or {}).get("de")})
    return out


@app.post("/api/projects")
async def create_project(media: UploadFile = File(...), name: str = Form(...), speaker: str = Form(...),
                         mode: str = Form("auto"), intro: bool = Form(True), profile: str = Form("general"),
                         title_de: str = Form(""), title_en: str = Form(""), instructions: str = Form(""),
                         source_url: str = Form(""), transcript_ar: str = Form("")):
    safe = "".join(c for c in name if c.isalnum() or c in "-_").strip("-_")
    if not safe:
        raise HTTPException(400, "invalid project name")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / (media.filename or "source.mp4")
        with tmp.open("wb") as f:
            shutil.copyfileobj(media.file, f)
        p = Project.create(safe, tmp, speaker, mode=mode, intro=intro, content_profile=profile,
                           instructions=instructions or None, source_url=source_url or None)
    if title_de or title_en:
        p.data["titles"]["chosen"] = {"de": title_de or None, "en": title_en or None}
        p.save()

    def work():
        q = Project.open(safe)
        pipeline.analyze(q)
        pipeline.transcribe(q)
        if transcript_ar.strip():
            pipeline.import_transcript(q, transcript_ar)

    _job(safe, "Analyse + Transkription", work)
    return {"name": safe}


@app.get("/api/projects/{name}")
def get_project(name: str):
    return _view(_open(name))


@app.get("/api/projects/{name}/job")
def get_job(name: str):
    return JOBS.get(name) or {"status": "idle"}


class RunReq(BaseModel):
    provider: str | None = None
    preview: bool = False
    final: bool = False
    lang: str | None = None


@app.post("/api/projects/{name}/run")
def run(name: str, req: RunReq):
    from .llm import get_provider

    _open(name)

    def work():
        prov = get_provider(req.provider) if (req.provider or not Project.open(name).data["timeline"]) else None
        pipeline.run_all(Project.open(name), provider=prov, langs=req.lang.split(",") if req.lang else None,
                         preview=req.preview, render_final=req.final)

    return _job(name, "Pipeline", work)


class TextReq(BaseModel):
    text: str


def _after(p: Project):
    pipeline.do_layout(p)
    return _view(p)


@app.post("/api/projects/{name}/segments/{seg}/de")
def set_de(name: str, seg: str, req: TextReq):
    p = _open(name)
    segmentation.set_de(p, seg, req.text)
    return _after(p)


@app.post("/api/projects/{name}/segments/{seg}/en")
def set_en(name: str, seg: str, req: TextReq):
    p = _open(name)
    segmentation.set_en(p, seg, req.text)
    return _after(p)


@app.post("/api/projects/{name}/segments/{seg}/confirm-en")
def confirm_en(name: str, seg: str):
    p = _open(name)
    segmentation.confirm_en(p, seg)
    return _after(p)


@app.post("/api/projects/{name}/regen-en")
def regen_en(name: str, provider: str | None = None):
    from .llm import get_provider

    def work():
        p = Project.open(name)
        stale = [s["id"] for s in p.data["timeline"] if p.en_status(s) != "OK"]
        if stale:
            for sid, en in get_provider(provider).regenerate_en(p, stale).items():
                segmentation.set_en(p, sid, en)
            pipeline.do_layout(p)

    return _job(name, "EN aus DE neu erzeugen", work)


class SplitReq(BaseModel):
    at_word: int
    de: list[str]
    en: list[str] | None = None


@app.post("/api/projects/{name}/segments/{seg}/split")
def split(name: str, seg: str, req: SplitReq):
    p = _open(name)
    segmentation.split(p, seg, req.at_word, tuple(req.de), tuple(req.en) if req.en else None)
    return _after(p)


class MergeReq(BaseModel):
    first: str
    second: str


@app.post("/api/projects/{name}/merge")
def merge(name: str, req: MergeReq):
    p = _open(name)
    segmentation.merge(p, req.first, req.second)
    return _after(p)


class BoundaryReq(BaseModel):
    to_word: int


@app.post("/api/projects/{name}/segments/{seg}/boundary")
def boundary(name: str, seg: str, req: BoundaryReq):
    p = _open(name)
    segmentation.move_boundary(p, seg, req.to_word)
    return _after(p)


class MaskReq(BaseModel):
    auto: bool = False
    start: float | None = None
    end: float | None = None


@app.post("/api/projects/{name}/mask")
def mask(name: str, req: MaskReq):
    p = _open(name)
    m = p.data["settings"]["mask"]
    if req.auto:
        m.update(mode="auto", fade_start=None, fade_end=None)
    else:
        m.update(mode="manual", fade_start=req.start, fade_end=req.end if req.end is not None else (req.start or 0.45) + 0.16)
    p.data["decisions"].append({"at": now(), "what": "mask", "value": dict(m)})
    return _after(p)


class SettingsReq(BaseModel):
    intro: bool | None = None
    title_de: str | None = None
    title_en: str | None = None
    content_profile: str | None = None


@app.post("/api/projects/{name}/settings")
def settings(name: str, req: SettingsReq):
    p = _open(name)
    if req.intro is not None:
        p.data["settings"]["intro"] = req.intro
    if req.content_profile:
        p.data["settings"]["content_profile"] = req.content_profile
    ch = p.data["titles"]["chosen"] or {}
    if req.title_de is not None:
        ch["de"] = req.title_de
    if req.title_en is not None:
        ch["en"] = req.title_en
    p.data["titles"]["chosen"] = ch
    return _after(p)


class NoteReq(BaseModel):
    enabled: bool | None = None
    approve: bool = False


@app.post("/api/projects/{name}/notes/{note_id}")
def note(name: str, note_id: str, req: NoteReq):
    p = _open(name)
    n = next((x for x in p.data["editorial_notes"] if x["id"] == note_id), None)
    if not n:
        raise HTTPException(404)
    if req.enabled is not None:
        n["enabled"] = req.enabled
    if req.approve:
        n["status"] = "APPROVED"
    p.save()
    return _view(p)


class RenderReq(BaseModel):
    lang: str = "de"
    preview: bool = True
    stills: list[int] | None = None


@app.post("/api/projects/{name}/render")
def render(name: str, req: RenderReq):
    def work():
        p = Project.open(name)
        pipeline.do_layout(p)
        if req.stills:
            pipeline.render(p, req.lang, stills=req.stills)
        else:
            pipeline.render(p, req.lang, preview=req.preview)
        qa.run(p)
        exports.export_all(p)

    return _job(name, f"Render {req.lang} {'Vorschau' if req.preview else 'final'}", work)


@app.post("/api/projects/{name}/qa")
def run_qa(name: str):
    p = _open(name)
    pipeline.prepare_assets(p)
    r = qa.run(p)
    exports.export_all(p)
    return r


@app.post("/api/projects/{name}/approve")
def approve(name: str):
    p = _open(name)
    r = qa.run(p)
    if not r["all_gates_ok"]:
        raise HTTPException(409, "QA gates not green")
    p.set_state("APPROVED", note="approved in review UI")
    p.save()
    return _view(p)


@app.get("/api/projects/{name}/files/{path:path}")
def files(name: str, path: str):
    root = (PROJECTS_DIR / name).resolve()
    f = (root / path).resolve()
    if root not in f.parents or not f.is_file():
        raise HTTPException(404)
    return FileResponse(f)
