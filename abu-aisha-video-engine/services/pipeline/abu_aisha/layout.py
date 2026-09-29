"""Canvas geometry and dynamic subtitle fitting (spec §18.5–18.7, §19, §24).

Fitting runs here (FreeType metrics of the exact font files the renderer loads)
so that the result is stored in the project, QA-checkable, and identical across
re-renders. The renderer only draws the given lines at the given size.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .paths import FONTS_DIR


@lru_cache(maxsize=64)
def _font(name: str, size: int):
    from PIL import ImageFont

    return ImageFont.truetype(str(FONTS_DIR / name), size)


@lru_cache(maxsize=8)
def _cmap(name: str) -> frozenset:
    from fontTools.ttLib import TTFont

    return frozenset(TTFont(str(FONTS_DIR / name)).getBestCmap().keys())


def text_width(text: str, font: str, size: int, fallback: str | None = None) -> float:
    """Width in px, per-run fallback for glyphs the primary face lacks (e.g. ḥ, ﷺ)."""
    if not text:
        return 0.0
    cmap = _cmap(font)
    runs: list[tuple[str, str]] = []
    for ch in text:
        f = font if (ord(ch) in cmap or fallback is None or ch.isspace()) else fallback
        if runs and runs[-1][0] == f:
            runs[-1] = (f, runs[-1][1] + ch)
        else:
            runs.append((f, ch))
    return sum(_font(f, size).getlength(t) for f, t in runs)


def _wrap_balanced(words: list[str], max_w: float, measure) -> list[str] | None:
    """Minimum-raggedness wrap (DP). None if a single word is wider than max_w."""
    n = len(words)
    widths = {}

    def w(i, j):
        if (i, j) not in widths:
            widths[(i, j)] = measure(" ".join(words[i:j]))
        return widths[(i, j)]

    best = [0.0] + [float("inf")] * n
    back = [0] * (n + 1)
    for j in range(1, n + 1):
        for i in range(j - 1, -1, -1):
            lw = w(i, j)
            if lw > max_w:
                if i == j - 1:
                    return None
                break
            cost = best[i] + ((max_w - lw) / max_w) ** 2
            # discourage a lone short last word (widow)
            if j == n and j - i == 1 and n > 2:
                cost += 0.35
            if cost < best[j]:
                best[j], back[j] = cost, i
    lines, j = [], n
    while j > 0:
        i = back[j]
        lines.append(" ".join(words[i:j]))
        j = i
    return lines[::-1]


def fit_block(text: str, box_w: float, box_h: float, sub: dict, fonts: dict, font_max: int | None = None) -> dict:
    """Largest font size at which the block fits the box (§18.7).

    Semantic line breaks (\\n) authored by the editor are kept; a paragraph is
    only re-wrapped when it cannot fit on one line. Returns lines, size and a
    status: OK | NEEDS_SPLIT (still too big at font_min).
    """
    fmax = font_max or sub["font_max"]
    fmin = sub["font_min"]
    step = sub.get("font_step", 2)
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    primary, fallback = fonts["subtitle"], fonts.get("subtitle_fallback")
    # Pass 1 keeps the editor's semantic lines intact; pass 2 may re-wrap a line.
    keep_floor = max(fmin, sub.get("keep_lines_font_min", 58))
    for allow_wrap in (False, True):
        for size in range(fmax, (fmin if allow_wrap else keep_floor) - 1, -step):
            res = _try_size(paras, size, box_w, box_h, sub, primary, fallback, allow_wrap)
            if res:
                return res
    return {"fontSize": fmin, "lines": paras, "lineHeight": round(fmin * sub["line_height"]), "status": "NEEDS_SPLIT",
            "width": None, "height": None}


def _try_size(paras, size, box_w, box_h, sub, primary, fallback, allow_wrap):
    stroke = size * sub["stroke_ratio"]
    avail = box_w - stroke - 8  # stroke spills outside glyphs; small safety margin
    lh = round(size * sub["line_height"])
    measure = lambda s: text_width(s, primary, size, fallback)  # noqa: E731
    lines: list[str] = []
    for p in paras:
        if measure(p) <= avail:
            lines.append(p)
            continue
        if not allow_wrap:
            return None
        wrapped = _wrap_balanced(p.split(), avail, measure)
        if wrapped is None:
            return None
        lines.extend(wrapped)
    if len(lines) > sub["maximum_lines"] or len(lines) * lh + stroke > box_h:
        return None
    widest = max(measure(l) for l in lines) + stroke
    return {"fontSize": size, "lines": lines, "lineHeight": lh, "status": "OK", "width": round(widest, 1),
            "height": len(lines) * lh, "rewrapped": allow_wrap}


def canvas_boxes(cfg: dict, mask: dict) -> dict:
    """Subtitle box, editorial lane and brand lockup geometry in canvas px."""
    W, H = cfg["video"]["width"], cfg["video"]["height"]
    sz = cfg["safe_zones"]
    L = cfg["layout"]
    brand_h = L["brand_height"]
    brand_bottom = H - sz["bottom"]
    brand_top = brand_bottom - brand_h
    lane_bottom = brand_top - L["gap_px"]
    lane_top = lane_bottom - L["editorial_lane_height"]
    sub_top = round(mask["fade_end"] * H - L["subtitle_top_overlap_px"])
    sub_bottom = lane_top - L["gap_px"]
    return {
        "subtitle": {"top": sub_top, "bottom": sub_bottom, "left": sz["left"], "right": W - sz["right"]},
        "editorial": {"top": lane_top, "bottom": lane_bottom, "left": sz["left"], "right": W - sz["right"]},
        "brand": {"top": brand_top, "height": brand_h, "bottom": brand_bottom},
    }


def fit_title(title: str, box_w: float, cfg: dict) -> dict:
    t = cfg["title"]
    fonts = cfg["fonts"]
    sub = dict(cfg["subtitles"], font_max=t["font_max"], font_min=t["font_min"], maximum_lines=t["max_lines"], line_height=1.08)
    fonts_t = {"subtitle": fonts["title"], "subtitle_fallback": fonts["subtitle_fallback"]}
    return fit_block(title.upper(), box_w, 10_000, sub, fonts_t)


def editorial_font_size(cfg: dict) -> int:
    return round(cfg["subtitles"]["font_max"] * cfg["subtitles"]["editorial_context_scale"] * 0.75)
