#!/usr/bin/env python3
"""Build and validate the master prompt of a single multi-shot generation from the shot list.

Usage:
  python3 master_prompt.py check plan.json                # validate only; exits 1 on any error
  python3 master_prompt.py build plan.json prompt.txt     # validate and write the video prompt
  python3 master_prompt.py storyboard plan.json folder/   # validate and write one image prompt per shot

The prompt is never written by hand: it comes out of the approved shot list.
An ERROR blocks the generation. A WARN must be read and accepted.
"""
import json
import os
import re
import sys

BLOCKED_VISUAL = [
    "glass", "glassy", "ice", "icy", "crystal", "frozen solid", "solid block",
    "solid cone", "photorealistic water", "morph", "seamlessly becomes",
]
# Film, studio and director names: describe the technique, never the studio or the film.
BLOCKED_NAMES = [
    "ghibli", "miyazaki", "ponyo", "pixar", "disney", "monsters, inc", "monsters inc",
    "sulley", "boo", "dreamworks", "studio", "in the style of",
]
SOFT_TRANSITIONS = ["fade", "dissolve", "crossfade", "cross-fade"]
CUT_TYPES = {
    "action": "on the action",
    "eyeline": "on the eyeline",
    "reaction": "to the reaction",
    "object": "through the object",
    "sound": "on the sound",
    "place": "to a new place",
    "end": "",
}
TIMESTAMP = re.compile(r"\b\d{1,2}\s*[-–]\s*\d{1,2}\s*s\b|\[\s*\d+\s*-\s*\d+\s*s?\s*\]|\b\d+:\d{2}\b")
FACE_PARTS = ("eyes", "eyebrows", "mouth")  # order in which the expression happens


