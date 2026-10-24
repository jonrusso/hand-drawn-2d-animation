#!/usr/bin/env python3
"""Check that the final version (upscale or new generation at a higher resolution) stays faithful to the approved film.

Usage:
  python3 fidelity.py approved_480p.mp4 final_1080p.mp4 output_folder

The final version is scaled down to the approved resolution and compared frame by frame, in luminance.
A faithful upscale has a low mean difference and no peaks; a regeneration usually shows peaks where
a face, hand or object changed. Writes FIDELITY.md and side-by-sides of the 6 most different frames.
The number points where to look; a human approves, looking at the frames.
Requires ffmpeg and ffprobe.
"""
import os
import subprocess
import sys

W, H = 128, 72


def info(v):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate:format=duration", "-of", "default=nw=1", v],
                         capture_output=True, text=True).stdout
    d = dict(line.split("=", 1) for line in out.strip().splitlines())
    a, b = d["r_frame_rate"].split("/")
    return int(d["width"]), int(d["height"]), float(a) / float(b), float(d["duration"])


def frames(v, rate):
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", v, "-vf", f"fps={rate},scale={W}:{H},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    n = W * H
    return [out[i:i + n] for i in range(0, len(out) - n + 1, n)]


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    a, b, out_dir = sys.argv[1:]
    os.makedirs(out_dir, exist_ok=True)
    wa, ha, fa, da = info(a)
    wb, hb, fb, db = info(b)
    fa_q, fb_q = frames(a, fa), frames(b, fa)
    n = min(len(fa_q), len(fb_q))
    diff = [sum(abs(x - y) for x, y in zip(fa_q[i], fb_q[i])) / (W * H) for i in range(n)]
    mean = sum(diff) / max(1, n)
    worst = sorted(range(n), key=lambda i: -diff[i])[:6]
    alerts = [i for i in range(n) if diff[i] > max(6.0, 3 * mean)]
    lines = ["# Final version fidelity", "",
             f"- Approved: `{a}` {wa}x{ha}, {fa:g} fps, {da:.2f} s",
             f"- Final: `{b}` {wb}x{hb}, {fb:g} fps, {db:.2f} s",
             f"- Same duration: {'yes' if abs(da - db) < 0.1 else 'NO'}; frames compared: {n}",
             f"- Mean difference: {mean:.2f} (0 to 255). Up to about 3 is expected from a faithful upscale.",
             f"- Frames above the limit: {len(alerts)}", "", "## Frames to look at", ""]
    for j, i in enumerate(worst, 1):
        t = i / fa
        dest = os.path.join(out_dir, f"compare_{j:02d}_{t:.2f}s.jpg")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", a, "-ss", f"{t:.3f}", "-i", b,
                        "-filter_complex", "[0:v]scale=-2:540,trim=end_frame=1[x];[1:v]scale=-2:540,trim=end_frame=1[y];[x][y]hstack",
                        "-frames:v", "1", dest], check=True)
        lines.append(f"- {t:.2f} s: difference {diff[i]:.2f} → `{os.path.basename(dest)}` (approved on the left, final on the right)")
    verdict = "suspect: check the frames" if alerts or mean > 3 else "no numeric alert"
    lines += ["", f"Result: {verdict}. Check face, hands, text and fine lines in the frames above."]
    with open(os.path.join(out_dir, "FIDELITY.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
