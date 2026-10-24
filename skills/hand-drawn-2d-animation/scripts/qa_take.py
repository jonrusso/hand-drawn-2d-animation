#!/usr/bin/env python3
"""Check a generated take against the shot list and prepare the human review.

Usage:
  python3 qa_take.py take.mp4 plan.json output_folder

Measures: real cuts against planned cuts (0.5 s tolerance), extra cuts (dissolves, jumps),
frozen frames longer than 8 frames, audio drops. Writes a contact sheet per shot and the
before/after frame strip of every cut, to check hands, face and screen axis.
It does not approve anatomy or acting: that is a human review, guided by the generated QA.md.
Requires ffmpeg and ffprobe; Python standard library only.
"""
import json
import os
import re
import subprocess
import sys


W, H = 96, 54


def frames(video):
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"scale={W}:{H},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    n = W * H
    return [out[i:i + n] for i in range(0, len(out) - n + 1, n)]


def fps(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                        "-of", "csv=p=0", video], capture_output=True, text=True).stdout.strip()
    a, b = r.split("/")
    return float(a) / float(b)


def real_cuts(fr, rate, threshold=28.0):
    n = W * H
    d = [sum(abs(a - b) for a, b in zip(fr[i], fr[i + 1])) / n for i in range(len(fr) - 1)]
    base = [sum(d[max(0, i - 4):i + 5]) / len(d[max(0, i - 4):i + 5]) for i in range(len(d))]
    peaks = [i + 1 for i in range(len(d)) if d[i] > threshold and d[i] > 3 * base[i] + 4]
    merged = []
    for p in peaks:
        if not merged or p - merged[-1] > 6:
            merged.append(p)
    return [round(p / rate, 3) for p in merged], d


def holds(d, rate, minimum=9):
    res, run = [], 0
    for i, x in enumerate(d):
        if x < 0.35:
            run += 1
        else:
            if run + 1 >= minimum:
                res.append((round((i - run) / rate, 2), round((i + 1) / rate, 2), run + 1))
            run = 0
    if run + 1 >= minimum:
        res.append((round((len(d) - run) / rate, 2), round(len(d) / rate, 2), run + 1))
    return res


def audio_drops(video):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", video, "-af", "ebur128=metadata=1,ametadata=print:key=lavfi.r128.M",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    t = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r)]
    m = [float(x) for x in re.findall(r"lavfi.r128.M=(-?[0-9.]+)", r)]
    drops = [(round(a, 1), b) for a, b in zip(t, m) if a > 0.5 and b < -38]
    out, last = [], -9
    for a, b in drops:
        if a - last > 0.6:
            out.append((a, b))
        last = a
    return out


def light_per_shot(video, bounds):
    """Mean luminance (0 to 255) and temperature (red minus blue) of each shot."""
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", "fps=4,scale=32:18,format=rgb24",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    n = 32 * 18 * 3
    fr = [out[i:i + n] for i in range(0, len(out) - n + 1, n)]
    res = []
    for a, b in zip(bounds[:-1], bounds[1:]):
        sel = fr[int(a * 4):max(int(a * 4) + 1, int(b * 4))]
        if not sel:
            res.append((0, 0))
            continue
        r = sum(sum(f[0::3]) for f in sel) / (len(sel) * 576)
        g = sum(sum(f[1::3]) for f in sel) / (len(sel) * 576)
        bl = sum(sum(f[2::3]) for f in sel) / (len(sel) * 576)
        res.append((round((r + g + bl) / 3), round(r - bl)))
    return res


def contact_sheet(video, start, end, dest):
    n = max(1, int((end - start) * 4))
    cols = min(n, 8)
    rows = (n + cols - 1) // cols
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-t", f"{end - start:.3f}", "-i", video, "-vf",
                    f"fps=4,scale=320:-1,tile={cols}x{rows}", "-frames:v", "1", dest], check=True)


