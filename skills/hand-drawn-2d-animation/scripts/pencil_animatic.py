#!/usr/bin/env python3
"""Turn a finished film into rough pencil animation for a breakdown/BTS: loose graphite line, hatching, paper and boil.

Usage:
  python3 pencil_animatic.py film.mp4 depth.mp4 output.mp4 [--start 0] [--dur 30] [--test 13,18,24]
                             [--lines lines.mp4] [--fps 12] [--style rough|test|animatic|isnet] [--model isnetis.onnx]

- depth.mp4 is a depth-map video synced to the film (from any monocular video depth model). It decides what
  stays: near and mid planes (character, props, close leaves) stay drawn; the distant background fades into
  the paper, the way an animator draws only the character.
- Line by the dodge method (pencil sketch), darkened and re-traced with an offset: loose line.
- Hatching in short irregular strokes, only inside dark areas.
- A new drawing every 2 frames ("on twos") with a fresh wobble: the "boil" of pencil animation.
- --test writes only PNGs of those seconds, to approve the look before the render.
- --lines takes a ready line video (sketch_lines.py --raw) synced to --start; required by the test,
  animatic and isnet styles.
- --style isnet cuts the character out with isnet-anime (https://huggingface.co/skytnt/anime-seg,
  Apache-2.0, file isnetis.onnx); pass the downloaded file with --model. Weights are not bundled.
Requires numpy, opencv-python and ffmpeg (plus onnxruntime for --style isnet). No generative AI, no credits.
"""
import argparse
import os
import subprocess
import sys

try:
    import cv2
    import numpy as np
except ImportError:  # checked in main() so --help and setup messages still work
    cv2 = np = None

W, H = 1280, 720  # drawing resolution; output is scaled to 1920x1080
PAPER = (236, 240, 244)  # BGR, slightly warm paper
GRAPHITE = (62, 58, 56)

ISNET_HELP = """isnet-anime model not found.
  1. Download isnetis.onnx from https://huggingface.co/skytnt/anime-seg (Apache-2.0)
  2. pip install onnxruntime
  3. Pass it with --model path/to/isnetis.onnx
The model is not redistributed with this skill."""


def read(path, start, dur, fps=12, w=W, h=H, gray=False):
    fmt = "gray" if gray else "bgr24"
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", path,
           "-vf", f"fps={fps},scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", fmt, "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    c = 1 if gray else 3
    n = w * h * c
    return [np.frombuffer(raw[i:i + n], np.uint8).reshape(h, w) if gray else
            np.frombuffer(raw[i:i + n], np.uint8).reshape(h, w, 3) for i in range(0, len(raw) - n + 1, n)]


