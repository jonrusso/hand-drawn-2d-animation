#!/usr/bin/env python3
"""Depth map of a finished film with Video Depth Anything Small, restarting at every real cut.

Usage:
  python3 depth_map.py VDA_REPO film.mp4 output_folder --cuts 0,46,105,146,179,553,656,720 [--input-size 518]

VDA_REPO is a local clone of https://github.com/DepthAnything/Video-Depth-Anything with the Small checkpoint
downloaded to checkpoints/video_depth_anything_vits.pth (code and Small: Apache 2.0; Base and Large: CC BY-NC 4.0).
Weights are not bundled with this skill.

- --cuts: frame boundaries of the real shots, from 0 to the last frame. Measure them on this film
  (qa_take.py lists the real cuts in seconds; multiply by the fps). Never copy the BOLHAO list above.
- The temporal state restarts at every cut: depth is never smoothed across a cut.
- Writes depth_0000.png... (16-bit, white near / black far, contrast fixed per shot from its 1st and 99th
  percentile, never per frame), shot_NN/relative_depth_float32.npz (raw values), shot_NN/comparison.png
  and manifest.json. A shot whose .npz already exists is reused, so an interrupted run resumes.
- Relative inverse depth, not metres and not a Z channel. Printed text becomes false relief; a transparent
  bubble gets an estimated surface.
- Visible video: ffmpeg -framerate 24 -i out/depth_%04d.png -vf scale=1920:1080 -pix_fmt yuv420p depth.mp4
Requires torch, numpy, opencv-python and ffmpeg. Uses Apple MPS when available, otherwise CPU. No credits.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

SETUP_HELP = """Video Depth Anything is not set up.
  1. git clone https://github.com/DepthAnything/Video-Depth-Anything
  2. Download the Small checkpoint linked in that README to checkpoints/video_depth_anything_vits.pth
  3. pip install torch numpy opencv-python (plus the repository's requirements)
  4. Pass the clone folder as the first argument of this script.
Use Small for commercial work: Base and Large are non-commercial. Weights are not redistributed here."""
CHECKPOINT = Path("checkpoints") / "video_depth_anything_vits.pth"


def probe(film):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
                          "stream=width,height,r_frame_rate,nb_read_frames", "-of", "json", film],
                         capture_output=True, text=True, check=True).stdout
    s = json.loads(out)["streams"][0]
    a, b = s["r_frame_rate"].split("/")
    return int(s["width"]), int(s["height"]), float(a) / float(b), int(s["nb_read_frames"])


def frames(film, w, h):
    """Decode once, in order, through ffmpeg: no frame-accurate seeking needed, no OpenCV colour matrix."""
    import numpy as np
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", film, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                            stdout=subprocess.PIPE)
    n = w * h * 3
    while True:
        buf = proc.stdout.read(n)
        if len(buf) < n:
            break
        yield np.frombuffer(buf, np.uint8).reshape(h, w, 3)
    proc.wait()


def patch_attention(attention_cls):
    """Spatial attention through PyTorch SDPA in batches of four, to fit Apple MPS memory. Same weights, same math:
    checked against the original on a random input before use. The temporal model and its 32-frame window stay upstream."""
    import torch
    import torch.nn.functional as F

    def forward(self, x):
        out = []
        for part in x.split(4, dim=0):
            b, n, c = part.shape
            qkv = self.qkv(part).reshape(b, n, 3, self.num_heads, c // self.num_heads).permute(2, 0, 3, 1, 4)
            y = F.scaled_dot_product_attention(qkv[0], qkv[1], qkv[2], dropout_p=0., scale=self.scale)
            out.append(self.proj_drop(self.proj(y.transpose(1, 2).reshape(b, n, c))))
        return torch.cat(out)

    torch.manual_seed(7)
    attn = attention_cls(48, 4).eval()
    test = torch.randn(6, 35, 48)
    with torch.no_grad():
        err = (attn(test) - forward(attn, test)).abs().max().item()
    assert err < 1e-5, err
    attention_cls.forward = forward
    return err


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", help="local clone of github.com/DepthAnything/Video-Depth-Anything with the Small checkpoint")
    ap.add_argument("film")
    ap.add_argument("output")
    ap.add_argument("--cuts", required=True, help="comma-separated frame boundaries, from 0 to the last frame")
    ap.add_argument("--input-size", type=int, default=518)
    a = ap.parse_args()
    repo = Path(a.repo)
    if not (repo / "video_depth_anything").is_dir() or not (repo / CHECKPOINT).is_file():
        print(f"Missing Video Depth Anything at '{a.repo}' (needs video_depth_anything/ and {CHECKPOINT}).\n\n{SETUP_HELP}")
        sys.exit(2)
    cuts = [int(x) for x in a.cuts.split(",")]
    if cuts[0] != 0 or any(b <= s for s, b in zip(cuts, cuts[1:])):
        sys.exit("--cuts must start at 0 and increase")
    try:
        import cv2
        import numpy as np
        import torch
    except ImportError as e:
        print(f"Missing Python package: {e.name}. Install with: pip install torch numpy opencv-python")
        sys.exit(2)
    sys.path.insert(0, str(repo))
    from video_depth_anything.dinov2_layers.attention import Attention
    from video_depth_anything.video_depth import VideoDepthAnything

    w, h, fps, count = probe(a.film)
    if count < cuts[-1]:
        sys.exit(f"the film has {count} frames, --cuts ends at {cuts[-1]}")
    err = patch_attention(Attention)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = VideoDepthAnything(encoder="vits", features=64, out_channels=[48, 96, 192, 384])
    model.load_state_dict(torch.load(repo / CHECKPOINT, map_location="cpu", weights_only=True), strict=True)
    model.to(device).eval()
    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=True)
    commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    report = dict(source=Path(a.film).name, source_sha256=sha256(a.film), model="Video-Depth-Anything-Small",
                  checkpoint_sha256=sha256(repo / CHECKPOINT), upstream_commit=commit or "unknown", device=device,
                  torch_version=torch.__version__, fps=fps, frames=cuts[-1], cuts=cuts, input_size=a.input_size,
                  depth_kind="relative inverse depth, white near / black far",
                  normalization="fixed 1st and 99th percentile per shot; never per frame",
                  cost_credits=0, attention_equivalence_max_error=err, shots=[])
    print(json.dumps(dict(device=device, fps=fps, frames=cuts[-1], input_size=a.input_size)), flush=True)
    src = frames(a.film, w, h)
    started = time.time()
    for idx, (start, end) in enumerate(zip(cuts, cuts[1:]), 1):
        shot = np.stack([next(src) for _ in range(start, end)])
        shot_dir = out / f"shot_{idx:02}"
        shot_dir.mkdir(exist_ok=True)
        raw = shot_dir / "relative_depth_float32.npz"
        t = time.time()
        if raw.exists():
            with np.load(raw) as z:
                depth = z["depth"]
            assert depth.shape == shot.shape[:3]
        else:
            depth, _ = model.infer_video_depth(shot, fps, input_size=a.input_size, device=device, fp32=True)
            assert np.isfinite(depth).all()
            np.savez_compressed(raw, depth=depth.astype(np.float32))
        low, high = np.percentile(depth[::max(1, len(depth) // 30)], [1, 99]).tolist()
        assert high > low
        for k, d in enumerate(depth):
            norm = np.clip((d - low) / (high - low), 0, 1)
            assert cv2.imwrite(str(out / f"depth_{start + k:04}.png"), (norm * 65535).round().astype(np.uint16))
        mid = len(shot) // 2
        grey = (np.clip((depth[mid] - low) / (high - low), 0, 1) * 255).astype(np.uint8)
        cv2.imwrite(str(shot_dir / "comparison.png"),
                    cv2.cvtColor(np.concatenate([shot[mid], np.repeat(grey[..., None], 3, axis=2)], axis=1), cv2.COLOR_RGB2BGR))
        report["shots"].append(dict(shot=idx, start_frame=start, end_frame_exclusive=end,
                                    seconds=round(time.time() - t, 2), low=low, high=high))
        report["elapsed_seconds"] = round(time.time() - started, 2)
        (out / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
        print(json.dumps(report["shots"][-1]), flush=True)
        if device == "mps":
            torch.mps.empty_cache()
    print(f"OK {cuts[-1]} depth maps in {out} ({device}, {report['elapsed_seconds']} s)")


if __name__ == "__main__":
    main()
