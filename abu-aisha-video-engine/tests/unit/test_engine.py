"""Unit tests for the engine's editorial/layout invariants (no ASR model or renderer needed)."""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "pipeline"))

from abu_aisha import asr, exports, layout, llm, render_input, segmentation  # noqa: E402
from abu_aisha.project import Project, load_defaults, text_hash  # noqa: E402
from abu_aisha.quran import QuranIndex  # noqa: E402

EXAMPLE = ROOT / "data" / "projects" / "ruhaili-eheleben"


@pytest.fixture()
def proj(tmp_path):
    """A copy of the example project's data in a temp dir (media not needed)."""
    data = json.loads((EXAMPLE / "project.json").read_text())
    root = tmp_path / "p"
    root.mkdir()
    return Project(root, copy.deepcopy(data))


# ---------------------------------------------------------------- layout

def test_fit_keeps_semantic_lines_and_respects_box():
    cfg = load_defaults()
    box = layout.canvas_boxes(cfg, {"fade_end": 0.59})["subtitle"]
    w, h = box["right"] - box["left"], box["bottom"] - box["top"]
    r = layout.fit_block("und ihr zeigt,\ndass darin\nein Nutzen liegt.", w, h, cfg["subtitles"], cfg["fonts"])
    assert r["status"] == "OK" and r["lines"] == ["und ihr zeigt,", "dass darin", "ein Nutzen liegt."]
    assert r["width"] <= w and r["height"] <= h
    assert cfg["subtitles"]["font_min"] <= r["fontSize"] <= cfg["subtitles"]["font_max"]


def test_fit_shrinks_long_text_but_never_below_min():
    cfg = load_defaults()
    long = " ".join(["Verhältnismäßigkeitsgrundsatz und Rechtschaffenheit"] * 6)
    r = layout.fit_block(long, 870, 440, cfg["subtitles"], cfg["fonts"])
    assert r["fontSize"] >= cfg["subtitles"]["font_min"]
    assert r["status"] in ("OK", "NEEDS_SPLIT")


def test_fallback_glyphs_are_measured():
    # ḥ and ﷺ are not in Roboto Slab; the fitter measures them with the fallback face.
    w = layout.text_width("der Prophet ﷺ – ḥadīth", "RobotoSlab-ExtraBold.ttf", 70, "Amiri-Bold.ttf")
    assert w > 300


def test_boxes_do_not_collide():
    cfg = load_defaults()
    b = layout.canvas_boxes(cfg, {"fade_end": 0.63})
    assert b["subtitle"]["bottom"] < b["editorial"]["top"] < b["editorial"]["bottom"] < b["brand"]["top"]
    assert b["brand"]["bottom"] <= cfg["video"]["height"] - cfg["safe_zones"]["bottom"]


# ------------------------------------------------------------- timeline

def test_example_timeline_covers_every_word_once(proj):
    segs = [{"words": [s["source_word_start"], s["source_word_end"]]} for s in proj.data["timeline"]]
    llm.check_coverage(segs, len(proj.data["transcript"]["word_timings"]))


def test_coverage_check_rejects_gaps():
    with pytest.raises(ValueError):
        llm.check_coverage([{"words": [0, 3]}, {"words": [5, 9]}], 10)
    with pytest.raises(ValueError):
        llm.check_coverage([{"words": [0, 3]}], 10)


def test_no_blank_flash_and_no_overlap(proj):
    tl = proj.data["timeline"]
    for a, b in zip(tl, tl[1:]):
        gap = b["start"] - a["end"]
        assert gap >= -1e-6
        assert not (0 < gap < 0.25)


def test_editing_german_marks_only_that_english_stale(proj):
    seg = proj.data["timeline"][3]["id"]
    assert all(proj.en_status(s) == "OK" for s in proj.data["timeline"])
    segmentation.set_de(proj, seg, "sie darin bestärkt")
    stale = [s["id"] for s in proj.data["timeline"] if proj.en_status(s) != "OK"]
    assert stale == [seg]
    segmentation.confirm_en(proj, seg)
    assert proj.en_status(proj.segment(seg)) == "OK"


