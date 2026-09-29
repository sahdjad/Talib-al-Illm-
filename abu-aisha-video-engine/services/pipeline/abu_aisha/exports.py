"""Text package, captions and review reports (spec §26)."""
from __future__ import annotations

import json

from . import render_input
from .project import Project


def tc(t: float, srt: bool = False) -> str:
    t = max(0.0, t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    if srt:
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)) % 1000:03d}"
    return f"{int(m):02d}:{s:05.2f}"


def _video_time(p: Project, t: float) -> float:
    """Source time → time in the rendered video (trim + intro offset)."""
    t_in, _ = p.trim
    intro = p.data["settings"]["intro_duration"] if p.data["settings"]["intro"] else 0
    return t - t_in + intro


def _segments_in_range(p: Project):
    t_in, t_out = p.trim
    for s in p.data["timeline"]:
        if s["type"] == "pause" or s["end"] <= t_in or s["start"] >= t_out:
            continue
        yield s


def srt(p: Project, lang: str) -> str:
    _, t_out = p.trim
    out = []
    for i, s in enumerate(_segments_in_range(p), 1):
        a = _video_time(p, max(s["start"], p.trim[0]))
        b = _video_time(p, min(s["end"], t_out))
        out.append(f"{i}\n{tc(a, True)} --> {tc(b, True)}\n{s[lang]}\n")
    return "\n".join(out)


def export_all(p: Project) -> list[str]:
    written = []

    def w(rel: str, text: str) -> None:
        p.path(rel).write_text(text, encoding="utf-8")
        written.append(rel)

    tr = p.data["transcript"]
    sp = p.data["speaker"]
    t_in, t_out = p.trim
    head = f"{sp.get('arabic_display') or sp['user_supplied_name']}\nQuelle: {p.data['source'].get('original_account') or p.data['source']['original_filename']}\n"
    lines = [head, "# Arabisch (geprüft) – Zeiten = Quellvideo\n"]
    for ph in tr["arabic_verbatim_reviewed"]:
        lines.append(f"[{tc(ph['start'])}–{tc(ph['end'])}] {ph['text']}")
    lines += ["", "# Arabisch (ASR roh, unverändert)", ""]
    for ph in tr["arabic_verbatim_raw"]:
        lines.append(f"[{tc(ph['start'])}–{tc(ph['end'])}] {ph['text']}")
    if tr["audit"]:
        lines += ["", "# Korrekturprotokoll"]
        for a in tr["audit"]:
            lines.append(f"- Wort {a['word']}: {a['from']} → {a['to']} ({a['reason']})")
    w("text/transcript_ar.txt", "\n".join(lines) + "\n")

    for lang, label in (("de", "Deutsch (Master)"), ("en", "Englisch (aus finalem Deutsch)")):
        title = (p.data["titles"]["chosen"] or {}).get(lang) or ""
        body = [f"{label}\nTitel: {title}\n"]
        for s in p.data["timeline"]:
            body.append(f"[{s['id']} · {tc(s['start'])}–{tc(s['end'])}]\n{s.get(lang) or ''}\n")
        body.append("— Fließtext —\n" + " ".join((s.get(lang) or "").replace("\n", " ") for s in p.data["timeline"]))
        w(f"text/translation_{lang}.txt", "\n".join(body) + "\n")
        w(f"captions/{lang}.srt", srt(p, lang))

    seg_export = []
    for s in p.data["timeline"]:
        seg_export.append({
            "id": s["id"], "source_word_start": s["source_word_start"], "source_word_end": s["source_word_end"],
            "start": s["start"], "end": s["end"], "video_start": round(_video_time(p, s["start"]), 3),
            "video_end": round(_video_time(p, s["end"]), 3), "type": s["type"], "ar": s["ar"], "de": s["de"],
            "en": s.get("en"), "en_status": p.en_status(s), "emphasis": s.get("emphasis", []),
            "reference_ids": s.get("reference_ids", []),
            "layout": {k: {"fontSize": v["fontSize"], "lines": v["lines"]} for k, v in (s.get("layout") or {}).items()},
        })
    w("text/segments.json", json.dumps({"trim": [t_in, t_out], "intro": p.data["settings"]["intro"],
                                        "intro_duration": p.data["settings"]["intro_duration"], "segments": seg_export},
                                       ensure_ascii=False, indent=1))

    refs = ["# Quellen & religiöse Inhalte\n"]
    if not p.data["references"]:
        refs.append("Keine Referenzen erkannt.")
    for r in p.data["references"]:
        refs.append(f"- **{r['id']}** · {r['type']} · `{r['status']}`\n  {r.get('label')}\n  Beleg: {r.get('evidence', '–')}")
    refs.append("\n## Redaktionelle Ergänzungen (nicht gesprochen)\n")
    for n in p.data["editorial_notes"]:
        txt = n["text"].get("all") or " / ".join(f"{k}: {v}" for k, v in n["text"].items())
        shown = n.get("enabled") and n["status"] in ("VERIFIED_EXACT", "VERIFIED_GENERAL", "APPROVED")
        refs.append(f"- **{n['id']}** ({n['kind']}, `{n['status']}`, {'eingeblendet' if shown else 'nur Vorschlag'}) "
                    f"{tc(n['start'])}–{tc(n['end'])}: {txt}\n  {n.get('provenance', '')}")
    w("text/references.md", "\n".join(refs) + "\n")
    w("text/qa_report.md", qa_report(p))
    return written


