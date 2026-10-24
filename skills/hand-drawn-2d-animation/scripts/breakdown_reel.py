#!/usr/bin/env python3
"""Build a 9:16 breakdown reel of stacked bands from a JSON config, and write an editable timeline XML plus a preview.

Usage:
  python3 breakdown_reel.py config.json [--font path/to/font.ttf]

The timeline is FCP7 XML (xmeml), which imports in Premiere and other NLEs.

Layout per section ("type"):
- "bands": 1 to 3 synced 16:9 videos stacked vertically, each with a label in the lower left corner.
- "full": one video full screen 9:16 (a crop of the 16:9), with an adjustable horizontal offset.

Every video, image and label goes on its own video track with Basic Motion (scale and position),
so the editor can adjust it by hand. Labels are transparent PNGs the size of the frame. The background is a solid PNG.
The reference music only goes in as a marker; the guide audio (if any) goes on A1.

config.json:
  name, output_dir, w, h          sequence name, output folder, frame size (e.g. 1080 x 1920)
  font, label_size                label font (optional; falls back to a common system font) and size (34)
  background                      background color ("#141414")
  gap, margin_x, safe_bottom      px between bands (16), label left margin (120), bottom safe line (1580)
  sections                        [{"type": "bands", "start", "dur", "bands": [{"file", "in", "label", "label_pos"}]},
                                   {"type": "full", "start", "dur", "file", "in", "offset_x", "label"}]
                                  "file" may be a list of files played back to back (a film in parts)
  overlays                        [{"file", "start", "dur", "in"}] full-frame alpha layers (timing charts, arrows)
  audio                           [{"file", "start", "dur", "in", "volume"}]
  markers                         [{"name", "comment", "t"}]
Requires ffmpeg, ffprobe and Pillow.
"""
import argparse
import json
import os
import subprocess
import urllib.parse

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FPS = 24
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


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,duration:format=duration", "-of", "default=nw=1", path],
                         capture_output=True, text=True).stdout
    vals = [line.split("=", 1) for line in out.strip().splitlines() if "=" in line]
    d = dict(vals)
    durations = [float(v) for k, v in vals if k == "duration" and v != "N/A"]
    # the video stream can end before the container (e.g. video 15.042 s, file 15.093 s); the shorter one avoids a black frame at the join
    dur = min(durations) if durations else None
    return int(d.get("width", 0)), int(d.get("height", 0)), dur  # pure audio has no width or height


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def fr(t):
    return int(round(t * FPS))


def file_url(f):
    return "file://" + urllib.parse.quote(os.path.abspath(f))


class Source:
    """A source is one file or a sequence of files (a film in parts); returns pieces (file, in, dur, w, h)."""

    def __init__(self, spec):
        self.parts = []
        files = spec if isinstance(spec, list) else [spec]
        t = 0.0
        for f in files:
            w, h, dur = probe(f)
            self.parts.append((f, t, dur, w, h))
            t += dur or 0
        # ffprobe reports 0.04 s for a JPEG: images are decided by extension, not by duration
        self.image = self.parts[0][0].lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"))

    def pieces(self, start, dur):
        if self.image:
            f, _, _, w, h = self.parts[0]
            return [(f, 0.0, dur, w, h)]
        res, end = [], start + dur
        for f, t0, d, w, h in self.parts:
            a, b = max(start, t0), min(end, t0 + d)
            if b - a > 1 / FPS / 2:
                res.append((f, a - t0, b - a, w, h))
        return res


def label_png(cfg, text, x, y, dest):
    W, H = cfg["w"], cfg["h"]
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    font = load_font(cfg.get("font"), cfg.get("label_size", 34))
    # soft shadow behind the text (no box): readable over light backgrounds such as animatic paper
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text((x, y), text, font=font, fill=(0, 0, 0, 255), stroke_width=6, stroke_fill=(0, 0, 0, 255))
    shadow = shadow.filter(ImageFilter.GaussianBlur(9))
    shadow.putalpha(shadow.getchannel("A").point(lambda a: min(255, int(a * 0.85))))
    img = Image.alpha_composite(img, shadow)
    ImageDraw.Draw(img).text((x, y), text, font=font, fill=(255, 255, 255, 255))
    img.save(dest)


def layout(cfg, n):
    """Vertical centers (in frame px) and height of the stacked 16:9 bands."""
    W, H, gap = cfg["w"], cfg["h"], cfg.get("gap", 16)
    height = W * 9 / 16
    total = n * height + (n - 1) * gap
    top = (H - total) / 2
    return [top + height / 2 + i * (height + gap) for i in range(n)], height