def test_paired_split_and_merge_roundtrip(proj):
    s = proj.segment("seg_013")  # فتطيب الحياة
    n = len(proj.data["timeline"])
    segmentation.split(proj, "seg_013", s["source_word_start"] + 1, ("so wird", "das Leben schön."), ("so", "life becomes beautiful."))
    assert len(proj.data["timeline"]) == n + 1
    a, b = proj.data["timeline"][12], proj.data["timeline"][13]
    assert a["end"] <= b["start"] + 1e-6 and a["source_word_end"] + 1 == b["source_word_start"]
    segmentation.merge(proj, a["id"], b["id"])
    assert len(proj.data["timeline"]) == n
    assert proj.en_status(proj.data["timeline"][12]) == "OK"


# ------------------------------------------------------------ rendering

def test_check_required_is_never_rendered(proj):
    proj.data["editorial_notes"].append({"id": "x", "kind": "context", "text": {"de": "Ibn Rajab starb 795 n. H."},
                                          "start": 10, "end": 14, "status": "CHECK_REQUIRED", "enabled": True})
    ri = render_input.build(proj, "de")
    assert "x" not in [e["id"] for e in ri["editorial"]]
    assert "ed_001" in [e["id"] for e in ri["editorial"]]


def test_de_en_share_one_timing_map(proj):
    de, en = render_input.build(proj, "de"), render_input.build(proj, "en")
    assert [(s["id"], s["start"], s["end"]) for s in de["segments"]] == [(s["id"], s["start"], s["end"]) for s in en["segments"]]
    assert de["stage"] == en["stage"] and de["mask"] == en["mask"] and de["intro"]["duration"] == en["intro"]["duration"]


def test_manual_mask_override_persists(proj):
    proj.data["settings"]["mask"] = {"mode": "manual", "fade_start": 0.41, "fade_end": 0.57}
    assert render_input.build(proj, "de")["mask"] == {"fadeStart": 0.41, "fadeEnd": 0.57, "topFade": 0.05}


def test_trim_rebases_times(proj):
    proj.data["source"]["trim_in"], proj.data["source"]["trim_out"] = 6.9, 60.0
    ri = render_input.build(proj, "de")
    assert ri["contentDuration"] == pytest.approx(53.1)
    assert ri["segments"][0]["id"] == "seg_002" and ri["segments"][0]["start"] >= 0
    assert all(s["end"] <= 53.1 + 1e-6 for s in ri["segments"])
    srt = exports.srt(proj, "de")
    assert srt.startswith("1\n00:00:04,")  # intro offset + trim


def test_spoken_and_editorial_are_distinct(proj):
    ri = render_input.build(proj, "de")
    ed = ri["editorial"][0]["fontSize"]
    assert ed <= 0.72 * min(s["layout"]["fontSize"] for s in ri["segments"])
    assert ri["style"]["editorialColor"].lower() != ri["style"]["fill"].lower()


# ------------------------------------------------------------------ misc

def test_hex_token_decoding_keeps_split_arabic_letters():
    # "الزوج": the ز is split across two byte-level tokens (d8 | b2)
    toks = ["20d8a7d984d8|", "b2|", "d988d8ac|"]
    assert asr._decode_tokens(toks) == "الزوج"


def test_quran_matcher_handles_uthmani_vs_imlai():
    idx = QuranIndex([(30, 21, "وَمِنۡ ءَايَٰتِهِۦٓ أَنۡ خَلَقَ لَكُم مِّنۡ أَنفُسِكُمۡ أَزۡوَٰجٗا لِّتَسۡكُنُوٓاْ إِلَيۡهَا"),
                      (4, 19, "وَعَاشِرُوهُنَّ بِٱلۡمَعۡرُوفِۚ فَإِن كَرِهۡتُمُوهُنَّ")])
    m = idx.match("ومن آياته أن خلق لكم من أنفسكم أزواجا لتسكنوا إليها")
    assert m["sura"] == 30 and m["aya_from"] == 21 and m["status"].startswith("VERIFIED")
    assert m["label"] == "Sūrat ar-Rūm [30:21]"
    assert idx.match("مما تطيب به الحياة بين الزوجين") is None


def test_hash_is_whitespace_insensitive_at_edges():
    assert text_hash(" a ") == text_hash("a")


def test_example_project_matches_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((ROOT / "packages" / "schema" / "project.schema.json").read_text())
    jsonschema.validate(json.loads((EXAMPLE / "project.json").read_text()), schema)
