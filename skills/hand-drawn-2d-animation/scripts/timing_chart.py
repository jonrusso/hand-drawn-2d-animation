#!/usr/bin/env python3
"""Render an animation timing layer (frame ruler, keys, breakdowns, exposure and cursor) with transparency.

Usage:
  python3 timing_chart.py config.json output.mov [--font path/to/font.ttf]

config.json:
  w, h, fps            frame size and rate (e.g. 1080, 1920, 24)
  total                number of frames in the passage (e.g. 96)
  drawings             [[start_frame, pose_number], ...] in exposure order; pose 0 = no drawing
  keys                 list of pose numbers that are keys (the rest are breakdowns/inbetweens)
  names                {"pose_number": "short nickname"} optional, shown next to the counter
  ruler                {"x0", "x1", "y"} ruler position in px
  stamp                {"x", "y"} corner where the drawing number goes (as an animator notes it on paper)
  font                 path to a TTF/OTF font (optional; --font overrides; falls back to a common system font)

Output: ProRes 4444 with alpha, one image per frame of the passage, for its own track in the NLE.
The line wobbles slightly (fixed seed) so it looks hand drawn. Requires Pillow and ffmpeg.

"column" mode (vertical exposure sheet next to a character sheet that swaps poses):
  mode                 "column"
  column               {"x", "y0", "y1"} vertical ruler in px; keys on the left, breakdowns on the right
  hold                 frames each pose stays on screen (e.g. 10); the lit pose and the cursor follow it
  duration_frames      duration of the layer (e.g. 120)
  ink, accent          [r, g, b] colors (default graphite and red pencil, for light paper)
No words in the image: only numbers and the chart's own marks. Key names go in a separate subtitle (SRT).
"""
import argparse
import json
import os
import random
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFilter, ImageFont

INK = (237, 230, 214, 255)
INK_FAINT = (237, 230, 214, 150)
ACCENT = (255, 206, 92, 255)

FONT_CANDIDATES = [
    "DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "C:/Windows/Fonts/arial.ttf",
]


def load_font(path, size):
    """Font from `path`; without one, the first common system font found; last resort, Pillow's default font."""
    if path:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            raise SystemExit(f"cannot open font {path}")
    for f in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def line(d, a, b, color, width, rnd, wobble=1.2):
    """Pencil line: two slightly offset passes."""
    for _ in range(2):
        j = [rnd.uniform(-wobble, wobble) for _ in range(4)]
        d.line([(a[0] + j[0], a[1] + j[1]), (b[0] + j[2], b[1] + j[3])], fill=color, width=width)


def circle(d, c, r, color, width, rnd):
    for _ in range(2):
        e = rnd.uniform(-1.5, 1.5)
        d.ellipse([c[0] - r + e, c[1] - r - e, c[0] + r - e, c[1] + r + e], outline=color, width=width)


def expo_out(t):
    return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)


def encode(tmp, pattern, fps, output):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-i", os.path.join(tmp, pattern),
                    "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", output], check=True)


