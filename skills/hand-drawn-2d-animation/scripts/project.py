#!/usr/bin/env python3
"""Small portable production ledger.

Usage:
  python3 project.py init PROJECT_FOLDER       # create the folder tree and manifest.json (never overwrites)
  python3 project.py context PROJECT_FOLDER    # rewrite CONTEXT.md from manifest.json
  python3 project.py verify PROJECT_FOLDER     # probe and decode every deliverable; exits 1 on failure.
                                               # A deliverable may declare its own width, height and fps.
  python3 project.py cache-key SPEC.json       # sha256 of a canonical spec JSON (content hashes of all inputs)

Python standard library, plus ffprobe/ffmpeg for verify.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "templates" / "project.json"
FOLDERS = ("01_brief", "02_references", "03_boards", "04_animatic", "05_generation",
           "06_composite", "07_audio", "08_delivery", "09_qa")


def read(root):
    return json.loads((root / "manifest.json").read_text())


def context(root):
    m = read(root)
    text = (f"# {m['project_name']}\n\nStatus: {m['status']}\nMaster: {json.dumps(m['master'])}\n"
            f"Direction: {json.dumps(m['direction'], ensure_ascii=False)}\n\nNext action: {m['next_action']}\n\n")
    for key in ("open_issues", "decisions", "jobs", "deliverables"):
        text += f"## {key}\n\n" + json.dumps(m[key], ensure_ascii=False, indent=2) + "\n\n"
    (root / "CONTEXT.md").write_text(text)


def init(root):
    if root.exists():
        raise SystemExit("Destination already exists; nothing was overwritten.")
    root.mkdir(parents=True)
    for name in FOLDERS:
        (root / name).mkdir()
    m = json.loads(TEMPLATE.read_text())
    m["project_name"] = root.name
    (root / "manifest.json").write_text(json.dumps(m, ensure_ascii=False, indent=2))
    (root / "01_brief/BRIEF.md").write_text(
        "# Brief\n\nGoal, audience, duration, format, character, asset rights, approved direction, sound, "
        "authorised budget and acceptance criteria.\n")
    context(root)


def verify(root):
    m = read(root)
    results = []
    ok = bool(m["deliverables"])
    for item in m["deliverables"]:
        raw = item["file"] if isinstance(item, dict) else item
        path = Path(raw)
        path = path if path.is_absolute() else root / path
        row = {"file": raw, "exists": path.is_file()}
        try:
            if not path.is_file():
                raise ValueError("Missing file")
            row["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            meta = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                                                       "-of", "json", str(path)]))
            row["metadata"] = meta
            vids = [s for s in meta["streams"] if s["codec_type"] == "video"]
            if vids:
                s = vids[0]
                n, d = map(int, s["avg_frame_rate"].split("/"))
                # a 1080p finish or a 9:16 reel declares its own size; the rest must match the master
                master = {**m["master"], **{k: item[k] for k in ("width", "height", "fps") if isinstance(item, dict) and k in item}}
                row["master_matches"] = (s["width"] == master["width"] and s["height"] == master["height"]
                                         and abs(n / d - master["fps"]) < .001)
                if not row["master_matches"]:
                    ok = False
            r = subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(path), "-f", "null", "-"],
                               capture_output=True, text=True)
            row["decode_pass"] = r.returncode == 0
            row["decode_errors"] = r.stderr
            ok = ok and row["decode_pass"]
        except Exception as e:
            row["error"] = str(e)
            ok = False
        results.append(row)
    report = {"technical_pass": ok, "artistic_review": "not evaluated", "results": results}
    (root / "09_qa").mkdir(exist_ok=True)
    (root / "09_qa/technical.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("command", choices=["init", "context", "verify", "cache-key"])
    a.add_argument("path")
    args = a.parse_args()
    root = Path(args.path).resolve()
    if args.command == "init":
        init(root)
    elif args.command == "context":
        context(root)
    elif args.command == "verify":
        raise SystemExit(verify(root))
    else:
        # Canonical spec JSON containing content hashes for every input reference.
        spec = json.loads(root.read_text())
        print(hashlib.sha256(json.dumps(spec, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest())


if __name__ == "__main__":
    main()
