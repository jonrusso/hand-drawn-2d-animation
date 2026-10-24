# Finishing in 1080p

Keep the approved draft as the reference. What 1080p fixes and what it does not: thin glasses rims, feathers, fingers and small label text soften at 480p and come back at 1080p; morphs, axis jumps, a pop without a cause and a glassy splash come from the prompt and the keyframes, and no resolution fixes them.

## Four routes, from cheapest
1. **Draft mode, if your surface exposes it.** Some APIs return a draft id from the 480p job and render the final at 1080p from it, inheriting prompt, references, seed and audio, so the approved motion survives (third-party docs describe drafts expiring after 7 days). It was not confirmed in the CapCut plugin used for BOLHAO; check before relying on it.
2. **Conventional upscale** of the approved file (for example the editor's quality enhancer). Keeps content and timing, cannot recover missing detail. 480p to 1080p is 2.25x per side. Test the hardest 3 s first (glasses, feathers, fingers, label text), then run `fidelity.py`: a faithful upscale stays at a mean difference of about 3 or less. The audio comes from the approved timeline and never passes through the upscaler.
3. **AI super-resolution.** Can recover plausible detail, but may also change lines and letters. Compare with `fidelity.py` and by eye.
4. **Regeneration at 1080p with the approved draft as video reference.** A new roll: detail, hands and small timings can change. This is what BOLHAO did, below.

## How the BOLHAO master was made
- The approved take: 480p, 30 s, Seedance 2.5, one pass. Seedance 2.5 in CapCut offered only 480p and 720p up to 30 s; Seedance 2 offered 1080p up to 15 s, so the film was regenerated as **two 15 s acts on Seedance 2 at 1080p**, each with its own 480p act as the video reference.
- The seam sits at a story beat (15.04 s, frame 361). Act 2 was trimmed so the master has exactly 720 frames.
- **Generated audio was excluded.** The two acts came back with different mixes (7.2 LU apart, see [sound](12-sound.md)); the master carries the approved take's continuous audio, copied without re-encoding and checked by packet hash.
- Checks that passed: all 720 frames decode, every cut lands on the same frame as in the approved take, the audio hash matches. Visual result: composition and story kept, not a pixel-identical copy, so the full visual review (the seam from 14 to 16 s, hands, faces, grounded feet, the bubble, the label) stays mandatory.
- A depth map could not ride along at full length: on Seedance 2 in CapCut a 15 s original plus a 15 s depth video exceeds the roughly 15 s total for reference videos. Pair shorter clips, or use depth with colour stills.

Join the acts by frame count, never by container duration (that is where the black frame came from), and take the audio from the approved take:
```sh
ffmpeg -i act1_1080p.mp4 -i act2_1080p.mp4 -i approved_480p.mp4 -filter_complex \
  "[0:v]trim=end_frame=361,setpts=PTS-STARTPTS[a];[1:v]trim=end_frame=359,setpts=PTS-STARTPTS[b];[a][b]concat=n=2:v=1:a=0[v]" \
  -map "[v]" -map 2:a -c:v libx264 -crf 16 -pix_fmt yuv420p -c:a copy -t 30 final_1080p.mp4
```
Replace 361 and 359 with your seam frame and the remaining frame count.

## Check after finishing
```sh
python3 scripts/qa_take.py final_1080p.mp4 plan.json qa_final/      # cuts on the same frames, no black frame
python3 scripts/fidelity.py draft_480p.mp4 final_1080p.mp4 out/      # where the finish drifted
python3 scripts/project.py verify my-film                            # declare {"width": 1920, "height": 1080} on the deliverable
```
`fidelity.py` compares synchronized frames. After an upscale the number is a test; after a regeneration it only points where to look, because every frame differs a little. No single threshold proves artistic fidelity. Compare cuts, foot contact, faces, hands, text, the bubble, the layout and the audio by eye.

Capabilities differ by model and change over time: check the connector before planning the finish.
