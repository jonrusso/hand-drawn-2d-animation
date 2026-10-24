# Breakdown reel for social (9:16)

A proven structure for a 30 to 35 s vertical breakdown:

| Block | Time | Layout |
|---|---|---|
| Comparison | 0 to 8.5 s | three stacked synchronized 16:9 bands: depth map, final, animatic |
| Process | 8.5 to about 23.5 s | two bands that swap every few seconds: character sheet and storyboard (with an animated timing chart), previz and pose guide, the editor screen recording with a brand frame, stills with the model names |
| Story | to the end | the film, cut to land on the story beat (for BOLHAO: the bubble pops, he falls in the lake) |
| Call to action | after the beat, about 5 s | a hard cut to a clean card, keyword in brand colours, a short exit animation |

## Rules learned the hard way
- **Text stays editable.** Labels, lettering and CTA go out as native editor text, captions (SRT) or a motion graphics template, never burned into a video or a PNG.
- **Instagram side crop.** On tall phones, Reels fills the screen and crops roughly 97 px from each side of a 1080 px frame. Keep every text between x = 120 and x = 960. Keep text above about y = 1580 for the caption and profile overlay.
- **The CTA enters on a hard cut at the story beat.** No dissolve, no music fade. If it needs more time, extend after the cut and extend the music with it.
- **Labels in a clean sans, small, bottom-left of each band, with a soft shadow and no box or pill.**
- **No camera moves on the bands.** Movement comes from the content: animated timing charts, swapping panels, held drawings.
- **Timing checks:** no black frame at seams, no static hold over half a second (`ffmpeg` blackdetect and freezedetect).

## Scripts
- `scripts/breakdown_reel.py config.json` builds the stacked bands, labels and overlays, and writes an FCP7 XML (imports in Premiere and other editors) plus a preview render.
- `scripts/timing_chart.py` renders the exposure-sheet overlay with alpha.
- `scripts/lettering.py` renders frame-by-frame lettering previews (rise with blur, pop with overshoot, typewriter, staggered exit). For delivery, rebuild the same animation as editable text.