def displace(img, rnd, amp, scale=90):
    """Smooth random warp: the line 'trembles' like a hand drawing it again."""
    gh, gw = H // scale + 2, W // scale + 2
    dx = cv2.resize(rnd.normal(0, amp, (gh, gw)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    dy = cv2.resize(rnd.normal(0, amp, (gh, gw)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    mx, my = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    return cv2.remap(img, mx + dx, my + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def pencil_sketch(gray):
    """Pencil sketch by the dodge method: darkens only where there is an edge, the rest becomes paper."""
    g = cv2.bilateralFilter(gray, 9, 40, 9)
    g = cv2.medianBlur(g, 5)
    inv = 255 - g
    bl = cv2.GaussianBlur(inv, (0, 0), 5)
    sk = cv2.divide(g, 255 - bl, scale=256).astype(np.float32) / 255.0
    sk = np.clip(sk, 0, 1) ** 5  # graphite contrast
    return np.clip(1.0 - sk, 0, 1)  # 1 = line


def hatching(dark, rnd, density=0.0011, length=(10, 26), angle=55):
    """Short irregular strokes, one by one, only where it is dark (like an animator shading)."""
    hh, ww = dark.shape
    canvas = np.zeros((hh, ww), np.uint8)
    ys, xs = np.nonzero(dark > 0.5)
    if len(xs) == 0:
        return canvas.astype(np.float32)
    n = int(len(xs) * density)
    idx = rnd.choice(len(xs), size=min(n, len(xs)), replace=False)
    for i in idx:
        L = rnd.uniform(*length)
        a = np.deg2rad(angle + rnd.normal(0, 6))
        x0, y0 = xs[i], ys[i]
        x1, y1 = int(x0 + L * np.cos(a)), int(y0 - L * np.sin(a))
        cv2.line(canvas, (int(x0), int(y0)), (x1, y1), 255, 1, cv2.LINE_AA)
    return canvas.astype(np.float32) / 255.0


def rough(rgb, dep, rnd, paper_grain, lines=None):
    gray = cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY)
    d = cv2.GaussianBlur(dep.astype(np.float32) / 255.0, (0, 0), 5)
    mask = np.clip((d - 0.17) / 0.10, 0, 1)  # distant background becomes blank paper
    if lines is not None:  # ready line (Anime2Sketch): darken and thicken it into graphite
        tr = np.clip((1.0 - lines.astype(np.float32) / 255.0) * 2.2, 0, 1) ** 0.7
        tr = cv2.dilate(tr, np.ones((2, 2), np.uint8))
    else:
        tr = pencil_sketch(gray)
        tr = np.clip(tr * 1.6, 0, 1)
    t1 = displace(tr, rnd, 1.4)
    t2 = displace(tr, rnd, 3.2) * 0.38  # loose, lighter re-trace
    stroke = np.clip(np.maximum(t1, t2) * mask, 0, 1)
    dark = np.clip((0.24 - gray.astype(np.float32) / 255.0) / 0.10, 0, 1) * mask
    hatch = hatching(cv2.GaussianBlur(dark, (0, 0), 2), rnd) * 0.75
    ink = np.clip(stroke + hatch, 0, 1) * (0.72 + 0.28 * paper_grain)
    paper, graphite = np.array(PAPER, np.float32), np.array(GRAPHITE, np.float32)
    out = paper[None, None, :] * (1 - ink[..., None]) + graphite[None, None, :] * ink[..., None]
    out *= (0.975 + 0.025 * paper_grain)[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


def pencil_test(rgb, dep, paper_grain, lines):
    """Pencil-test look: character in dark clean line; background in light smudged graphite."""
    gray = cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    d = cv2.GaussianBlur(dep.astype(np.float32) / 255.0, (0, 0), 3)
    # the character sits in the mid depth band; leaves glued to the lens and the far background become set
    char = np.clip((d - 0.24) / 0.08, 0, 1) * np.clip((0.86 - d) / 0.08, 0, 1)
    char = cv2.GaussianBlur(char, (0, 0), 2)
    tr = np.clip((1.0 - lines.astype(np.float32) / 255.0) * 2.6, 0, 1) ** 0.6
    tr = cv2.dilate(tr, np.ones((2, 2), np.uint8))
    bg_tone = np.clip((1.0 - cv2.GaussianBlur(gray, (0, 0), 4)) * 0.11, 0, 1)  # very light smudged graphite
    bg_line = tr * 0.17
    ink_bg = np.maximum(bg_tone, bg_line) * (0.8 + 0.2 * paper_grain)
    ink_char = tr * 0.95
    ink = ink_bg * (1 - char) + np.maximum(ink_char, ink_bg * 0.5) * char
    paper = np.array([243, 244, 245], np.float32)
    graphite = np.array([40, 40, 44], np.float32)
    out = paper[None, None] * (1 - ink[..., None]) + graphite[None, None] * ink[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


def pink_mask(hsv):
    """Saturated pink areas (in the BOLHAO example, the bubble): always kept as part of the character."""
    return (((hsv[..., 0] >= 140) | (hsv[..., 0] <= 8)) & (hsv[..., 1] > 35) & (hsv[..., 2] > 120))


def line_animatic(rgb, dep, lines):
    """Animatic, line only. Character in full line; set only with its long strokes (trunk, ground, horizon), light."""
    hsv = cv2.cvtColor(rgb, cv2.COLOR_BGR2HSV)
    d = cv2.GaussianBlur(dep.astype(np.float32) / 255.0, (0, 0), 3)
    leaf_sky = ((hsv[..., 0] >= 30) & (hsv[..., 0] <= 105) & (hsv[..., 1] > 50)).astype(np.float32)
    leaf_sky = cv2.morphologyEx(leaf_sky, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    char = np.clip((d - 0.26) / 0.08, 0, 1) * np.clip((0.84 - d) / 0.08, 0, 1) * (1 - leaf_sky)
    pink = pink_mask(hsv).astype(np.float32)
    char = np.maximum(char, cv2.morphologyEx(pink, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8)))
    char = cv2.morphologyEx(char, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    char = cv2.GaussianBlur((cv2.GaussianBlur(char, (0, 0), 3) > 0.5).astype(np.float32), (0, 0), 1.5)
    tr = np.clip((1.0 - lines.astype(np.float32) / 255.0) * 2.6, 0, 1)
    line_bin = (tr > 0.5).astype(np.uint8)  # line only: the model's grey shading goes away
    line_bin = cv2.dilate(line_bin, np.ones((2, 2), np.uint8))
    # inside the character, loose specks also go (ground texture that fell into the mask)
    inside = (line_bin * (char >= 0.5)).astype(np.uint8)
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inside, connectivity=8)
    clean = np.zeros_like(inside)
    for i in range(1, n2):
        if max(st2[i, cv2.CC_STAT_WIDTH], st2[i, cv2.CC_STAT_HEIGHT]) >= 7:
            clean[lab2 == i] = 1
    # outline of round pink shapes, drawn as a line
    pink_m = cv2.morphologyEx(pink, cv2.MORPH_CLOSE, np.ones((31, 31), np.uint8))  # closes the face seen through the bubble
    pink_m = (cv2.GaussianBlur(pink_m, (0, 0), 4) > 0.5).astype(np.uint8)
    cs, _ = cv2.findContours(pink_m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    for c in cs:
        area, per = cv2.contourArea(c), cv2.arcLength(c, True)
        if area > 4000 and 4 * np.pi * area / (per * per + 1e-6) > 0.55:  # round shapes only
            cv2.polylines(clean, [cv2.convexHull(c)], True, 1, 2, cv2.LINE_AA)
    char_ink = cv2.GaussianBlur(clean.astype(np.float32), (0, 0), 0.7)
    # set: long line components; leaf specks and texture go
    bg = (line_bin * (char < 0.5)).astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(bg, connectivity=8)
    long_lines = np.zeros_like(bg)
    for i in range(1, n):
        w, h, area = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT], stats[i, cv2.CC_STAT_AREA]
        filled = area / float(w * h)
        if max(w, h) >= 110 and filled < 0.12:  # long thin stroke; blobs and foliage go
            long_lines[labels == i] = 1
    set_ink = cv2.GaussianBlur(long_lines.astype(np.float32), (0, 0), 0.8) * 0.40
    ink = np.maximum(char_ink, set_ink)
    paper = np.array([243, 244, 245], np.float32)
    graphite = np.array([38, 38, 42], np.float32)
    out = paper[None, None] * (1 - ink[..., None]) + graphite[None, None] * ink[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


_SEG = None


def character_matte(rgb, model):
    """Character silhouette by isnet-anime (huggingface.co/skytnt/anime-seg, Apache-2.0). 1 = character."""
    global _SEG
    import onnxruntime as ort
    if _SEG is None:
        _SEG = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
    h, w = rgb.shape[:2]
    s = 1024 / max(h, w)
    nh, nw = int(h * s), int(w * s)
    img = np.zeros((1024, 1024, 3), np.float32)
    ph, pw = (1024 - nh) // 2, (1024 - nw) // 2
    img[ph:ph + nh, pw:pw + nw] = cv2.resize(cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB), (nw, nh)).astype(np.float32) / 255.0
    m = _SEG.run(None, {"img": img.transpose(2, 0, 1)[None]})[0][0, 0]
    m = m[ph:ph + nh, pw:pw + nw]
    return cv2.resize(m, (w, h))


def isnet_animatic(rgb, lines, model):
    """Animatic: character cut out by isnet-anime in full dark line; set in a few long, light strokes."""
    char = character_matte(rgb, model)
    char = (char > 0.3).astype(np.uint8)
    # round pink shapes join the matte (the model only knows characters): pink, large and round
    hsv = cv2.cvtColor(rgb, cv2.COLOR_BGR2HSV)
    pink = pink_mask(hsv).astype(np.uint8)
    pink = cv2.morphologyEx(pink, cv2.MORPH_CLOSE, np.ones((31, 31), np.uint8))
    cs, _ = cv2.findContours(pink, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    for c in cs:
        area, per = cv2.contourArea(c), cv2.arcLength(c, True)
        if area > 4000 and 4 * np.pi * area / (per * per + 1e-6) > 0.5:
            cv2.drawContours(char, [cv2.convexHull(c)], -1, 1, -1)
    char = cv2.GaussianBlur(char.astype(np.float32), (0, 0), 1.2)
    tr = np.clip((1.0 - lines.astype(np.float32) / 255.0) * 2.6, 0, 1)
    lb = cv2.dilate((tr > 0.45).astype(np.uint8), np.ones((2, 2), np.uint8))
    inside = cv2.GaussianBlur(lb.astype(np.float32), (0, 0), 0.7) * char
    # outer contour of the character, always closed
    cs, _ = cv2.findContours((char > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    edge = np.zeros(char.shape, np.uint8)
    for c in cs:
        if cv2.contourArea(c) > 400:
            cv2.polylines(edge, [c], True, 1, 2, cv2.LINE_AA)
    bg = (lb * (char < 0.3)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(bg, connectivity=8)
    long_lines = np.zeros_like(bg)
    for i in range(1, n):
        w, h, area = st[i, cv2.CC_STAT_WIDTH], st[i, cv2.CC_STAT_HEIGHT], st[i, cv2.CC_STAT_AREA]
        if max(w, h) >= 110 and area / float(w * h) < 0.12:
            long_lines[lab == i] = 1
    set_ink = cv2.GaussianBlur(long_lines.astype(np.float32), (0, 0), 0.8) * 0.35
    ink = np.maximum(np.maximum(inside, edge.astype(np.float32) * 0.95), set_ink)
    paper = np.array([243, 244, 245], np.float32)
    graphite = np.array([38, 38, 42], np.float32)
    out = paper[None, None] * (1 - ink[..., None]) + graphite[None, None] * ink[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("film")
    ap.add_argument("depth", help="depth-map video synced to the film")
    ap.add_argument("output")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--dur", type=float, default=30.0)
    ap.add_argument("--test", default="", help="comma-separated seconds: write only PNG tests (rough style)")
    ap.add_argument("--lines", default="", help="ready line video (sketch_lines.py --raw), synced with --start")
    ap.add_argument("--fps", type=int, default=12, help="drawings per second (8 = on threes, 12 = on twos)")
    ap.add_argument("--style", default="rough", choices=["rough", "test", "animatic", "isnet"],
                    help="rough = loose sketch; test = pencil test with toned set; animatic = line only, simple set; "
                         "isnet = line only with an isnet-anime character matte")
    ap.add_argument("--model", default="", help="path to isnetis.onnx (only for --style isnet)")
    a = ap.parse_args()
    if a.style == "isnet" and not (a.model and os.path.isfile(a.model)):
        print(ISNET_HELP)
        sys.exit(2)
    if a.style != "rough" and not a.test and not a.lines:
        print(f"--style {a.style} needs --lines (a line video made with sketch_lines.py --raw)")
        sys.exit(2)
    if cv2 is None:
        print("Missing Python packages. Install with: pip install numpy opencv-python")
        sys.exit(2)
    rg = np.random.default_rng(3)
    paper_grain = cv2.GaussianBlur(rg.random((H, W)).astype(np.float32), (0, 0), 0.8)
    if a.test:
        for t in [float(x) for x in a.test.split(",")]:
            rgb = read(a.film, t, 0.1)[0]
            dep = read(a.depth, t, 0.1, gray=True)[0]
            img = rough(rgb, dep, np.random.default_rng(int(t * 100)), paper_grain)
            cv2.imwrite(f"{os.path.splitext(a.output)[0]}_test_{t:.1f}s.png", img)
        print("OK tests")
        return
    rgbs, deps = read(a.film, a.start, a.dur, fps=a.fps), read(a.depth, a.start, a.dur, fps=a.fps, gray=True)
    lns = read(a.lines, 0.0, a.dur, fps=a.fps, gray=True) if a.lines else [None] * len(rgbs)
    n = min(len(rgbs), len(deps), len(lns))
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                             "-r", str(a.fps), "-i", "-", "-vf", "scale=1920:1080:flags=lanczos,fps=24",
                             "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", a.output], stdin=subprocess.PIPE)
    for i in range(n):
        if a.style == "isnet":
            frame = isnet_animatic(rgbs[i], lns[i], a.model)
        elif a.style == "animatic":
            frame = line_animatic(rgbs[i], deps[i], lns[i])
        elif a.style == "test":
            frame = pencil_test(rgbs[i], deps[i], paper_grain, lns[i])
        else:
            frame = rough(rgbs[i], deps[i], np.random.default_rng(1000 + i), paper_grain, lns[i])
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait()
    print(f"OK {a.output}: {n} drawings at {a.fps} per second, output 24 fps")


if __name__ == "__main__":
    main()
