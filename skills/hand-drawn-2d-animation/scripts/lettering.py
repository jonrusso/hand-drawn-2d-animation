#!/usr/bin/env python3
"""Animated lettering for vertical reels (ProRes 4444 with alpha), with measured motion curves.

Usage:
  python3 lettering.py config.json output.mov [--font path/to/font.ttf]

Motion language (per element, "anim"):
- "pop": scale on a value curve (back.out): 0.72 -> overshoots 1.0 -> settles at 1.0 in 8 frames; opacity in 3 frames.
  Only for a small highlight object (keyword, badge).
- "rise": enters 3 frames before its marked time; rises 28 px with expo.out over 7 frames, with a blur-in (8 px -> 0).
- "type": letter by letter (each letter with a 3-frame fade), duration in "type_dur".
- "cut": appears hard.
- glow: reacts 2 frames after the landing: peaks at 1.8x and settles in 8 frames.
- "breathe": true -> once settled, scale 1 -> 1.018 -> 1 over a cycle of "period" s (nothing dead for more than 2 s).
- "glow_strength": multiplies the glow intensity (gradient text wants little glow so it does not smear).
- "exit" (s): leaves with expo.in over 6 frames: fades, rises 18 px and blurs (the inverse of "rise").
  Stagger exits bottom to top, 2 frames apart, so the end does not drop flat.

Card-level options:
- "video": an animated drawing inside the card (8 drawings per second); the drawing's paper becomes the card's paper.
  "crop": [x, y, w, h] in the 16:9 source to get closer to the character; "exit" and "exit_dur" (s): the drawing's
  line fades into the paper at the end (the page ends clean). Other keys: "file", "start", "t", "w", "x", "y", "fps", "tint".
- "fade_in" (s): the whole card dissolves in over what is below, instead of a cut.
- "background_only": true -> render only the card and the drawing, no text (the text stays editable in the NLE;
  text on the timeline should always be editable, never baked into an image).
- "bg_color", "bg_alpha", "bg_fade_in": card color, dark veil opacity and its fade-in time.
Position: "y" is the text center in px; "block_center" re-centers the whole block (video + texts) at that height.
Style rule: no box and no pill behind text; glow or shadow, never a frame.
Font: per element "font", else the config "font", else --font, else a common system font, else Pillow's default.
Requires Pillow and ffmpeg.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

FONT_CANDIDATES = [
    "DejaVuSans-Bold.ttf",
    "DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "C:/Windows/Fonts/arialbd.ttf",
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


def color(hexa, a=255):
    hexa = hexa.lstrip("#")
    return tuple(int(hexa[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def back_out(t, s=1.9):
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


def expo_out(t):
    return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)


def text_base(e, W, H):
    """Text layer (with shadow) and glow layer kept apart, so the glow can react after the text."""
    font = load_font(e.get("font"), e["size"])
    txt = e["text"].upper() if e.get("uppercase") else e["text"]
    e["_font"], e["_txt"] = font, txt
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if e.get("shadow"):
        s = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(s).text((W / 2, e["y"]), txt, font=font, fill=(0, 0, 0, 255), anchor="mm",
                               stroke_width=max(4, e["size"] // 12), stroke_fill=(0, 0, 0, 255))
        s = s.filter(ImageFilter.GaussianBlur(e["size"] / 8))
        s.putalpha(s.getchannel("A").point(lambda a: int(a * 0.8)))
        img = Image.alpha_composite(img, s)
    if e.get("gradient"):
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).text((W / 2, e["y"]), txt, font=font, fill=255, anchor="mm")
        x0, y0, x1, y1 = m.getbbox()
        a, b = color(e["gradient"][0]), color(e["gradient"][1])
        grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(grad)
        for yy in range(y0, y1 + 1):
            f = (yy - y0) / max(1, y1 - y0)
            gd.line([(0, yy), (W, yy)], fill=tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3)) + (255,))
        grad.putalpha(m)
        img = Image.alpha_composite(img, grad)
    else:
        ImageDraw.Draw(img).text((W / 2, e["y"]), txt, font=font, fill=color(e["color"]), anchor="mm")
    glow = None
    if e.get("glow"):
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((W / 2, e["y"]), txt, font=font, fill=color(e.get("glow_color", e.get("color", "#FFFFFF"))), anchor="mm")
        glow = g.filter(ImageFilter.GaussianBlur(e["glow"]))
    return img, glow


def with_alpha(im, f):
    if f >= 1:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda a: int(a * max(0.0, f))))
    return im


def scaled(im, sc, cy, W, H):
    if abs(sc - 1) < 1e-4:
        return im
    nw, nh = round(W * sc), round(H * sc)
    r = im.resize((nw, nh), Image.LANCZOS)
    ox, oy = round((nw - W) / 2), round(cy * sc - cy)
    if sc >= 1:
        return r.crop((ox, oy, ox + W, oy + H))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(r, (-ox, -oy))
    return out


def typed(e, k, fps, W, H):
    n = len(e["_txt"])
    step = e.get("type_dur", 0.6) * fps / max(1, n)
    if k > n * step + 3:
        return e["_img"]
    font, txt = e["_font"], e["_txt"]
    x0 = W / 2 - font.getlength(txt) / 2
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    for i in range(n):
        a = (k - i * step) / 3
        if a <= 0:
            break
        d.rectangle([x0 + font.getlength(txt[:i]) - 1, 0, x0 + font.getlength(txt[:i + 1]) + 1, H], fill=int(255 * min(1, a)))
    im = e["_img"].copy()
    im.putalpha(ImageChops.darker(im.getchannel("A"), m))
    return im


def element(e, q, fps, W, H):
    anim = e.get("anim", "pop")
    q0 = e["_q0"] - (3 if anim == "rise" else 0)  # lettering enters 3 frames before its marked time
    k = q - q0
    if k < 0:
        return []
    if anim == "cut":
        im = e["_img"]
    elif anim == "type":
        im = typed(e, k, fps, W, H)
    elif anim == "rise":
        p = expo_out(min(1.0, (k + 1) / 7))
        im = with_alpha(e["_img"], min(1.0, (k + 1) / 4))
        if 8 * (1 - p) > 0.4:
            im = im.filter(ImageFilter.GaussianBlur(8 * (1 - p)))
        dy = round(28 * (1 - p))
        if dy:
            out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            out.paste(im, (0, dy))
            im = out
    else:  # pop
        sc = 0.72 + 0.28 * back_out(min(1.0, (k + 1) / 8))
        im = scaled(with_alpha(e["_img"], min(1.0, (k + 1) / 3)), sc, e["y"], W, H)
    layers = [im]
    if e.get("_glow") is not None:
        landing = 8 if anim == "pop" else 4
        kg = k - landing - 2  # glow reacts 2 frames after the landing
        fg = min(1.0, (k + 1) / (landing + 2)) * 0.6 if kg < 0 else 1.0 + 0.8 * max(0.0, 1 - kg / 8)
        if e.get("breathe") and kg > 8:
            fg = 1.0 + 0.25 * (0.5 - 0.5 * math.cos(2 * math.pi * (kg - 8) / (e.get("period", 1.6) * fps)))
        fg *= e.get("glow_strength", 1.0)
        layers.insert(0, with_alpha(e["_glow"], min(1.0, fg)))
        if fg > 1:
            layers.insert(0, with_alpha(e["_glow"], fg - 1))
    if e.get("breathe"):
        settle = (8 if anim == "pop" else 7) + 10
        if k > settle:
            sc = 1 + 0.018 * (0.5 - 0.5 * math.cos(2 * math.pi * (k - settle) / (e.get("period", 1.6) * fps)))
            layers = [scaled(c, sc, e["y"], W, H) for c in layers]
    if e.get("exit") is not None and q >= round(e["exit"] * fps):
        p = min(1.0, (q - round(e["exit"] * fps) + 1) / 6) ** 2.2  # approximate expo.in: starts slow, leaves fast
        dy = -round(18 * p)
        leaving = []
        for c in layers:
            c = with_alpha(c, 1 - p)
            if p > 0.05:
                c = c.filter(ImageFilter.GaussianBlur(6 * p))
            if dy:
                out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                out.paste(c, (0, dy))
                c = out
            leaving.append(c)
        layers = leaving
    return layers


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("output")
    ap.add_argument("--font", default=None, help="default TTF/OTF font for elements without their own 'font'")
    a = ap.parse_args()
    with open(a.config, encoding="utf-8") as fh:
        cfg = json.load(fh)
    W, H, fps = cfg["w"], cfg["h"], cfg["fps"]
    total = round(cfg["dur"] * fps)
    vid = cfg.get("video")
    if cfg.get("block_center"):
        tops = [e["y"] - e["size"] * 0.6 for e in cfg["elements"]]
        bottoms = [e["y"] + e["size"] * 0.6 for e in cfg["elements"]]
        if vid:
            tops.append(vid["y"])
            bottoms.append(vid["y"] + round(vid["w"] * 9 / 16))
        shift = round(cfg["block_center"] - (min(tops) + max(bottoms)) / 2)
        for e in cfg["elements"]:
            e["y"] += shift
        if vid:
            vid["y"] += shift
    for e in cfg["elements"]:
        e.setdefault("font", cfg.get("font") or a.font)
        e["_q0"] = round(e["t"] * fps)
        e["_img"], e["_glow"] = text_base(e, W, H)
    drawings = []
    if vid:
        vw = vid["w"]
        vh = round(vw * 9 / 16)
        crop = "crop={}:{}:{}:{},".format(*vid["crop"][2:], *vid["crop"][:2]) if vid.get("crop") else ""
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(vid["start"]), "-t", str(cfg["dur"]), "-i", vid["file"],
                              "-vf", f"{crop}fps={vid.get('fps', 8)},scale={vw}:{vh},format=gray", "-f", "rawvideo", "-"],
                             capture_output=True, check=True).stdout
        n = vw * vh
        paper = color(cfg.get("bg_color", "#F9FAEC"))
        ink = color(vid.get("tint", "#1A1A1F"))
        for i in range(0, len(raw) - n + 1, n):
            g = Image.frombytes("L", (vw, vh), raw[i:i + n]).point(lambda v: 255 if v >= 228 else max(0, int(255 - (228 - v) * 2.2)))
            drawings.append(Image.composite(Image.new("RGBA", (vw, vh), paper), Image.new("RGBA", (vw, vh), ink), g))
    tmp = tempfile.mkdtemp(prefix="lettering_")
    fa, fe = cfg.get("bg_alpha", 0), round(cfg.get("bg_fade_in", 0.25) * fps)
    for q in range(total):
        frame = Image.new("RGBA", (W, H), color(cfg["bg_color"]) if cfg.get("bg_color") else (0, 0, 0, 0))
        if fa:
            frame = Image.alpha_composite(frame, Image.new("RGBA", (W, H), (8, 8, 10, int(255 * fa * min(1.0, (q + 1) / max(1, fe))))))
        if drawings and q >= round(vid.get("t", 0) * fps):
            k = min(len(drawings) - 1, int((q - round(vid.get("t", 0) * fps)) * vid.get("fps", 8) / fps))
            d = drawings[k]
            if vid.get("exit") is not None and q >= round(vid["exit"] * fps):
                d = with_alpha(d, max(0.0, 1 - (q - round(vid["exit"] * fps) + 1) / max(1, round(vid.get("exit_dur", 0.4) * fps))))
            frame.alpha_composite(d, ((W - vid["w"]) // 2 if vid.get("x") is None else vid["x"], vid["y"]))
        for e in [] if cfg.get("background_only") else cfg["elements"]:
            for c in element(e, q, fps, W, H):
                frame = Image.alpha_composite(frame, c)
        if cfg.get("fade_in") and q < round(cfg["fade_in"] * fps):
            frame = with_alpha(frame, (q + 1) / round(cfg["fade_in"] * fps))
        frame.save(os.path.join(tmp, f"l_{q:04d}.png"))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-i", os.path.join(tmp, "l_%04d.png"),
                    "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", a.output], check=True)
    shutil.rmtree(tmp)
    print(f"OK {a.output}: {total} frames")


if __name__ == "__main__":
    main()
