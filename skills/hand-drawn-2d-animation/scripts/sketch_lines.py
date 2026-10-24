#!/usr/bin/env python3
"""Run Anime2Sketch frame by frame over a video, without torchvision or kornia.

Usage:
  python3 sketch_lines.py ANIME2SKETCH_REPO film.mp4 output.mp4 [--start 11] [--dur 8.5] [--fps 12]
                          [--depth depth.mp4] [--test 13,18] [--raw]

ANIME2SKETCH_REPO is a local clone of https://github.com/Mukosame/Anime2Sketch (MIT licence) with the
upstream weights downloaded to weights/improved.bin (see the repository README for the download link).
Weights are not bundled with this skill.

- 16:9 without squashing: the frame goes to 1024x576 and gets a mirrored border up to 1024x768
  (the model wants multiples of 256).
- --fps 12: one drawing every 2 frames ("on twos"); the output is 24 fps.
- --depth: a depth-map video synced to the film; the distant background (low depth) turns into paper,
  as in pencil_animatic.py.
- Output: graphite on light paper, 1920x1080. With --raw, only the grey line comes out, for
  pencil_animatic.py --lines to give it the pencil finish.
Requires torch, numpy and ffmpeg. Uses MPS (Apple) when available, otherwise CPU.
"""
import argparse
import os
import subprocess
import sys

SETUP_HELP = """Anime2Sketch is not set up.
  1. git clone https://github.com/Mukosame/Anime2Sketch
  2. Download the 'improved.bin' weights linked in that repository's README into Anime2Sketch/weights/
  3. pip install torch numpy
  4. Pass the clone folder as the first argument of this script.
Anime2Sketch is MIT licensed; its weights come from the upstream project and are not redistributed here."""


def read(path, start, dur, fps, w, h, gray=False):
    import numpy as np
    fmt = "gray" if gray else "rgb24"
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", path, "-vf",
                          f"fps={fps},scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", fmt, "-"],
                         capture_output=True, check=True).stdout
    c = 1 if gray else 3
    n = w * h * c
    return [np.frombuffer(raw[i:i + n], np.uint8).reshape((h, w) if gray else (h, w, 3)) for i in range(0, len(raw) - n + 1, n)]


def load(repo, device):
    sys.path.insert(0, repo)
    cwd = os.getcwd()
    os.chdir(repo)  # the repository's model.py loads the weights by relative path
    try:
        from model import create_model
        net = create_model("improved")
    finally:
        os.chdir(cwd)
    return net.to(device).eval()


def sketch(net, rgb, device):
    import numpy as np
    import torch
    x = torch.from_numpy(rgb.astype(np.float32) / 127.5 - 1.0).permute(2, 0, 1)[None]
    pad = (768 - 576) // 2
    x = torch.nn.functional.pad(x, (0, 0, pad, pad), mode="reflect")
    with torch.no_grad():
        y = net(x.to(device))[0, 0].float().cpu().numpy()
    y = y[pad:pad + 576]
    return np.clip((y + 1) / 2, 0, 1)  # 1 = paper, 0 = line


def paint(sk, dep=None):
    import numpy as np
    paper = np.array([244, 240, 236], np.float32)  # RGB
    graphite = np.array([56, 58, 62], np.float32)
    ink = 1.0 - sk
    if dep is not None:
        d = dep.astype(np.float32) / 255.0
        ink *= np.clip((d - 0.17) / 0.10, 0, 1)
    out = paper[None, None] * (1 - ink[..., None]) + graphite[None, None] * ink[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", help="local clone of github.com/Mukosame/Anime2Sketch with weights/improved.bin")
    ap.add_argument("film")
    ap.add_argument("output")
    ap.add_argument("--start", type=float, default=0.0, help="start time in the film (s)")
    ap.add_argument("--dur", type=float, default=30.0, help="duration to process (s)")
    ap.add_argument("--fps", type=int, default=12, help="drawings per second (12 = on twos)")
    ap.add_argument("--depth", default="", help="depth-map video synced to the film (optional)")
    ap.add_argument("--test", default="", help="comma-separated seconds: write only PNG tests of these moments")
    ap.add_argument("--raw", action="store_true", help="output only the grey line (for pencil_animatic.py --lines)")
    a = ap.parse_args()
    if not os.path.isfile(os.path.join(a.repo, "model.py")) or not os.path.isfile(os.path.join(a.repo, "weights", "improved.bin")):
        print(f"Missing Anime2Sketch at '{a.repo}' (needs model.py and weights/improved.bin).\n\n{SETUP_HELP}")
        sys.exit(2)
    try:
        import numpy as np
        import torch
    except ImportError as e:
        print(f"Missing Python package: {e.name}. Install with: pip install torch numpy")
        sys.exit(2)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    net = load(a.repo, device)
    if a.test:
        for t in [float(x) for x in a.test.split(",")]:
            rgb = read(a.film, t, 0.1, a.fps, 1024, 576)[0]
            dep = read(a.depth, t, 0.1, a.fps, 1024, 576, gray=True)[0] if a.depth else None
            img = paint(sketch(net, rgb, device), dep)
            dest = f"{os.path.splitext(a.output)[0]}_test_{t:.1f}s.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1024x576", "-i", "-",
                            dest], input=img.tobytes(), check=True)
        print(f"OK tests ({device})")
        return
    rgbs = read(a.film, a.start, a.dur, a.fps, 1024, 576)
    deps = read(a.depth, a.start, a.dur, a.fps, 1024, 576, gray=True) if a.depth else [None] * len(rgbs)
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1024x576",
                             "-r", str(a.fps), "-i", "-", "-vf", "scale=1920:1080:flags=lanczos,fps=24",
                             "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", a.output], stdin=subprocess.PIPE)
    for rgb, dep in zip(rgbs, deps):
        if a.raw:
            sk = (sketch(net, rgb, device) * 255).astype(np.uint8)
            proc.stdin.write(np.repeat(sk[..., None], 3, axis=2).tobytes())
        else:
            proc.stdin.write(paint(sketch(net, rgb, device), dep).tobytes())
    proc.stdin.close()
    proc.wait()
    print(f"OK {a.output}: {len(rgbs)} drawings ({device})")


if __name__ == "__main__":
    main()