def column(cfg, output):
    """Vertical exposure sheet: ruler of the animation's real time; the pose on screen lights up and the cursor slides to it."""
    W, H, total = cfg["w"], cfg["h"], cfg["total"]
    x, y0, y1 = cfg["column"]["x"], cfg["column"]["y0"], cfg["column"]["y1"]
    step = (y1 - y0) / total
    ink = tuple(cfg.get("ink", [42, 42, 46])) + (255,)
    faint = ink[:3] + (110,)
    accent = tuple(cfg.get("accent", [214, 64, 44])) + (255,)
    small = load_font(cfg.get("font"), 22)
    drawings = [(q, p) for q, p in cfg["drawings"] if p]
    keys = set(cfg["keys"])
    start = {}
    for q, p in drawings:
        start.setdefault(p, q)
    poses = sorted(start)
    ends = {p: next((start[o] for o in poses if start[o] > start[p]), total) for p in poses}
    hold, n = cfg["hold"], cfg["duration_frames"]
    tmp = tempfile.mkdtemp(prefix="column_")
    for f in range(n):
        rnd = random.Random(7)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        k = min(len(poses) - 1, f // hold)
        current = poses[k]
        line(d, (x, y0), (x, y1), ink, 3, rnd)
        for q in range(0, total + 1, 2):
            width = 14 if q % 12 == 0 else 7
            line(d, (x - width, y0 + q * step), (x + width, y0 + q * step), faint, 2, rnd, 0.5)
        for p in poses:
            cy = y0 + start[p] * step
            color = accent if p == current else ink
            if p in keys:
                circle(d, (x - 50, cy), 17, color, 3, rnd)
                d.text((x - 50, cy), str(p), font=small, fill=color, anchor="mm")
                line(d, (x - 33, cy), (x, cy), color, 3, rnd)
            else:
                line(d, (x, cy), (x + 26, cy), color, 3, rnd)
                d.text((x + 44, cy), str(p), font=small, fill=color, anchor="mm")
            if p == current:  # exposure of the lit drawing: pencil bracket from first to last frame
                yf = y0 + ends[p] * step
                line(d, (x + 64, cy), (x + 64, yf), accent, 3, rnd, 0.4)
                line(d, (x + 58, cy), (x + 70, cy), accent, 3, rnd, 0.4)
                line(d, (x + 58, yf), (x + 70, yf), accent, 3, rnd, 0.4)
                d.text((x + 88, (cy + yf) / 2), f"x{ends[p] - start[p]}", font=small, fill=accent, anchor="lm")
        # the cursor slides to the new pose's frame with expo.out over 4 frames
        previous = start[poses[k - 1]] if k else 0
        p_ = expo_out(min(1.0, (f - k * hold + 1) / 4)) if k else 1.0
        cy = y0 + (previous + (start[current] - previous) * p_) * step
        line(d, (x - 80, cy), (x + 30, cy), accent, 2, rnd, 0.3)
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        shadow.putalpha(img.getchannel("A").filter(ImageFilter.GaussianBlur(4)).point(lambda a: int(a * 0.18)))
        img = Image.alpha_composite(shadow, img)
        img.save(os.path.join(tmp, f"c_{f:04d}.png"))
    encode(tmp, "c_%04d.png", cfg["fps"], output)
    shutil.rmtree(tmp)
    print(f"OK {output}: {n} frames with alpha (column)")


def ruler(cfg, output):
    W, H, total = cfg["w"], cfg["h"], cfg["total"]
    x0, x1, y = cfg["ruler"]["x0"], cfg["ruler"]["x1"], cfg["ruler"]["y"]
    step = (x1 - x0) / total
    font = load_font(cfg.get("font"), 30)
    small = load_font(cfg.get("font"), 22)
    big = load_font(cfg.get("font"), 40)
    drawings = cfg["drawings"]
    keys = set(cfg["keys"])
    names = {int(k): v for k, v in cfg.get("names", {}).items()}
    starts = [q for q, _ in drawings] + [total]
    tmp = tempfile.mkdtemp(prefix="timing_")
    for f in range(total):
        rnd = random.Random(7)  # same wobble on every frame: the drawing does not boil
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.text((x0, y - 118), f"TIMING  ·  {cfg['fps']} fps", font=small, fill=INK_FAINT)
        d.text((x1, y - 118), f"F {f + 1:03d} / {total:03d}", font=font, fill=INK, anchor="ra")
        line(d, (x0, y), (x1, y), INK, 3, rnd)
        for q in range(0, total + 1, 2):
            tall = 18 if q % 12 == 0 else 9
            line(d, (x0 + q * step, y - tall), (x0 + q * step, y + tall), INK_FAINT, 2, rnd, 0.6)
        current = max(i for i, q in enumerate(starts[:-1]) if q <= f)
        for i, (q, pose) in enumerate(drawings):
            if pose == 0:
                continue
            if i > 0 and drawings[i - 1][1] == pose:
                continue  # continued hold of the same drawing
            end = next((starts[k] for k in range(i + 1, len(drawings)) if drawings[k][1] != pose), total)
            cx = x0 + q * step
            color = ACCENT if i <= current and (current == i or drawings[current][1] == pose) else INK
            if pose in keys:
                circle(d, (cx, y - 52), 22, color, 3, rnd)
                d.text((cx, y - 52), str(pose), font=small, fill=color, anchor="mm")
                line(d, (cx, y - 30), (cx, y), color, 3, rnd)
            else:
                line(d, (cx, y), (cx, y + 34), color, 3, rnd)
                d.text((cx, y + 52), str(pose), font=small, fill=color, anchor="mm")
            d.text(((cx + x0 + end * step) / 2, y + 92), f"x{end - q}", font=small, fill=INK_FAINT, anchor="mm")
        px = x0 + (f + 0.5) * step
        line(d, (px, y - 86), (px, y + 70), ACCENT, 3, rnd, 0.4)
        pose = drawings[current][1]
        if pose:
            kind = "KEY" if pose in keys else "BREAKDOWN"
            label = f"{kind} {pose:02d}" + (f"  ·  {names[pose]}" if pose in names else "")
            d.text((x0, y + 138), label, font=font, fill=ACCENT if pose in keys else INK, anchor="lm")
            cx, cy = cfg["stamp"]["x"], cfg["stamp"]["y"]
            text = f"A{pose:02d}"
            if pose in keys:
                circle(d, (cx, cy), 46, ACCENT, 4, rnd)
                d.text((cx, cy), text, font=big, fill=ACCENT, anchor="mm")
            else:
                d.text((cx, cy), text, font=big, fill=INK, anchor="mm")
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        shadow.putalpha(img.getchannel("A").filter(ImageFilter.GaussianBlur(5)).point(lambda a: min(255, int(a * 1.6))))
        img = Image.alpha_composite(shadow, img)  # soft shadow: ruler readable over the picture, no box
        img.save(os.path.join(tmp, f"t_{f:04d}.png"))
    encode(tmp, "t_%04d.png", cfg["fps"], output)
    shutil.rmtree(tmp)
    print(f"OK {output}: {total} frames with alpha")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("output")
    ap.add_argument("--font", default=None, help="TTF/OTF font path (overrides 'font' in the config)")
    a = ap.parse_args()
    with open(a.config, encoding="utf-8") as fh:
        cfg = json.load(fh)
    if a.font:
        cfg["font"] = a.font
    if cfg.get("mode") == "column":
        return column(cfg, a.output)
    return ruler(cfg, a.output)


if __name__ == "__main__":
    main()