def cut_strip(video, t, dest, rate):
    a = max(0.0, t - 2 / rate)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{4 / rate:.3f}", "-i", video, "-vf",
                    "scale=480:-1,tile=4x1", "-frames:v", "1", dest], check=True)


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    video, plan_json, out_dir = sys.argv[1:]
    os.makedirs(out_dir, exist_ok=True)
    with open(plan_json, encoding="utf-8") as fh:
        p = json.load(fh)
    rate = fps(video)
    fr = frames(video)
    dur = len(fr) / rate
    real, d = real_cuts(fr, rate)
    planned, t = [], 0.0
    for x in p["shots"][:-1]:
        t += float(x["dur_s"])
        planned.append(round(t, 3))
    lines = ["# Take QA", "", f"File: `{video}`  ", f"Duration: {dur:.2f} s at {rate:g} fps; planned {p['duration_s']} s.", ""]
    lines += ["## Cuts", "", "| Planned (s) | Real (s) | Difference | Status |", "|---|---|---|---|"]
    used = set()
    failures = 0
    for c in planned:
        near = [r for r in real if abs(r - c) <= 0.5 and r not in used]
        if near:
            r = min(near, key=lambda r: abs(r - c))
            used.add(r)
            lines.append(f"| {c:.2f} | {r:.2f} | {r - c:+.2f} | ok |")
        else:
            near = [r for r in real if abs(r - c) <= 1.5 and r not in used]
            if near:
                r = min(near, key=lambda r: abs(r - c))
                used.add(r)
                lines.append(f"| {c:.2f} | {r:.2f} | {r - c:+.2f} | off time |")
            else:
                lines.append(f"| {c:.2f} | not found | | shot skipped or merged |")
            failures += 1
    extras = [r for r in real if r not in used]
    for r in extras:
        lines.append(f"| | {r:.2f} | | extra cut: jump, dissolve or invented shot |")
        failures += 1
    lines += ["", "## Frozen frames longer than 8 frames", ""]
    hs = holds(d, rate)
    lines += [f"- {a:.2f} to {b:.2f} s ({n} frames): needs a reason on the exposure sheet" for a, b, n in hs] or ["- none"]
    lines += ["", "## Audio drops below -38 LUFS momentary", ""]
    drops = audio_drops(video)
    lines += [f"- {a:.1f} s ({b:.1f} LUFS)" for a, b in drops] or ["- none"]
    bounds = [0.0] + sorted(set(planned)) + [dur]
    light = light_per_shot(video, bounds)
    lines += ["", "## Light per shot", "", "| Shot | Location | Luminance | Temperature | Status |", "|---|---|---|---|---|"]
    jumps = 0
    for i, (lum, temp) in enumerate(light):
        x = p["shots"][i] if i < len(p["shots"]) else {}
        status = ""
        if i and i < len(p["shots"]) and p["shots"][i - 1].get("location") == x.get("location") and abs(lum - light[i - 1][0]) > 25:
            status = "light jump in the same location"
            jumps += 1
        lines.append(f"| {i + 1} | {x.get('location', '')} | {lum} | {temp:+d} | {status} |")
    for i in range(len(bounds) - 1):
        contact_sheet(video, bounds[i], bounds[i + 1], os.path.join(out_dir, f"shot_{i + 1:02d}.jpg"))
    for j, r in enumerate(real, 1):
        cut_strip(video, r, os.path.join(out_dir, f"cut_{j:02d}_{r:.2f}s.jpg"), rate)
    lines += ["", "## Mandatory human review (open the sheets)", ""]
    for i, x in enumerate(p["shots"], 1):
        items = []
        if x.get("face_visible"):
            f = x.get("face", {})
            items.append(f"face: {'; '.join(f.get(k, '') for k in ('eyebrows', 'eyes', 'mouth') if f.get(k))}")
        for m in x.get("micro_actions", []):
            items.append(f"{m['hand']} hand {m['verb']} {m['object']}: five fingers, no fusion")
        if x.get("cut", {}).get("reason") and i < len(p["shots"]):
            items.append(f"cut happens {x['cut']['reason']}")
        lines.append(f"- [ ] shot {i} (`shot_{i:02d}.jpg`): " + " | ".join(items or ["readable action"]))
    lines += ["", f"Automatic result: {'FAILED' if failures or hs or jumps else 'no alerts'} "
              f"({failures} cut problem(s), {len(hs)} hold(s), {jumps} light jump(s)). Fix only the failed interval."]
    with open(os.path.join(out_dir, "QA.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
