#!/usr/bin/env python3
"""Build the storyboard animatic at the exact duration of each shot, so the timing is approved before any video.

Usage:
  python3 animatic.py plan.json frames_folder output.mp4 [guide_track.wav]

Expects frames SB_01.png, SB_02.png... in the folder (jpg/jpeg/webp also work). Each frame stays on screen
for the shot's dur_s, with a slow push from 100% to 103%, at 24 fps, 1280x720. Without a track the output is silent.
Requires ffmpeg.
"""
import json
import os
import subprocess
import sys
import tempfile


def find_frame(folder, i):
    for ext in ("png", "jpg", "jpeg", "webp"):
        f = os.path.join(folder, f"SB_{i:02d}.{ext}")
        if os.path.exists(f):
            return f
    raise SystemExit(f"missing frame SB_{i:02d} in {folder}")


def main():
    if len(sys.argv) not in (4, 5):
        print(__doc__)
        sys.exit(2)
    plan, folder, output = sys.argv[1:4]
    track = sys.argv[4] if len(sys.argv) == 5 else None
    with open(plan, encoding="utf-8") as fh:
        p = json.load(fh)
    tmp = tempfile.mkdtemp(prefix="animatic_")
    parts = []
    t = 0.0
    for i, x in enumerate(p["shots"], 1):
        # round the running cut time, not each shot, so the cuts land where qa_take.py expects them
        frames = max(1, round((t + float(x["dur_s"])) * 24) - round(t * 24))
        t += float(x["dur_s"])
        out = os.path.join(tmp, f"p{i:02d}.mp4")
        zoom = f"zoompan=z='1+0.03*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1280x720:fps=24"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", find_frame(folder, i), "-vf",
                        f"scale=2560:1440:force_original_aspect_ratio=increase,crop=2560:1440,{zoom},format=yuv420p",
                        "-frames:v", str(frames), "-c:v", "libx264", "-crf", "18", out], check=True)
        parts.append(out)
    concat_list = os.path.join(tmp, "list.txt")
    with open(concat_list, "w") as fh:
        fh.write("".join(f"file '{x}'\n" for x in parts))
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", concat_list]
    if track:
        cmd += ["-i", track, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-shortest"]
    cmd += ["-c:v", "copy", output]
    subprocess.run(cmd, check=True)
    total = sum(float(x["dur_s"]) for x in p["shots"])
    print(f"OK animatic {output}: {len(parts)} shots, {total:.2f} s")


if __name__ == "__main__":
    main()
