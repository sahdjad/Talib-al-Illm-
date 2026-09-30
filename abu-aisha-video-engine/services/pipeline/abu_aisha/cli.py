"""Command line: `python -m abu_aisha <command> …` (see services/pipeline/README.md)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import exports, pipeline, qa, segmentation
from .project import Project, now


def _p(name: str) -> Project:
    return Project.open(name)


def cmd_new(a):
    settings = dict(mode=a.mode, intro=not a.no_intro, content_profile=a.profile, trim_in=a.trim_in, trim_out=a.trim_out,
                    source_url=a.source_url, original_account=a.source_account, background_image=a.background,
                    instructions=a.instructions)
    p = Project.create(a.name, a.media, a.speaker, **settings)
    if a.title_de or a.title_en:
        p.data["titles"]["chosen"] = {"de": a.title_de, "en": a.title_en}
        p.data["titles"]["user_supplied"] = True
        p.save()
    print(f"created {p.root}")


def cmd_run(a):
    from .llm import get_provider

    p = _p(a.name)
    prov = get_provider(a.provider) if a.provider else None
    pipeline.run_all(p, provider=prov, langs=a.lang.split(",") if a.lang else None, preview=a.preview,
                     render_final=not a.no_render)
    print(json.dumps(pipeline.stage_status(p), indent=1))


def cmd_analyze(a):
    p = _p(a.name)
    pipeline.analyze(p)
    v = p.data["visual"]
    print(json.dumps({k: v.get(k) for k in ("mode", "mode_suggested", "stage", "mask_auto", "freeze_time")}, ensure_ascii=False, indent=1))


def cmd_transcribe(a):
    p = _p(a.name)
    pipeline.transcribe(p, asr_json=a.asr_json)
    for ph in p.data["transcript"]["arabic_verbatim_raw"]:
        print(f"{ph['start']:7.2f}–{ph['end']:7.2f}  {ph['text']}")


def cmd_import_transcript(a):
    p = _p(a.name)
    pipeline.import_transcript(p, Path(a.file).read_text())
    print(f"aligned {len(p.data['transcript']['word_timings'])} words")


def cmd_editorial(a):
    from .llm import get_provider

    p = _p(a.name)
    ed = get_provider(a.provider).editorial(p)
    out = p.path("editorial", f"editorial_{now().replace(':', '')}.json")
    out.write_text(json.dumps(ed, ensure_ascii=False, indent=2))
    pipeline.apply_editorial(p, ed)
    pipeline.verify_references(p)
    pipeline.do_layout(p)
    print(f"editorial applied ({len(p.data['timeline'])} blocks), saved {out.relative_to(p.root)}")


def cmd_layout(a):
    p = _p(a.name)
    pipeline.do_layout(p)
    for s in p.data["timeline"]:
        print(s["id"], {k: (v["fontSize"], len(v["lines"]), v["status"]) for k, v in s["layout"].items()})


def cmd_verify(a):
    p = _p(a.name)
    found = pipeline.verify_references(p)
    pipeline.prepare_assets(p)
    r = qa.run(p)
    exports.export_all(p)
    print(f"new references: {len(found)}; QA: {r['status']}")
    for g in r["gates"]:
        print(f"  {'✅' if g['ok'] else '❌'} {g['n']:2d} {g['gate']}  {g['detail']}")


def cmd_render(a):
    p = _p(a.name)
    langs = a.lang.split(",") if a.lang else p.data["settings"]["languages"]
    for lang in langs:
        if a.stills:
            print(pipeline.render(p, lang, stills=[int(x) for x in a.stills.split(",")], debug=a.debug))
        else:
            print(pipeline.render(p, lang, preview=a.preview, debug=a.debug))
    qa.run(p)
    exports.export_all(p)


def cmd_export(a):
    p = _p(a.name)
    qa.run(p)
    for f in exports.export_all(p):
        print(f)


def cmd_status(a):
    p = _p(a.name)
    d = p.data
    print(f"{d['name']}  state={d['state']}  mode={d['visual'].get('mode')}  trim={p.trim}")
    print(json.dumps(pipeline.stage_status(p), indent=1))
    for s in d["timeline"]:
        print(f"{s['id']} {s['start']:6.2f}–{s['end']:6.2f} [{p.en_status(s)}]  DE: {s['de']!r}")
    if d.get("errors"):
        print("last error:", d["errors"][-1])


# ------------------------------------------------------------------ edits

def _after_edit(p: Project):
    pipeline.do_layout(p)
    p.save()
    stale = [s["id"] for s in p.data["timeline"] if p.en_status(s) == "STALE_EN"]
    if stale:
        print("STALE_EN:", ", ".join(stale), "→ `regen-en` or `confirm-en`")


def cmd_set_de(a):
    p = _p(a.name)
    segmentation.set_de(p, a.seg, a.text.replace("\\n", "\n"))
    _after_edit(p)


def cmd_set_en(a):
    p = _p(a.name)
    segmentation.set_en(p, a.seg, a.text.replace("\\n", "\n"))
    _after_edit(p)


def cmd_confirm_en(a):
    p = _p(a.name)
    segmentation.confirm_en(p, a.seg)
    _after_edit(p)


def cmd_regen_en(a):
    from .llm import get_provider

    p = _p(a.name)
    stale = a.seg.split(",") if a.seg else [s["id"] for s in p.data["timeline"] if p.en_status(s) != "OK"]
    if not stale:
        print("nothing stale")
        return
    new = get_provider(a.provider).regenerate_en(p, stale)
    for sid, en in new.items():
        segmentation.set_en(p, sid, en)
    _after_edit(p)
    print("regenerated:", ", ".join(new))


def cmd_split(a):
    p = _p(a.name)
    segmentation.split(p, a.seg, a.at_word, tuple(x.replace("\\n", "\n") for x in a.de),
                       tuple(x.replace("\\n", "\n") for x in a.en) if a.en else None)
    _after_edit(p)


def cmd_merge(a):
    p = _p(a.name)
    segmentation.merge(p, a.first, a.second)
    _after_edit(p)


def cmd_boundary(a):
    p = _p(a.name)
    segmentation.move_boundary(p, a.seg, a.to_word)
    _after_edit(p)


def cmd_mask(a):
    p = _p(a.name)
    m = p.data["settings"]["mask"]
    if a.auto:
        m.update(mode="auto", fade_start=None, fade_end=None)
    else:
        fs = a.start if a.start is not None else p.data["visual"]["mask_auto"]["fade_start"]
        fe = a.end if a.end is not None else fs + 0.16
        m.update(mode="manual", fade_start=fs, fade_end=fe)
    p.data["decisions"].append({"at": now(), "what": "mask", "value": dict(m)})
    _after_edit(p)
    print(m)


def cmd_title(a):
    p = _p(a.name)
    ch = p.data["titles"]["chosen"] or {}
    if a.de:
        ch["de"] = a.de
    if a.en:
        ch["en"] = a.en
    p.data["titles"]["chosen"] = ch
    _after_edit(p)


def cmd_intro(a):
    p = _p(a.name)
    p.data["settings"]["intro"] = a.state == "on"
    p.data["decisions"].append({"at": now(), "what": "intro", "value": a.state})
    p.save()


def cmd_editorial_note(a):
    p = _p(a.name)
    n = next(x for x in p.data["editorial_notes"] if x["id"] == a.id)
    if a.enable is not None:
        n["enabled"] = a.enable == "on"
    if a.approve:
        n["status"] = "APPROVED"
    p.save()
    print(n)


def cmd_clone(a):
    p = _p(a.name)
    over = {}
    if a.trim_in is not None:
        over["trim_in"] = a.trim_in
    if a.trim_out is not None:
        over["trim_out"] = a.trim_out
    if a.use_trim_suggestion:
        ts = p.data["source"]["trim_suggestion"]
        over.update(trim_in=ts["trim_in"], trim_out=ts["trim_out"])
    q = p.clone(a.new, **over)
    if "trim_in" in over and q.data["visual"].get("analysis"):
        from . import media

        b = q.data["visual"]["analysis"]["content_box"]
        q.data["visual"]["freeze_time"] = media.first_usable_frame_time(q.source_path, q.trim[0], (b["x0"], b["y0"], b["x1"], b["y1"]))
    pipeline.do_layout(q)
    print(f"cloned → {q.root}  trim={q.trim}")


def cmd_approve(a):
    p = _p(a.name)
    r = qa.run(p)
    if not r["all_gates_ok"]:
        sys.exit("QA gates not green – cannot approve")
    p.set_state("APPROVED", note=a.note or "human review done")
    p.save()
    print("APPROVED (nothing is published automatically)")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="abu-aisha", description="Abu Aisha al-Kumasi video engine")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("new", help="create project from a clip")
    s.add_argument("name")
    s.add_argument("--media", required=True)
    s.add_argument("--speaker", required=True, help="as you write it, e.g. 'الشيخ صالح الفوزان حفظه الله'")
    s.add_argument("--mode", default="auto", choices=["auto", "video", "audio_visual"])
    s.add_argument("--no-intro", action="store_true")
    s.add_argument("--profile", default="general", choices=["general", "soft", "tazkiyah", "rebuttal"])
    s.add_argument("--title-de")
    s.add_argument("--title-en")
    s.add_argument("--background", help="image for Audio+Visual mode")
    s.add_argument("--trim-in", type=float, default=0.0)
    s.add_argument("--trim-out", type=float)
    s.add_argument("--source-url")
    s.add_argument("--source-account")
    s.add_argument("--instructions")
    s.set_defaults(fn=cmd_new)

    s = sub.add_parser("run", help="run/resume the whole pipeline")
    s.add_argument("name")
    s.add_argument("--provider", help="claude model id (default claude-opus-5-5) or file:editorial.json")
    s.add_argument("--lang")
    s.add_argument("--preview", action="store_true")
    s.add_argument("--no-render", action="store_true")
    s.set_defaults(fn=cmd_run)

    for nm, fn in (("analyze", cmd_analyze), ("layout", cmd_layout), ("verify", cmd_verify), ("export", cmd_export),
                   ("status", cmd_status)):
        s = sub.add_parser(nm)
        s.add_argument("name")
        s.set_defaults(fn=fn)

    s = sub.add_parser("transcribe")
    s.add_argument("name")
    s.add_argument("--asr-json", help="re-use a stored ASR result instead of running Whisper")
    s.set_defaults(fn=cmd_transcribe)

    s = sub.add_parser("import-transcript", help="Gemini/manual Arabic → aligned")
    s.add_argument("name")
    s.add_argument("file")
    s.set_defaults(fn=cmd_import_transcript)

    s = sub.add_parser("editorial", help="LLM (or file) editorial pass")
    s.add_argument("name")
    s.add_argument("--provider", default=None)
    s.set_defaults(fn=cmd_editorial)

    s = sub.add_parser("render")
    s.add_argument("name")
    s.add_argument("--lang")
    s.add_argument("--preview", action="store_true")
    s.add_argument("--stills", help="frame numbers, comma separated")
    s.add_argument("--debug", action="store_true", help="draw safe zones")
    s.set_defaults(fn=cmd_render)

    for nm, fn in (("set-de", cmd_set_de), ("set-en", cmd_set_en)):
        s = sub.add_parser(nm)
        s.add_argument("name")
        s.add_argument("seg")
        s.add_argument("text", help="use \\n for a semantic line break")
        s.set_defaults(fn=fn)
    s = sub.add_parser("confirm-en")
    s.add_argument("name")
    s.add_argument("seg")
    s.set_defaults(fn=cmd_confirm_en)
    s = sub.add_parser("regen-en")
    s.add_argument("name")
    s.add_argument("--seg")
    s.add_argument("--provider")
    s.set_defaults(fn=cmd_regen_en)

    s = sub.add_parser("split", help="paired DE/EN split at a word anchor")
    s.add_argument("name")
    s.add_argument("seg")
    s.add_argument("at_word", type=int)
    s.add_argument("--de", nargs=2, required=True)
    s.add_argument("--en", nargs=2)
    s.set_defaults(fn=cmd_split)
    s = sub.add_parser("merge")
    s.add_argument("name")
    s.add_argument("first")
    s.add_argument("second")
    s.set_defaults(fn=cmd_merge)
    s = sub.add_parser("boundary", help="move boundary after SEG to word index")
    s.add_argument("name")
    s.add_argument("seg")
    s.add_argument("to_word", type=int)
    s.set_defaults(fn=cmd_boundary)

    s = sub.add_parser("mask", help="manual mask position (fractions of height)")
    s.add_argument("name")
    s.add_argument("--start", type=float)
    s.add_argument("--end", type=float)
    s.add_argument("--auto", action="store_true")
    s.set_defaults(fn=cmd_mask)
    s = sub.add_parser("title")
    s.add_argument("name")
    s.add_argument("--de")
    s.add_argument("--en")
    s.set_defaults(fn=cmd_title)
    s = sub.add_parser("intro")
    s.add_argument("name")
    s.add_argument("state", choices=["on", "off"])
    s.set_defaults(fn=cmd_intro)
    s = sub.add_parser("note", help="enable/approve an editorial note")
    s.add_argument("name")
    s.add_argument("id")
    s.add_argument("--enable", choices=["on", "off"])
    s.add_argument("--approve", action="store_true")
    s.set_defaults(fn=cmd_editorial_note)
    s = sub.add_parser("clone", help="new variant, e.g. with the trim suggestion")
    s.add_argument("name")
    s.add_argument("new")
    s.add_argument("--trim-in", type=float)
    s.add_argument("--trim-out", type=float)
    s.add_argument("--use-trim-suggestion", action="store_true")
    s.set_defaults(fn=cmd_clone)
    s = sub.add_parser("approve")
    s.add_argument("name")
    s.add_argument("--note")
    s.set_defaults(fn=cmd_approve)

    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
