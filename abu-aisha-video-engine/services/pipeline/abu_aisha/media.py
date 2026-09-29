"""Media ingest, preflight and FFmpeg plumbing (spec §8, §18.2, §20.2, §21, §22).

Everything here is deterministic and cheap; results are written into
project["visual"] / project["source"] so a re-render never re-analyses.
"""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

import numpy as np


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def probe(path: str | Path) -> dict:
    out = json.loads(run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)]))
    v = next((s for s in out["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in out["streams"] if s["codec_type"] == "audio"), None)
    info = {"duration": float(out["format"]["duration"]), "has_audio": a is not None, "has_video": v is not None}
    if v:
        w, h = int(v["width"]), int(v["height"])
        rot = 0
        for sd in v.get("side_data_list", []) or []:
            if "rotation" in sd:
                rot = int(sd["rotation"])
        if abs(rot) in (90, 270):
            w, h = h, w
        num, den = v.get("r_frame_rate", "30/1").split("/")
        info.update(width=w, height=h, rotation=rot, fps=round(float(num) / float(den or 1), 3), vcodec=v["codec_name"])
    if a:
        info.update(acodec=a["codec_name"], sample_rate=int(a.get("sample_rate", 0)), channels=int(a.get("channels", 0)))
    return info


def grab_frame(src: str | Path, t: float, dst: str | Path, vf: str | None = None) -> Path:
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, t):.3f}", "-i", str(src), "-frames:v", "1"]
    if vf:
        cmd += ["-vf", vf]
    subprocess.run(cmd + [str(dst)], check=True)
    return Path(dst)


def sample_frames(src: str | Path, duration: float, n: int = 16, width: int | None = None) -> list[np.ndarray]:
    """Grey frames sampled uniformly (skipping the very first/last 2%)."""
    import cv2

    cap = cv2.VideoCapture(str(src))
    frames = []
    for k in range(n):
        t = duration * (0.02 + 0.96 * k / max(1, n - 1))
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, fr = cap.read()
        if not ok:
            continue
        if width:
            fr = cv2.resize(fr, (width, int(fr.shape[0] * width / fr.shape[1])))
        frames.append(fr)
    cap.release()
    return frames


def content_box(frames: list[np.ndarray]) -> tuple[int, int, int, int]:
    """Largest region with real picture content (x0, y0, x1, y1).

    Detects letterboxing and pre-baked gradients from re-uploads: rows/cols
    whose horizontal texture AND temporal variation are ~0 are not content.
    """
    import cv2

    g = np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32) for f in frames])
    tex_r = np.abs(np.diff(g, axis=2)).mean(axis=(0, 2))  # per row
    lum_r = g.mean(axis=(0, 2))
    tmp_r = g.std(axis=0).mean(axis=1)
    row_ok = (tex_r > 1.2) | (tmp_r > 6) | (lum_r > 90)
    y0, y1 = _longest_run(row_ok)
    band = g[:, y0:y1, :]
    tex_c = np.abs(np.diff(band, axis=1)).mean(axis=(0, 1))  # per column, inside the content rows only
    lum_c = band.mean(axis=(0, 1))
    tmp_c = band.std(axis=0).mean(axis=0)
    col_ok = (tex_c > 1.0) | (tmp_c > 6) | (lum_c > 90)
    x0, x1 = _longest_run(col_ok)
    return int(x0), int(y0), int(x1), int(y1)


def _longest_run(mask: np.ndarray) -> tuple[int, int]:
    best, cur, start = (0, len(mask)), 0, 0
    best_len = 0
    for i, m in enumerate(list(mask) + [False]):
        if m:
            if cur == 0:
                start = i
            cur += 1
        else:
            if cur > best_len:
                best_len, best = cur, (start, i)
            cur = 0
    return best