def build(cfg):
    for s in cfg["sections"] + cfg.get("overlays", []) + cfg.get("audio", []):
        # everything on the frame grid: end of one section = start of the next, no 1-2 frame hole in the preview
        end = fr(s["start"] + s["dur"])
        s["start"] = fr(s["start"]) / FPS
        s["dur"] = (end - fr(s["start"])) / FPS
    out = cfg["output_dir"]
    os.makedirs(os.path.join(out, "labels"), exist_ok=True)
    W, H = cfg["w"], cfg["h"]
    background = os.path.join(out, "labels", "background.png")
    Image.new("RGB", (W, H), cfg.get("background", "#141414")).save(background)
    tracks = {}  # name -> list of items (file, seq_start, src_in, dur, scale, dx, dy, w, h)
    duration = max(s["start"] + s["dur"] for s in cfg["sections"])
    tracks["V1 background"] = [(background, 0.0, 0.0, duration, 100.0, 0.0, 0.0, W, H)]
    for k, s in enumerate(cfg["sections"], 1):
        if s["type"] == "bands":
            centers, height = layout(cfg, len(s["bands"]))
            for j, (band, cy) in enumerate(zip(s["bands"], centers), 1):
                source = Source(band["file"])
                t = s["start"]
                for f, a, d, w, h in source.pieces(band.get("in", 0.0), s["dur"]):
                    scale = min(W / w, height / h) * 100
                    tracks.setdefault(f"V{j + 1} band {j}", []).append((f, t, a, d, scale, 0.0, cy - H / 2, w, h))
                    t += d
                if band.get("label"):
                    png = os.path.join(out, "labels", f"s{k:02d}_b{j}.png")
                    # Reels safe area: caption and profile cover the bottom from ~1580 px (of 1920)
                    y_base = int(cy + height / 2 - 60)
                    y_label = y_base if (band.get("label_pos") != "top" and y_base + 44 <= cfg.get("safe_bottom", 1580)) else int(cy - height / 2 + 22)
                    label_png(cfg, band["label"], cfg.get("margin_x", 120), y_label, png)  # tall Reels crop ~97 px per side
                    tracks.setdefault("V8 labels", []).append((png, s["start"], 0.0, s["dur"], 100.0, 0.0, 0.0, W, H))
        else:
            source = Source(s["file"])
            t = s["start"]
            for f, a, d, w, h in source.pieces(s.get("in", 0.0), s["dur"]):
                scale = H / h * 100
                dx = s.get("offset_x", 0.0) * scale / 100
                tracks.setdefault("V5 full", []).append((f, t, a, d, scale, dx, 0.0, w, h))
                t += d
            if s.get("label"):
                png = os.path.join(out, "labels", f"s{k:02d}_full.png")
                label_png(cfg, s["label"], cfg.get("margin_x", 120), H - 140, png)
                tracks.setdefault("V8 labels", []).append((png, s["start"], 0.0, s["dur"], 100.0, 0.0, 0.0, W, H))
    for o in cfg.get("overlays", []):  # full-frame alpha layers (timing, arrows), no motion
        w, h, _ = probe(o["file"])
        tracks.setdefault("V9 overlays", []).append((o["file"], o["start"], o.get("in", 0.0), o["dur"], 100.0, 0.0, 0.0, w, h))
    xml = write_xml(cfg, tracks, duration)
    xml_path = os.path.join(out, cfg["name"] + ".xml")
    with open(xml_path, "w", encoding="utf-8") as fh:
        fh.write(xml)
    preview = os.path.join(out, cfg["name"] + "_preview.mp4")
    render(cfg, tracks, duration, preview)
    print(f"OK xml: {xml_path}\nOK preview: {preview}\nduration {duration:.2f} s, {sum(len(v) for v in tracks.values())} clips on {len(tracks)} tracks")


