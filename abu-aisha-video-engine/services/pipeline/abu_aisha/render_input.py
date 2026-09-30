"""project.json → RenderInput for the Remotion renderer (apps/renderer/src/types.ts)."""
from __future__ import annotations

from . import layout
from .project import Project


def speaker_line(p: Project) -> str:
    sp = p.data["speaker"]
    return sp.get("intro_line") or f"🎙️ {sp.get('arabic_display') or sp['user_supplied_name']}"


def build(p: Project, lang: str, *, debug: bool = False) -> dict:
    cfg = p.cfg
    vis = p.data["visual"]
    W, H, fps = cfg["video"]["width"], cfg["video"]["height"], cfg["video"]["fps"]
    t_in, t_out = p.trim
    mask = effective_mask(p)
    boxes = layout.canvas_boxes(cfg, mask)
    st = p.data["settings"]
    mode = vis["mode"]
    prepared = vis.get("prepared", {})

    segments = []
    for s in p.data["timeline"]:
        if s["type"] == "pause" or not s.get(lang):
            continue
        if s["end"] <= t_in or s["start"] >= t_out:
            continue
        lay = (s.get("layout") or {}).get(lang)
        if not lay:
            raise RuntimeError(f"segment {s['id']} has no {lang} layout — run the layout stage")
        segments.append({
            "id": s["id"],
            "start": round(max(0.0, s["start"] - t_in), 3),
            "end": round(min(t_out, s["end"]) - t_in, 3),
            "type": s.get("render_type", "spoken"),
            "text": s[lang],
            "accent": s.get("accent"),
            "layout": {"fontSize": lay["fontSize"], "lines": lay["lines"], "lineHeight": lay["lineHeight"]},
        })

    editorial = []
    for n in p.data["editorial_notes"]:
        if not n.get("enabled") or n.get("status") not in ("VERIFIED_EXACT", "VERIFIED_GENERAL", "APPROVED"):
            continue  # CHECK_REQUIRED never renders as if verified (§12.2, §24, QA gate 8)
        # text: {"de": ..., "en": ...} or language-independent {"all": ...} (e.g. an Arabic book line)
        text = n["text"].get(lang) or n["text"].get("all")
        if not text or n["end"] <= t_in or n["start"] >= t_out:
            continue
        editorial.append({
            "id": n["id"], "kind": n["kind"],
            "start": round(max(0.0, n["start"] - t_in), 3), "end": round(min(t_out, n["end"]) - t_in, 3),
            "text": text, "dir": n.get("dir", "ltr") if lang not in n["text"] else "ltr",
            "fontSize": n.get("font_size") or layout.editorial_font_size(cfg),
        })

    title = (p.data["titles"]["chosen"] or {}).get(lang) or ""
    tfit = p.data["titles"].get("layout", {}).get(lang) or layout.fit_title(title, boxes["subtitle"]["right"] - boxes["subtitle"]["left"], cfg)
    intro_on = bool(st["intro"])
    stage = vis["stage"]
    return {
        "projectId": p.data["project_id"],
        "lang": lang,
        "theme": "classic",
        "width": W, "height": H, "fps": fps,
        "mode": mode,
        "contentDuration": round(t_out - t_in, 3),
        "audio": prepared.get("audio", "audio.wav"),
        "stage": {
            "video": prepared.get("stage_video") if mode == "video" else None,
            "still": prepared.get("still") if mode == "audio_visual" else None,
            "y": stage["y"], "height": stage["height"],
            "flow": vis.get("flow") if mode == "audio_visual" else None,
        },
        "mask": {"fadeStart": mask["fade_start"], "fadeEnd": mask["fade_end"], "topFade": 0.05 if stage["y"] > 0 else 0.0},
        "intro": {
            "enabled": intro_on,
            "duration": float(st["intro_duration"]),
            "freezeFrame": prepared.get("freeze"),
            "speakerLine": speaker_line(p),
            "title": title,
            "titleFontSize": tfit["fontSize"],
            "titleLines": tfit["lines"],
            "intensity": cfg["content_profiles"].get(st.get("content_profile", "general"), 1.0),
        },
        "subtitleBox": boxes["subtitle"],
        "editorialLane": boxes["editorial"],
        "segments": segments,
        "editorial": editorial,
        "brand": {
            "lockup": "brand/" + cfg["brand"]["lockup"],
            "top": boxes["brand"]["top"], "height": boxes["brand"]["height"],
        },
        "style": {
            "subtitleFont": cfg["fonts"]["subtitle"], "arabicFont": cfg["fonts"]["arabic"],
            "fill": cfg["subtitles"]["fill"], "stroke": cfg["subtitles"]["outline"],
            "strokeWidth": cfg["subtitles"]["stroke_ratio"], "accent": cfg["subtitles"]["accent"],
            "editorialColor": cfg["subtitles"]["editorial_color"],
        },
        "debug": {"safeZones": debug},
    }


def effective_mask(p: Project) -> dict:
    """Manual override (review slider) wins over the automatic decision and persists (§36)."""
    m = p.data["settings"]["mask"]
    auto = p.data["visual"]["mask_auto"]
    fs = m.get("fade_start") if m.get("mode") == "manual" and m.get("fade_start") is not None else auto["fade_start"]
    fe = m.get("fade_end") if m.get("mode") == "manual" and m.get("fade_end") is not None else auto["fade_end"]
    return {"fade_start": fs, "fade_end": fe}
