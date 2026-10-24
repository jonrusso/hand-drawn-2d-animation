#!/usr/bin/env python3
"""Composite RGBA layers with explicit exposure per layer under a continuous camera.

Usage:
  python3 compose_layers.py scene.json output.mp4

scene.json (paths relative to the scene file; see assets/templates/layers.example.json):
  width, height, fps, frames   output size, rate and length
  layers                       bottom to top; each has "file" (still) or "sequence" ("pose/{index:04d}.png"),
                               "exposure" (frames each drawing holds: 1 = on ones, 2 = on twos),
                               "depth" (parallax factor of the camera move), optional "x", "y" offsets
  camera                       {"from": [x, y], "to": [x, y]} linear move sampled on every output frame
  audio                        optional audio file, padded or trimmed to the picture
  clear_color                  canvas color under the first layer (default "#000000")

The first layer is the background plate and must overscan every camera position: gaps are never filled
silently. All sequence files are checked before encoding; the output is written to a .partial file and
renamed only on success, next to a .exposure.json report. Requires Pillow and ffmpeg.
"""
import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image


def compose(spec_path, output):
    spec_path = Path(spec_path).resolve()
    root = spec_path.parent
    s = json.loads(spec_path.read_text())
    out = Path(output).resolve()
    if out.exists():
        raise ValueError("Output exists; choose a new version")
    w, h, fps, total = (int(s[k]) for k in ("width", "height", "fps", "frames"))
    if min(w, h, fps, total) <= 0:
        raise ValueError("Positive dimensions, fps and frames required")
    if not s["layers"]:
        raise ValueError("No layers")
    audio = None if not s.get("audio") else root / s["audio"]
    if audio and not audio.is_file():
        raise ValueError("Missing audio")
    # Preflight all sequence files before starting the encoder.
    for layer in s["layers"]:
        exposure = layer.get("exposure", 1)
        if not isinstance(exposure, int) or exposure < 1:
            raise ValueError("Exposure must be a positive integer")
        if "file" in layer:
            paths = [root / layer["file"]]
        else:
            paths = [root / layer["sequence"].format(index=i) for i in range((total + exposure - 1) // exposure)]
        for path in paths:
            if not path.is_file():
                raise FileNotFoundError(path)
        layer["_paths"] = paths
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = out.with_name(out.stem + ".partial" + out.suffix)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "pipe:0"]
    if audio:
        cmd += ["-i", str(audio), "-map", "0:v:0", "-map", "1:a:0", "-af", f"apad,atrim=duration={total / fps}",
                "-c:a", "aac", "-b:a", "256k"]
    cmd += ["-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-t", str(total / fps), "-movflags", "+faststart", str(temp)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    cache = {}
    cam = s.get("camera", {})
    start = cam.get("from", [0, 0])
    end = cam.get("to", start)
    try:
        for f in range(total):
            t = f / max(1, total - 1)
            cx = start[0] + t * (end[0] - start[0])
            cy = start[1] + t * (end[1] - start[1])
            canvas = Image.new("RGBA", (w, h), s.get("clear_color", "#000000"))
            for n, layer in enumerate(s["layers"]):
                idx = 0 if "file" in layer else f // layer.get("exposure", 1)
                path = layer["_paths"][idx]
                if n not in cache or cache[n][0] != idx:
                    with Image.open(path) as im:
                        cache[n] = (idx, im.convert("RGBA"))
                im = cache[n][1]
                depth = layer.get("depth", 1)
                x = layer.get("x", 0) - cx * depth
                y = layer.get("y", 0) - cy * depth
                # Full backgrounds must overscan every camera position; never fill gaps silently.
                if n == 0 and (x > 0 or y > 0 or x + im.width < w or y + im.height < h):
                    raise ValueError(f"Background overscan insufficient at frame {f}")
                shifted = im.transform((w, h), Image.Transform.AFFINE, (1, 0, -x, 0, 1, -y), resample=Image.Resampling.BICUBIC)
                canvas = Image.alpha_composite(canvas, shifted)
            proc.stdin.write(canvas.convert("RGB").tobytes())
        proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError("Encoder failed")
        temp.replace(out)
    except Exception:
        if not proc.stdin.closed:
            proc.stdin.close()
        proc.terminate()
        proc.wait()
        temp.unlink(missing_ok=True)
        raise
    report = {"fps": fps, "frames": total,
              "layers": [{k: v for k, v in layer.items() if not k.startswith("_")} for layer in s["layers"]],
              "camera_sampled_every_output_frame": True, "optical_flow": False}
    out.with_suffix(".exposure.json").write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("scene")
    p.add_argument("output")
    a = p.parse_args()
    compose(a.scene, a.output)