def write_xml(cfg, tracks, duration):
    W, H = cfg["w"], cfg["h"]
    rate = f"<rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate>"
    seen, tracks_xml, n = set(), [], 0
    for name in sorted(tracks, key=lambda s: int(s.split()[0][1:])):
        items = []
        for f, start, a, d, scale, dx, dy, w, h in tracks[name]:
            n += 1
            fid = "f-" + str(abs(hash(f)) % 10 ** 10)
            image = f.lower().endswith((".png", ".jpg", ".jpeg"))
            src_dur = fr(d) if image else fr(probe(f)[2])
            fel = (f'<file id="{fid}"><name>{esc(os.path.basename(f))}</name><pathurl>{file_url(f)}</pathurl>'
                   f"{rate}<duration>{src_dur}</duration><media><video><samplecharacteristics>{rate}"
                   f"<width>{w}</width><height>{h}</height></samplecharacteristics></video></media></file>") if fid not in seen else f'<file id="{fid}"/>'
            seen.add(fid)
            start_f, end_f = fr(start), fr(start + d)
            in_f = 0 if image else fr(a)
            motion = (f"<filter><effect><name>Basic Motion</name><effectid>basic</effectid><effectcategory>motion</effectcategory>"
                      f"<effecttype>motion</effecttype><mediatype>video</mediatype>"
                      f"<parameter><parameterid>scale</parameterid><name>Scale</name><valuemin>0</valuemin><valuemax>1000</valuemax><value>{scale:.3f}</value></parameter>"
                      f"<parameter><parameterid>center</parameterid><name>Center</name><value><horiz>{dx / W:.5f}</horiz><vert>{dy / H:.5f}</vert></value></parameter>"
                      f"</effect></filter>")
            items.append(f'<clipitem id="c{n}"><name>{esc(os.path.basename(f))}</name><duration>{src_dur}</duration>{rate}'
                         f"<start>{start_f}</start><end>{end_f}</end><in>{in_f}</in><out>{in_f + end_f - start_f}</out>{fel}{motion}</clipitem>")
        tracks_xml.append(f"<track>{''.join(items)}</track>")
    markers = "".join(f"<marker><name>{esc(m['name'])}</name><comment>{esc(m.get('comment', ''))}</comment>"
                      f"<in>{fr(m['t'])}</in><out>-1</out></marker>" for m in cfg.get("markers", []))
    audio = ""
    for k, a in enumerate(cfg.get("audio", []), 1):
        fid = f"aud-{k}"
        d = a["dur"]
        audio += (f'<track><clipitem id="a{k}"><name>{esc(os.path.basename(a["file"]))}</name>{rate}'
                  f"<start>{fr(a['start'])}</start><end>{fr(a['start'] + d)}</end><in>{fr(a.get('in', 0))}</in><out>{fr(a.get('in', 0) + d)}</out>"
                  f'<file id="{fid}"><name>{esc(os.path.basename(a["file"]))}</name><pathurl>{file_url(a["file"])}</pathurl>{rate}'
                  f"<duration>{fr(probe(a['file'])[2])}</duration><media><audio><channelcount>2</channelcount></audio></media></file>"
                  f"<sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack></clipitem></track>")
    audio += "<track></track>"
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="4"><sequence id="seq1">'
            f"<name>{esc(cfg['name'])}</name><duration>{fr(duration)}</duration>{rate}{markers}"
            f"<media><video><format><samplecharacteristics>{rate}<width>{W}</width><height>{H}</height>"
            f"<pixelaspectratio>square</pixelaspectratio></samplecharacteristics></format>{''.join(tracks_xml)}</video>"
            f"<audio>{audio}</audio></media></sequence></xmeml>\n")


def render(cfg, tracks, duration, output):
    W, H = cfg["w"], cfg["h"]
    inputs, filters, last = [], [], "base"
    filters.append(f"color=c={cfg.get('background', '#141414')}:s={W}x{H}:r={FPS}:d={duration:.3f}[base]")
    idx = 0
    for name in sorted(tracks, key=lambda s: int(s.split()[0][1:])):
        if name.startswith("V1 "):
            continue
        for f, start, a, d, scale, dx, dy, w, h in tracks[name]:
            image = f.lower().endswith((".png", ".jpg", ".jpeg"))
            if image:
                # a looped JPEG fails in overlay; the preview uses an RGBA PNG copy (the XML still points to the original)
                png = f
                if not f.lower().endswith(".png"):  # rebuilt on every render, so a stale version is never reused
                    png = os.path.join(os.path.dirname(output), "labels", "preview_" + os.path.splitext(os.path.basename(f))[0] + ".png")
                    Image.open(f).convert("RGBA").save(png)
                inputs += ["-loop", "1", "-t", f"{d + 2 / FPS:.3f}", "-i", png]  # slack: the overlay's enable cuts at the right frame
            else:
                inputs += ["-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", f]
            sw, sh = round(w * scale / 100 / 2) * 2, round(h * scale / 100 / 2) * 2
            x, y = W / 2 + dx - sw / 2, H / 2 + dy - sh / 2
            filters.append(f"[{idx}:v]fps={FPS},scale={sw}:{sh},format=rgba,setpts=PTS-STARTPTS+{fr(start)}/{FPS}/TB[v{idx}]")
            q0, q1 = fr(start), fr(start + d) - 1  # by frame number: rounded seconds left the first frame out
            filters.append(f"[{last}][v{idx}]overlay=x={x:.1f}:y={y:.1f}:eof_action=pass:enable='between(n,{q0},{q1})'[o{idx}]")
            last = f"o{idx}"
            idx += 1
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs]
    maps = ["-map", f"[{last}]"]
    for a in cfg.get("audio", []):
        cmd += ["-ss", f"{a.get('in', 0):.3f}", "-t", f"{a['dur']:.3f}", "-i", a["file"]]
        filters.append(f"[{idx}:a]adelay={int(a['start'] * 1000)}|{int(a['start'] * 1000)},volume={a.get('volume', 1.0)}[a{idx}]")
        maps += ["-map", f"[a{idx}]"]
        idx += 1
    cmd += ["-filter_complex", ";".join(filters), *maps, "-t", f"{duration:.3f}", "-r", str(FPS),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac", output]
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("--font", default=None, help="TTF/OTF font path for labels (overrides 'font' in the config)")
    a = ap.parse_args()
    with open(a.config, encoding="utf-8") as fh:
        cfg = json.load(fh)
    if a.font:
        cfg["font"] = a.font
    build(cfg)


if __name__ == "__main__":
    main()