def texts(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from texts(v)
    elif isinstance(node, list):
        for v in node:
            yield from texts(v)


def check(p):
    errors, warnings = [], []
    dur = float(p["duration_s"])
    shots = p["shots"]
    total = sum(float(x["dur_s"]) for x in shots)
    if abs(total - dur) > 0.5:
        errors.append(f"shot durations add up to {total:.1f}s, plan duration is {dur:.1f}s")
    mean = dur / max(1, len(shots))
    if mean < 3:
        errors.append(f"{len(shots)} shots in {dur:.0f}s (mean {mean:.1f}s): below 3 s per shot the model skips and shuffles shots")
    elif mean < 4.5 and p.get("genre", "acting") == "acting":
        warnings.append(f"mean of {mean:.1f}s per shot: for acting, sources suggest 3 to 5 shots in 30 s")
    if dur > 15 and not p.get("use_timestamps"):
        warnings.append("long generation without time bands: risk of the action bunching at the start; run the timestamp A/B test before adopting")

    numbers = {3: "three", 4: "four", 5: "five", 6: "six"}
    for name, c in p["characters"].items():
        b = c["block"].lower()
        if not c.get("has_hands", True):
            continue
        fingers = int(c.get("fingers", 5))
        if fingers != 5 and not c.get("fingers_approved_on_sheet"):
            errors.append(f"character {name}: {fingers} fingers only allowed with 'fingers_approved_on_sheet': true (humans have five)")
        if f"exactly {numbers.get(fingers, fingers)} fingers" not in b:
            errors.append(f"character {name}: the block must say 'exactly {numbers.get(fingers, fingers)} fingers on each hand'")
    setups = {}
    for i, x in enumerate(shots, 1):
        tag = f"shot {i}"
        if float(x["dur_s"]) < 2:
            warnings.append(f"{tag}: {x['dur_s']}s is too short to read action and reaction")
        setups.setdefault(x["location"], set()).add(x["setup"])
        if not x.get("action"):
            errors.append(f"{tag}: no action")
        if not x.get("end_frame"):
            errors.append(f"{tag}: missing 'end_frame' (pose, expression and object positions on the last frame of the shot)")
        if x.get("face_visible"):
            f = x.get("face", {})
            empty = [k for k in FACE_PARTS if not f.get(k)]
            if len(empty) > 1:
                errors.append(f"{tag}: a visible face needs at least two parts described ({', '.join(FACE_PARTS)})")
            if not f.get("cause"):
                errors.append(f"{tag}: the expression needs its cause (what the character just saw or felt)")
        for m in x.get("micro_actions", []):
            missing = [k for k in ("hand", "object", "verb") if not m.get(k)]
            if missing:
                errors.append(f"{tag}: incomplete micro-action, missing {', '.join(missing)}")
            if not m.get("count"):
                warnings.append(f"{tag}: micro-action without a count ('twice', 'once'); a count pins the gesture")
        if len(x.get("micro_actions", [])) > 2:
            warnings.append(f"{tag}: more than two micro-actions in the same shot")
        wide = "wide" in x.get("framing", "").lower()
        if wide and x.get("micro_actions"):
            errors.append(f"{tag}: hand micro-action in a wide shot; in a wide shot the hand is a simple shape, micro-actions belong in a medium shot or close-up")
        if wide and x.get("face_visible"):
            warnings.append(f"{tag}: an expression in a wide shot disappears at 480p; move it to a medium shot or close-up")
        cut = x.get("cut", {})
        if i < len(shots):
            if cut.get("type") not in CUT_TYPES or cut.get("type") == "end":
                errors.append(f"{tag}: exit cut without a valid type ({', '.join(k for k in CUT_TYPES if k != 'end')})")
            if not cut.get("reason"):
                errors.append(f"{tag}: exit cut without a visible reason")
            nxt = shots[i]
            if nxt["location"] == x["location"] and nxt["setup"] == x["setup"]:
                errors.append(f"{tag}: the next shot repeats the same setup in the same location (jump cut)")
            if (nxt["location"] == x["location"] and x.get("screen_direction") and nxt.get("screen_direction")
                    and x["screen_direction"] != nxt["screen_direction"] and cut.get("type") != "reaction"):
                errors.append(f"{tag}: screen direction flips in the same location without a reaction cut (axis break)")
    for location, s in setups.items():
        if len(s) > 4:
            warnings.append(f"location {location}: {len(s)} camera setups; fixed coverage calls for at most 4 per location")

    everything = " ".join(texts(p)).lower()
    for w in BLOCKED_VISUAL:
        if re.search(r"\b" + re.escape(w) + r"\b", everything) and not re.search(r"\bnever " + re.escape(w), everything):
            errors.append(f"blocked term: '{w}' (turns into glass, ice or a morph)")
    for w in BLOCKED_NAMES:
        if re.search(r"\b" + re.escape(w) + r"\b", everything):
            errors.append(f"third-party name in the prompt: '{w}' (describe the technique, not the studio, director or film)")
    for w in SOFT_TRANSITIONS:
        if re.search(r"\b" + w, everything) and not re.search(r"\bno " + w, everything):
            warnings.append(f"'{w}' appears: video models tend to resolve it as a dissolve or a morph")
    if not p.get("use_timestamps") and TIMESTAMP.search(everything):
        errors.append("timestamp in the text while use_timestamps=false (time bands only after the A/B test)")
    return errors, warnings


def build(p):
    parts = [p["style"].strip(), ""]
    for r in p.get("references", []):
        if r.get("type") != "storyboard":
            parts.append(f"{r['id']}: {r['role']}")
    if p.get("references"):
        parts.append("")
    for c in p["characters"].values():
        parts.append(c["block"].strip())
    parts.append("")
    n = len(p["shots"])
    kf = [r["id"] for r in p.get("references", []) if r.get("type") == "storyboard"]
    if kf:
        parts.append(f"Use {kf[0]} to {kf[-1]} in order as keyframes, one per shot; they guide composition and pose, they are not panels to animate.")
    parts.append(f"CAMERA: exactly {n} shots joined by motivated hard cuts, no other cuts, no jump cuts. Each shot keeps a gentle drift, never a frozen frame. {p.get('axis_rule', '')}".strip())
    parts.append("")
    parts.append("SCENE:")
    t = 0.0
    for i, x in enumerate(p["shots"], 1):
        head = f"[{int(t)}-{int(t + float(x['dur_s']))}s] " if p.get("use_timestamps") else ""
        t += float(x["dur_s"])
        sentence = [f"{i}. {head}{x['framing']}, {x['camera']}. {x['action'].strip()}"]
        for m in x.get("micro_actions", []):
            sentence.append(f"His {m['hand']} hand {m['verb']} the {m['object']} {m.get('count', '')}".strip() + ".")
        f = x.get("face") if x.get("face_visible") else None
        if f:
            pieces = [f.get(k) for k in FACE_PARTS if f.get(k)]
            sentence.append(f"Because {f['cause']}: first " + ", then ".join(pieces) + ".")
        sentence.append(f"On screen at end: {x['end_frame']}.")
        if i < n:
            c = x["cut"]
            sentence.append(f"Cut to shot {i + 1} {c['reason']}.")
        parts.append(" ".join(s.strip() for s in sentence))
    parts.append("")
    parts.append(p["life"].strip())
    parts.append("")
    parts.append(p["constraints"].strip())
    parts.append(f"Sound: {p['sound'].strip()} No music.")
    return "\n".join(parts).strip() + "\n"


def storyboard(p, folder):
    """One image prompt per shot, for the storyboard frame that becomes a keyframe of the generation."""
    os.makedirs(folder, exist_ok=True)
    refs = [f"{r['id']}: {r['role']}" for r in p.get("references", []) if r.get("type") != "storyboard"]
    blocks = [c["block"].strip() for c in p["characters"].values()]
    for i, x in enumerate(p["shots"], 1):
        f = x.get("face") if x.get("face_visible") else None
        face = ""
        if f:
            face = "Expression: " + ", ".join(f.get(k) for k in FACE_PARTS if f.get(k)) + f", because {f['cause']}."
        txt = "\n".join([
            p["style"].strip(), "", *refs, "", *blocks, "",
            f"Single still storyboard frame for shot {i} of {len(p['shots'])}. {x['framing']}, {p.get('aspect_ratio', '16:9')} frame.",
            f"The moment shown: {x['end_frame']}. Context: {x['action'].strip()}",
            face,
            "Clean finished frame, no panel borders, no numbers, no text, no watermark.",
        ]).replace("\n\n\n", "\n\n").strip() + "\n"
        with open(os.path.join(folder, f"SB_{i:02d}_prompt.txt"), "w", encoding="utf-8") as fh:
            fh.write(txt)
    print(f"OK {len(p['shots'])} storyboard prompts in {folder}")


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("check", "build", "storyboard") or (sys.argv[1] != "check" and len(sys.argv) < 4):
        print(__doc__)
        sys.exit(2)
    with open(sys.argv[2], encoding="utf-8") as fh:
        p = json.load(fh)
    errors, warnings = check(p)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    if sys.argv[1] == "storyboard" and not errors:
        storyboard(p, sys.argv[3])
    if sys.argv[1] == "build":
        txt = build(p)
        limit = int(p.get("char_limit", 4000))
        if len(txt) > limit:
            errors.append(f"prompt has {len(txt)} characters, limit is {limit}")
            print("ERROR", errors[-1])
        if not errors:
            with open(sys.argv[3], "w", encoding="utf-8") as fh:
                fh.write(txt)
            print(f"OK prompt written: {len(txt)}/{limit} characters")
    if errors:
        print(f"FAILED: {len(errors)} error(s). Fix the shot list, not the prompt.")
        sys.exit(1)
    if sys.argv[1] == "check":
        print("PASSED the check")


if __name__ == "__main__":
    main()
