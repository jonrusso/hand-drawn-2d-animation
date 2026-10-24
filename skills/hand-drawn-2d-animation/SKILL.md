---
name: hand-drawn-2d-animation
description: Plans, prompts, generates and checks short 2D animated films that look hand-drawn, made with AI video models such as Seedance inside CapCut. Covers the story interview, character, place and object sheets, shot list and storyboard, a single master prompt for one-pass generation, frame-by-frame QA with localized repair, 1080p finishing, a depth-map pass and a pencil animatic made with open-source tools. Use when the user wants an AI animated short, a storybook or classic hand-drawn look, character model sheets, a shot list or storyboard for an AI video, a Seedance prompt for a multi-shot film, a QA of a generated take, or a pencil-test or animatic version of a finished film.
license: Apache-2.0
compatibility: Python 3.10+ and ffmpeg/ffprobe for the scripts. Pillow and numpy for image tools. Optional torch (sketch lines, depth) and onnxruntime (character mask). An image generator and a video generator (for example CapCut with Seedance) are needed for the generation steps.
metadata:
  version: "0.2.0"
  author: "russodev"
---

# Hand-drawn 2D animation with AI video

An AI video model is a probability machine. This skill takes every decision away from it that can be made earlier and cheaper, then spends video credits once. Six steps; only step 5 costs video.

| Step | Output | Cost | Gate before moving on |
|---|---|---|---|
| 1. Story interview | `intent.md` with no open question | none | the user answers until no shot depends on a guess |
| 2. Story bible | character, place and object sheets | images | the user approves each sheet |
| 3. Shots and storyboard | `plan.json` with 3 to 7 shots, one keyframe per shot, an animatic | images | `scripts/master_prompt.py check` passes and the user approves the animatic |
| 4. Master prompt | prompt assembled by the script, never by hand | none | the user sees the prompt and the quoted cost |
| 5. One generation | the whole film in one pass, draft resolution | video | explicit user approval with the cost on screen |
| 6. QA and repair | QA sheets, repaired shots, 1080p finish | video only for repairs | user acceptance |

Load only the reference for the current step:

| Step | Reference |
|---|---|
| 1 | [story interview](references/01-story-interview.md) |
| 2 | [story bible and sheet prompts](references/02-story-bible.md) |
| 3 | [shots, storyboard and animatic](references/03-shots-and-storyboard.md), [acting that feels human](references/04-acting.md) |
| 4 | [master prompt anatomy](references/05-master-prompt.md) |
| 5 | [generating in CapCut](references/06-generation.md) |
| 6 | [QA and repair](references/07-qa-and-repair.md), [finishing in 1080p](references/08-finishing.md) |
| Extras | [depth map pass](references/09-depth-map.md), [pencil animatic from a finished film](references/10-pencil-animatic.md), [breakdown reel for social](references/11-breakdown-reel.md), [sound](references/12-sound.md) |
| Credits and style lineage | [credits](references/13-credits-and-style.md) |

## Rules that change outcomes

1. **Never generate video before the storyboard plays well as a slideshow.** If the story does not work as stills, motion will not save it.
2. **Five fingers, in words.** Every prompt that shows a hand says "exactly five fingers on each hand (four fingers plus one thumb), never four, never six". `master_prompt.py` rejects a plan without it.
3. **Every face change has a cause and an order.** "Because X: first the eyes, then the eyebrows, then the mouth."
4. **Every cut has a trigger.** A look, an action, a sound or an object filling the frame. "Exactly N shots, no other cuts."
5. **Describe technique, never a film, studio or director.** Credits for inspiration live in the README and in [credits](references/13-credits-and-style.md), never in prompts. A character that reads as a famous one gets redesigned, not renamed.
6. **Water, steam and bubbles are drawn.** Rounded shapes in 3 or 4 tones with an outline. Never glass, ice or photographic fluid.
7. **Typed text goes in the edit.** Titles, taglines, captions and CTA are editable text in the editor. A product label that already exists in a reference image can stay in the generation; check every letter. A generated tagline can misspell a word and pass every review.
8. **Keyframes are clean stills.** Make them in the image tool. Never use a frame exported from a generated video: it carries the platform watermark, and the model redraws it.
9. **First and last frame must agree.** Same characters on the same sides, same scale, light and set. If they cannot agree, use the first frame only.
10. **Repair locally.** Never regenerate the whole film for one local defect.
11. **Cost needs consent.** Quote the price and wait for an explicit yes before any paid image or video job. A job already submitted is polled, never resubmitted. Tell a chat-driven generator to make one attempt and stop on error.
12. **A file that exists is not a film that works.** Watch at full speed, then frame by frame at every cut, before saying it is done.

What the BOLHAO example proves and what it does not: the approved 480p take is one 30 s pass of the integral v3 prompt, the one published with the film (`assets/examples/bolhao_v03_integral_prompt.txt`: whole-second time ranges, its own continuous score, the product shot inside the generation); the 1080p master is two 15 s regenerations of that take. `bolhao_30s_plan.json` is this method applied afterwards and has not been generated yet.

## Project state

Keep one folder per film with `intent.md`, `plan.json`, the approved sheets, `storyboard/`, prompts, takes and a `manifest.json` (one entry per attempt: references, prompt hash, job id, cost, file, QA verdict). Start one with:

```sh
python3 scripts/project.py init path/to/my-film
python3 scripts/project.py verify path/to/my-film
```

Re-read the manifest before submitting anything. Provider capabilities, prices and limits change: check them in the connector at the time of the job.

## Scripts

All scripts are local and free. See [scripts/README.md](scripts/README.md).

| Script | Use |
|---|---|
| `master_prompt.py` | check a `plan.json`, build storyboard image prompts and the video master prompt |
| `animatic.py` | storyboard frames to an animatic at exact shot durations |
| `qa_take.py` | compare a generated take with the plan: cuts, frozen and black frames, audio drops and sample rate, per-shot sheets |
| `fidelity.py` | confirm a 1080p finish still matches the approved draft |
| `depth_map.py` | depth map of the finished film, restarted at every cut (Video Depth Anything Small) |
| `timing_chart.py` | animated exposure sheet overlay (keys, breakdowns, frame ruler) |
| `sketch_lines.py`, `pencil_animatic.py` | pencil animatic from a finished film (Anime2Sketch, isnet-anime) |
| `breakdown_reel.py`, `lettering.py` | 9:16 breakdown reel with stacked bands, and animated lettering |
| `compose_layers.py`, `project.py` | layer compositing on twos, project init and verification |
