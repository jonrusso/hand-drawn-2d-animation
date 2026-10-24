# Changelog

All notable changes to this project are documented here. Format: [Keep a Changelog](https://keepachangelog.com), versioning: SemVer.

## [0.2.1] - 2026-10-24
### Added
- `TRIBUTE.md`: the skill is dedicated to Tyrus Wong, with his story, why the skill follows his work, how we keep that respectful, and where to learn more.
- A dedication under the hero image in both READMEs.

## [0.2.0] - 2026-10-24
Review of the BOLHAO production files by [@wanrleydesigner](https://www.instagram.com/wanrleydesigner): every rule checked against what the film, the V1 corrections and the master QA prove.

### Added
- `depth_map.py`: the Video Depth Anything Small pass used on BOLHAO, restarted at every cut, as a script.
- The v03 integral prompt published with the film, as `assets/examples/bolhao_v03_integral_prompt.txt`.
- Evals for mismatched first and last frames, keyframes taken from video, generated text, 1080p finishing and music across blocks.
- The case study and README now say how the film was really made.
- CI installs OpenCV so the pencil animatic test runs.

### Changed
- References now carry what the BOLHAO files prove: plugin practice and failures (06), the defect table (07), how the 1080p master was really made, with a join command that reproduces it (08), measured facts about the generated audio and loudness targets (12), the originality check (02), timestamp evidence on both sides (05).
- Rule 7 now separates typed text (always in the edit) from a label that exists in a reference image; new rules for clean keyframes, agreeing first and last frames and one-attempt requests.
- The example plan is labelled as the method applied afterwards, not the generation that made the film.

### Fixed
- `master_prompt.py`: micro-actions always said "His"; it now follows `possessive` or `owner`. The credited lineage (Bambi, Snow White, Tyrus Wong) and Peter Pan are blocked in prompts. A storyboard count different from the shot count, and more reference images than the surface takes, are caught. `music_in_generation` drops "No music." for a one-pass film with its own score.
- `qa_take.py`: black frames and the audio sample rate are reported; the face checklist follows the planned order (eyes, eyebrows, mouth).
- `animatic.py`: shot lengths are rounded on the running cut time, so fractional durations no longer drift.
- `project.py verify`: a 1080p or 9:16 deliverable can declare its own size instead of failing against the draft master.
- `pencil_animatic.py`: keeping pink shapes as character is now opt-in (`--keep-pink`); before, pink flowers or skies in any film became character lines.

## [0.1.0] - 2026-10-23
### Added
- Skill `hand-drawn-2d-animation`: six-step workflow from story interview to one-pass generation, QA and 1080p finishing.
- References for the story bible, shots and storyboard, acting, master prompt, generation, QA, finishing, depth map, pencil animatic, breakdown reel, sound and credits.
- Local scripts: prompt checker and builder, animatic, take QA, fidelity check, timing chart, pencil animatic, breakdown reel, lettering, layer compositing, project init.
- BOLHAO example plan and generated master prompt.