def qa_report(p: Project) -> str:
    qa = p.data.get("qa") or {}
    sp = p.data["speaker"]
    t_in, t_out = p.trim
    mask = render_input.effective_mask(p)
    lines = [
        f"# QA-Bericht – {p.data['name']}",
        "",
        f"- Sprecher: {sp.get('arabic_display') or sp['user_supplied_name']} ({sp.get('latin_display') or '–'}) – Quelle der Identität: Nutzer",
        f"- Quelle: {p.data['source'].get('original_account') or '–'}",
        f"- Verwendeter Bereich: {t_in:.2f}–{t_out:.2f} s ({t_out - t_in:.2f} s) · Intro: {'ja, ' + str(p.data['settings']['intro_duration']) + ' s' if p.data['settings']['intro'] else 'nein'}",
        f"- Modus: {p.data['visual'].get('mode')} · Maske: {mask['fade_start']:.3f}–{mask['fade_end']:.3f} ({'manuell' if p.data['settings']['mask'].get('mode') == 'manual' else 'automatisch'})",
        f"- Titel: DE „{(p.data['titles']['chosen'] or {}).get('de')}“ · EN “{(p.data['titles']['chosen'] or {}).get('en')}”",
        f"- ASR: {(p.data['transcript'].get('asr') or {}).get('provider')} / {(p.data['transcript'].get('asr') or {}).get('model')}",
        f"- Redaktion: {(p.data['translations'].get('provenance') or {}).get('provider')} · Prompts: {', '.join((p.data.get('prompts') or {}).values())}",
        f"- Status: **{qa.get('status', 'nicht geprüft')}**",
        "",
        "## Qualitäts-Gates (§28)",
        "",
        "| # | Gate | OK | Detail |",
        "|---|------|----|--------|",
    ]
    for g in qa.get("gates", []):
        lines.append(f"| {g['n']} | {g['gate']} | {'✅' if g['ok'] else '❌'} | {g['detail']} |")
    lines += ["", "## Zu prüfen", ""]
    for it in qa.get("review_items", []):
        t = f" @ {tc(it['time'])}" if it.get("time") is not None else ""
        txt = f" „{it['text']}“" if it.get("text") else ""
        lines.append(f"- **{it['kind']}**{t}{txt}: {it['detail']}")
    lines += ["", "## Freigabe-Checkliste", ""] + [f"- [ ] {c}" for c in qa.get("checklist", [])]
    lines += ["", "Erst nach dieser Prüfung: APPROVED. Keine automatische Veröffentlichung (v1).", ""]
    return "\n".join(lines)