def detect_subject(frames: list[np.ndarray], box: tuple[int, int, int, int]) -> dict:
    """Face-based subject estimate inside the content box, motion fallback."""
    import cv2

    x0, y0, x1, y1 = box
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = []
    for f in frames:
        crop = cv2.cvtColor(f[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
        scale = 2.0 if crop.shape[1] < 700 else 1.0
        big = cv2.resize(crop, None, fx=scale, fy=scale)
        for fx, fy, fw, fh in casc.detectMultiScale(big, 1.08, 5, minSize=(int(24 * scale), int(24 * scale))):
            faces.append((fx / scale, fy / scale, fw / scale, fh / scale))
    if faces:
        a = np.array(faces)
        cx = float(np.median(a[:, 0] + a[:, 2] / 2)) + x0
        cy = float(np.median(a[:, 1] + a[:, 3] / 2)) + y0
        fh = float(np.median(a[:, 3]))
        return {"method": "face", "cx": cx, "cy": cy, "face_h": fh, "hits": len(faces), "frames": len(frames)}
    g = np.stack([cv2.cvtColor(f[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY).astype(np.float32) for f in frames])
    motion = np.abs(np.diff(g, axis=0)).mean(axis=0)
    cols = motion.mean(axis=0)
    rows = motion.mean(axis=1)
    cx = float((cols * np.arange(len(cols))).sum() / (cols.sum() + 1e-6)) + x0
    cy = float((rows * np.arange(len(rows))).sum() / (rows.sum() + 1e-6)) + y0
    return {"method": "motion", "cx": cx, "cy": cy, "face_h": None, "hits": 0, "frames": len(frames)}


def static_text_regions(frames: list[np.ndarray], box: tuple[int, int, int, int]) -> list[dict]:
    """Burned-in text / lower thirds: bands with dense edges that do not change over time."""
    import cv2

    x0, y0, x1, y1 = box
    edges = []
    for f in frames:
        g = cv2.cvtColor(f[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
        edges.append(cv2.Canny(g, 80, 180).astype(np.float32) / 255)
    e = np.stack(edges)
    persistent = (e.mean(axis=0) > 0.6).astype(np.float32)  # edge present in >60% of frames
    rows = persistent.mean(axis=1)
    h = y1 - y0
    thr = max(0.02, float(np.percentile(rows, 85)))
    out, k = [], 0
    while k < h:
        if rows[k] > thr:
            j = k
            while j < h and rows[j] > thr * 0.5:
                j += 1
            if j - k >= max(4, h * 0.02):
                band = persistent[k:j]
                colsum = band.mean(axis=0)
                xs = np.where(colsum > 0.02)[0]
                out.append({
                    "y0": int(k + y0), "y1": int(j + y0),
                    "x0": int((xs.min() if len(xs) else 0) + x0), "x1": int((xs.max() if len(xs) else x1 - x0) + x0),
                    "density": round(float(band.mean()), 3),
                    "rel_y": round((k + j) / 2 / h, 3),
                })
            k = j
        else:
            k += 1
    return out


def first_usable_frame_time(src: str | Path, start: float, box: tuple[int, int, int, int], limit: float = 3.0) -> float:
    """Spec §20.2: skip black frames / transition blur near the start."""
    import cv2

    cap = cv2.VideoCapture(str(src))
    x0, y0, x1, y1 = box
    t = start
    best_t, best_sharp = start, -1.0
    while t <= start + limit:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, fr = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(fr[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
        lum = float(g.mean())
        sharp = float(cv2.Laplacian(g, cv2.CV_64F).var())
        if lum > 25 and sharp > 30:
            cap.release()
            return round(t, 3)
        if sharp > best_sharp:
            best_t, best_sharp = t, sharp
        t += 0.1
    cap.release()
    return round(best_t, 3)


def audio_levels(src: str | Path, trim_in: float = 0, trim_out: float | None = None) -> dict:
    cmd = ["ffmpeg", "-v", "info", "-ss", f"{trim_in:.3f}", "-i", str(src)]
    if trim_out:
        cmd += ["-t", f"{trim_out - trim_in:.3f}"]
    cmd += ["-vn", "-af", "volumedetect", "-f", "null", "-"]
    err = subprocess.run(cmd, capture_output=True, text=True).stderr
    res = {}
    for key in ("mean_volume", "max_volume"):
        for line in err.splitlines():
            if key in line:
                res[key] = float(line.split(":")[-1].strip().split()[0])
    return res


def waveform(wav_samples: np.ndarray, sr: int, points_per_sec: int = 50) -> list[float]:
    hop = sr // points_per_sec
    n = len(wav_samples) // hop
    a = np.abs(wav_samples[: n * hop]).reshape(n, hop).max(axis=1)
    return [round(float(v), 3) for v in a]


# ------------------------------------------------------------------ geometry

def plan_stage(info: dict, box: tuple[int, int, int, int], subject: dict, text_regions: list[dict], cfg: dict) -> dict:
    """Choose crop + placement of the source picture on the 1080×1920 canvas and
    an automatic mask (spec §18.3). Returns canvas-space numbers."""
    W, H = cfg["video"]["width"], cfg["video"]["height"]
    st = cfg["stage"]
    x0, y0, x1, y1 = box
    cw, ch = x1 - x0, y1 - y0
    top = st["top_landscape"] if cw / ch > 1.1 else 0
    max_zoom = st["max_upscale"]
    # Desired picture height: down to the default fade end, limited by acceptable upscaling.
    desired_bottom = cfg["mask"]["default_fade_end"] * H
    target_h = desired_bottom - top
    zoom = min(target_h / ch, max_zoom)
    zoom = max(zoom, W / cw)  # never narrower than the canvas
    crop_w = W / zoom
    crop_h = min(ch, target_h / zoom)
    # Horizontal: centre on subject, clamp inside content.
    cx = subject.get("cx", (x0 + x1) / 2)
    cxs = min(max(cx - crop_w / 2, x0), x1 - crop_w)
    # Vertical: keep top of content (titles/banners, attribution) unless subject would be too low.
    cys = y0
    if subject.get("cy") and (subject["cy"] - cys) * zoom > 0.42 * target_h:
        cys = min(max(subject["cy"] - 0.36 * target_h / zoom, y0), y1 - crop_h)
    stage_h = round(crop_h * zoom)
    stage = {
        "crop": {"x": round(cxs, 2), "y": round(cys, 2), "w": round(crop_w, 2), "h": round(crop_h, 2)},
        "zoom": round(zoom, 3),
        "y": int(top),
        "height": int(stage_h - stage_h % 2),
    }
    stage_bottom = top + stage["height"]
    fade_end = min(stage_bottom / H + 0.02, cfg["mask"]["fade_end_max"])
    fade_end = max(fade_end, cfg["mask"]["fade_end_min"])
    fade_len = cfg["mask"]["default_fade_end"] - cfg["mask"]["default_fade_start"]
    fade_start = fade_end - fade_len
    reasons = [f"stage bottom at {stage_bottom}px ({stage_bottom / H:.3f})"]
    # Raise the mask so burned-in text in the lower part of the picture is hidden (§18.3, §21).
    for r in text_regions:
        if r["rel_y"] < 0.72:  # only lower-third / burned subtitle zone, not banners beside the speaker
            continue
        ry0 = top + (r["y0"] - cys) * zoom
        if ry0 < fade_end * H and ry0 / H - 0.02 < fade_start + fade_len * 0.55:
            new_start = max(cfg["mask"]["fade_start_min"], ry0 / H - fade_len * 0.55)
            if new_start < fade_start:
                reasons.append(f"burned-in text at canvas y≈{ry0:.0f}px → mask raised")
                fade_start = new_start
                fade_end = min(fade_end, fade_start + fade_len)
    return {
        "stage": stage,
        "mask": {"fade_start": round(fade_start, 4), "fade_end": round(fade_end, 4), "reasons": reasons},
    }


def prepare_stage_video(src: str | Path, dst: str | Path, crop: dict, width: int, height: int, fps: int,
                        trim_in: float, trim_out: float, sharpen: bool = True) -> Path:
    """Crop + high-quality upscale once with FFmpeg so the renderer only composites."""
    vf = (
        f"crop={crop['w']:.2f}:{crop['h']:.2f}:{crop['x']:.2f}:{crop['y']:.2f},"
        f"scale={width}:{height}:flags=lanczos+accurate_rnd+full_chroma_int,"
        + ("unsharp=5:5:0.55:5:5:0.0," if sharpen else "")
        + f"fps={fps},format=yuv420p"
    )
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-ss", f"{trim_in:.3f}", "-i", str(src), "-t", f"{trim_out - trim_in:.3f}",
        "-vf", vf, "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "12", "-g", "15", str(dst),
    ], check=True)
    return Path(dst)


def prepare_freeze(src: str | Path, dst: str | Path, t: float, crop: dict, width: int, height: int, sharpen: bool = True) -> Path:
    vf = (
        f"crop={crop['w']:.2f}:{crop['h']:.2f}:{crop['x']:.2f}:{crop['y']:.2f},"
        f"scale={width}:{height}:flags=lanczos+accurate_rnd+full_chroma_int"
        + (",unsharp=5:5:0.55:5:5:0.0" if sharpen else "")
    )
    return grab_frame(src, t, dst, vf)


def prepare_audio(src: str | Path, dst: str | Path, trim_in: float, trim_out: float, limiter: bool) -> Path:
    """Original voice, 0 dB. Only a true-peak safety limiter if the source would clip (§9)."""
    af = ["alimiter=limit=0.97:level=false:attack=1:release=50"] if limiter else []
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{trim_in:.3f}", "-i", str(src), "-t", f"{trim_out - trim_in:.3f}", "-vn"]
    if af:
        cmd += ["-af", ",".join(af)]
    cmd += ["-c:a", "pcm_s16le", str(dst)]
    subprocess.run(cmd, check=True)
    return Path(dst)


def make_proxy(src: str | Path, dst: str | Path) -> Path:
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", "scale=-2:640,fps=30", "-c:v", "libx264",
        "-preset", "veryfast", "-crf", "28", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(dst),
    ], check=True)
    return Path(dst)


def orientation(w: int, h: int) -> str:
    r = w / h
    if r > 1.15:
        return "landscape"
    if r < 0.87:
        return "portrait"
    return "square"


def ceil_even(x: float) -> int:
    return int(math.ceil(x / 2) * 2)
