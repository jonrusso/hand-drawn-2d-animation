# Finishing in 1080p

Keep the approved draft as the reference. Three different operations:

- **Conventional upscale.** Keeps content and timing, cannot recover missing detail. 480p to 1080p is 2.25x vertically.
- **AI super-resolution.** Can recover plausible detail, but may also change lines and letters. Compare.
- **Regeneration at higher resolution with the approved draft as reference** (optionally plus its depth map). Appearance and motion come from the original; depth adds structure. Valid, with no guarantee of an identical result. BOLHAO's final master was regenerated in 1080p as two 15 s acts joined at a story beat, with the continuous master audio kept from the approved edit.

Check after finishing:
```sh
python3 scripts/fidelity.py draft_480p.mp4 final_1080p.mp4 out/
```
It compares synchronized frames so you can see where the finish drifted from the approved draft. Metrics locate changes; no single threshold proves artistic fidelity. Compare cuts, foot contact, faces, hands, text, the bubble, the layout and audio by eye.

Capabilities differ by model and change over time (at the time of writing Seedance 2.5 in CapCut offered 480p/720p up to 30 s, while Seedance 2 offered 1080p up to 15 s). Check the connector before planning the finish.
