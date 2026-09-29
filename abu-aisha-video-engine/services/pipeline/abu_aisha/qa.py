"""Quality gates (spec §28) and the actionable review list (spec §25 Screen 4)."""
from __future__ import annotations

from pathlib import Path

from . import layout, media, render_input, segmentation
from .project import Project, now

CHECKLIST = [
    "Speaker korrekt?",
    "Arabisches Transkript an markierten Stellen korrekt?",
    "Deutsche Bedeutung freigegeben?",
    "Englisch spiegelt das Deutsche?",
    "Quellen freigegeben?",
    "Redaktionelle Ergänzungen klar getrennt?",
    "Visuelles Layout akzeptabel?",
]


def run(p: Project) -> dict:
    p.set_state("VERIFYING")
    cfg = p.cfg
    gates: list[dict] = []

    def gate(n: int, name: str, ok: bool, detail: str = "") -> None:
        gates.append({"n": n, "gate": name, "ok": bool(ok), "detail": detail})

    t_in, t_out = p.trim
    tl = [s for s in p.data["timeline"] if s["type"] != "pause"]
    pub = p.root / "render_public" / "audio.wav"
    if pub.exists():
        a = media.probe(pub)
        gate(1, "Audio vorhanden, Dauer = Quellbereich", a["has_audio"] and abs(a["duration"] - (t_out - t_in)) < 0.08,
             f"{a['duration']:.3f}s vs {t_out - t_in:.3f}s")
    else:
        gate(1, "Audio vorhanden, Dauer = Quellbereich", False, "render_public/audio.wav fehlt (prepare_assets)")
    gate(2, "Arabisches Transkript vorhanden", bool(p.data["transcript"]["word_timings"]))
    missing_de = [s["id"] for s in tl if not (s.get("de") or "").strip()]
    gate(3, "Jeder Block hat DE", not missing_de, ", ".join(missing_de))
    en_bad = [f"{s['id']}:{p.en_status(s)}" for s in tl if "en" in p.data["settings"]["languages"] and p.en_status(s) != "OK"]
    gate(4, "Jeder Block hat aktuelles EN", not en_bad, ", ".join(en_bad))

    mask = render_input.effective_mask(p)
    boxes = layout.canvas_boxes(cfg, mask)
    sb = boxes["subtitle"]
    over = []
    for s in tl:
        for lang, lay in (s.get("layout") or {}).items():
            if lay["status"] != "OK" or lay["width"] > sb["right"] - sb["left"] or lay["height"] > sb["bottom"] - sb["top"]:
                over.append(f"{s['id']}/{lang}")
    missing_layout = [s["id"] for s in tl if not s.get("layout")]
    gate(5, "Kein Untertitel verlässt den sicheren Bereich", not over and not missing_layout,
         ", ".join(over + [f"{m}: kein Layout" for m in missing_layout]))
    ed = boxes["editorial"]
    br = boxes["brand"]
    gate(6, "Branding kollidiert nicht mit Untertiteln", sb["bottom"] <= ed["top"] and ed["bottom"] <= br["top"]
         and br["bottom"] <= cfg["video"]["height"] - cfg["safe_zones"]["bottom"],
         f"Untertitel ≤{sb['bottom']} · Quellenzeile {ed['top']}–{ed['bottom']} · Branding {br['top']}–{br['bottom']}")

    finals = [r for r in p.data["render_history"] if r.get("status") in ("OK", "CHECK")]
    latest = {}
    for r in finals:
        latest[(r["lang"], r["preview"])] = r
    intro_ok = all(r["verify"]["duration_ok"] for r in latest.values()) if latest else None
    gate(7, "Intro-Länge exakt wie konfiguriert", intro_ok is not False,
         "noch kein Render" if intro_ok is None else f"{p.data['settings']['intro_duration']}s")

    bad_refs = [n["id"] for n in p.data["editorial_notes"] if n.get("enabled")
                and n.get("status") not in ("VERIFIED_EXACT", "VERIFIED_GENERAL", "APPROVED")]
    gate(8, "Kein CHECK_REQUIRED als verifiziert gerendert", True,
         ("unverifiziert & aktiviert (werden NICHT gerendert): " + ", ".join(bad_refs)) if bad_refs else "")

    min_sub = min((lay["fontSize"] for s in tl for lay in (s.get("layout") or {}).values()), default=cfg["subtitles"]["font_max"])
    ed_size = max([n.get("font_size") or layout.editorial_font_size(cfg) for n in p.data["editorial_notes"]] or [0])
    gate(9, "Redaktioneller Kontext visuell getrennt", ed_size == 0 or (ed_size <= 0.72 * min_sub and
         cfg["subtitles"]["editorial_color"].lower() != cfg["subtitles"]["fill"].lower()),
         f"Quellenzeile {ed_size}px vs. kleinster Untertitel {min_sub}px, eigene Farbe & Spur")

    unsynced = [s["id"] for s in tl if bool(s.get("de")) != bool(s.get("en"))]
    gate(10, "DE/EN-Timeline synchron", not unsynced, ", ".join(unsynced) or "gemeinsame Timing-Map")

    flashes = []
    for a, b in zip(tl, tl[1:]):
        gap = b["start"] - a["end"]
        if 0 < gap < 0.25:
            flashes.append(f"{a['id']}→{b['id']} ({gap:.2f}s)")
        if gap < -0.001:
            flashes.append(f"{a['id']}↔{b['id']} überlappen")
    gate(11, "Keine Blitz-Lücken zwischen Blöcken", not flashes, ", ".join(flashes))

    finals_only = [r for (lang, prev), r in latest.items() if not prev]
    render_ok = all(r["verify"]["ok"] for r in finals_only) if finals_only else None
    gate(12, "Render öffnet und enthält Audio", render_ok is not False,
         "noch kein finaler Render" if render_ok is None else ", ".join(f"{r['lang']}: {r['verify']['duration']:.2f}s" for r in finals_only))

    # --------------------------------------------------------- review items
    items = []
    ws = p.data["transcript"]["word_timings"]
    for f in p.data["transcript"]["confidence_flags"]:
        w = ws[f["word"]] if f.get("word") is not None and f["word"] < len(ws) else None
        items.append({"kind": "UNSICHERES_ARABISCH", "time": f.get("time"), "text": w["text"] if w else None, "detail": f["reason"]})
    for a in p.data["transcript"]["audit"]:
        items.append({"kind": "TRANSKRIPT_KORREKTUR", "time": ws[a["word"]]["start"], "text": f"{a['from']} → {a['to']}", "detail": a["reason"]})
    for r in p.data["references"]:
        if r.get("status") not in ("VERIFIED_EXACT", "VERIFIED_GENERAL", "APPROVED"):
            items.append({"kind": "QUELLE_PRÜFEN", "detail": r.get("label"), "status": r.get("status")})
    for n in p.data["editorial_notes"]:
        items.append({"kind": "REDAKTIONELLE_ERGÄNZUNG", "time": n["start"], "text": n["text"].get("all") or n["text"].get("de"),
                      "detail": f"{n['kind']} · {n['status']} · {'eingeblendet' if n.get('enabled') and n['status'] in ('VERIFIED_EXACT','VERIFIED_GENERAL','APPROVED') else 'nur Vorschlag'}"})
    for w in segmentation.readability(p):
        items.append({"kind": "LESEGESCHWINDIGKEIT" if w["kind"] == "READING_SPEED" else "KURZER_BLOCK", "detail": w["message"]})
    for s in tl:
        if s.get("notes"):
            items.append({"kind": "NOTIZ", "time": s["start"], "text": s["id"], "detail": s["notes"]})
    ts = p.data["source"].get("trim_suggestion")
    if ts:
        items.append({"kind": "TRIM_VORSCHLAG", "detail": f"{ts['trim_in']}–{ts['trim_out']} s: {ts['reason']}"})
    dur = t_out - t_in
    if p.data["settings"]["intro"] and dur < cfg["intro"]["suggest_disable_below_seconds"]:
        items.append({"kind": "INTRO_VORSCHLAG", "detail": f"Clip nur {dur:.0f}s – ggf. ohne Intro?"})

    ok = all(g["ok"] for g in gates)
    qa = {"at": now(), "gates": gates, "all_gates_ok": ok, "review_items": items, "checklist": CHECKLIST,
          "status": "READY_FOR_REVIEW" if ok else "BLOCKED"}
    p.data["qa"] = qa
    p.set_state("REVIEW_REQUIRED" if ok else "VERIFYING")
    p.save()
    return qa
