# Scripts

Command-line tools behind the skill. Each one prints its full usage with `-h` (or with no arguments).
Install with `pip install -r requirements.txt`; ffmpeg and ffprobe must be on `PATH`.
Nothing here calls a network service or spends generation credits.

| Script | Purpose | Example |
|---|---|---|
| `master_prompt.py` | Validate a shot-list plan (five-finger rule, blocked film/studio names, motivated cuts, end frames) and build the multi-shot video prompt or per-shot storyboard prompts. | `python3 master_prompt.py build ../assets/examples/bolhao_30s_plan.json prompt.txt` |
| `animatic.py` | Storyboard animatic with every frame held for its shot's exact duration, slow push-in, optional guide track. | `python3 animatic.py plan.json boards/ animatic.mp4 guide.wav` |
| `qa_take.py` | Measure a generated take against the plan: real vs planned cuts, frozen frames, audio drops, light jumps; writes QA.md and contact sheets for human review. | `python3 qa_take.py take.mp4 plan.json qa/` |
| `fidelity.py` | Compare an upscale or re-generation with the approved low-res film and point at the frames that changed. | `python3 fidelity.py approved_480p.mp4 final_1080p.mp4 fidelity/` |
| `timing_chart.py` | Transparent ProRes 4444 timing layer: frame ruler, keys, breakdowns, exposure brackets and cursor (horizontal or column mode). | `python3 timing_chart.py timing.json timing.mov --font MyFont.ttf` |
| `compose_layers.py` | Composite RGBA layers with per-layer exposure (ones/twos) under a continuous parallax camera, with preflight and overscan checks. | `python3 compose_layers.py ../assets/templates/layers.example.json shot.mp4` |
| `sketch_lines.py` | Run Anime2Sketch frame by frame to extract clean line art from a film (weights not bundled). | `python3 sketch_lines.py ~/src/Anime2Sketch film.mp4 lines.mp4 --raw` |
| `pencil_animatic.py` | Turn a film plus its depth map into rough pencil animation (rough, pencil test, line animatic, or isnet-anime matte). | `python3 pencil_animatic.py film.mp4 depth.mp4 pencil.mp4 --lines lines.mp4 --style animatic` |
| `lettering.py` | Animated lettering card with alpha (pop, rise, type, cut; glow, breathe, exits). | `python3 lettering.py title.json title.mov` |
| `breakdown_reel.py` | 9:16 breakdown reel of stacked bands with labels; writes FCP7 XML (xmeml), which imports in Premiere and other NLEs, plus an MP4 preview. | `python3 breakdown_reel.py reel.json` |
| `project.py` | Portable production ledger: create a project tree, regenerate CONTEXT.md, verify deliverables, hash specs. | `python3 project.py init my_film && python3 project.py verify my_film` |

## Third-party models (not bundled)

- **Anime2Sketch** (MIT): clone https://github.com/Mukosame/Anime2Sketch and download `weights/improved.bin`
  from the upstream README. Pass the clone folder as the first argument of `sketch_lines.py`.
- **isnet-anime** (Apache-2.0): download `isnetis.onnx` from https://huggingface.co/skytnt/anime-seg and pass it
  with `pencil_animatic.py --style isnet --model isnetis.onnx`.
- The depth map for `pencil_animatic.py` can come from any monocular video depth model; the script only reads a
  greyscale video synced to the film (bright = near).

## Fonts

`timing_chart.py`, `lettering.py` and `breakdown_reel.py` take a font path from the config or `--font`.
Without one they try common system fonts (DejaVu Sans, Arial, Helvetica) and fall back to Pillow's default font.
