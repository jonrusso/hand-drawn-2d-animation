# Step 6 · QA and repair

## Automatic pass
```sh
python3 scripts/qa_take.py take.mp4 plan.json qa/
```
It compares real cuts with planned cuts (0.5 s tolerance), flags extra cuts (dissolves, jumps), frozen stretches over 8 frames, black frames, audio drops, and brightness or temperature jumps between shots in the same place. It reports the frame size and the audio sample rate: native audio below 44.1 kHz is band-limited and works only as a foley guide. It writes one sheet per shot and the frames before and after every cut.

## Human pass
Watch once at full speed, then frame by frame at every cut.
- [ ] Five fingers on every visible hand; a hidden hand is not a missing hand. Child hands smaller than the face.
- [ ] The face changes in the planned order.
- [ ] Every cut has its trigger, and there are no extra cuts.
- [ ] No frozen frame over a third of a second without a reason.
- [ ] Water and bubbles look drawn, not glassy; a splash never reverses.
- [ ] Objects stay in place between angles; feet in contact do not slide; companions keep their sides.
- [ ] The background is a layout: trees, ground and horizon do not redraw because the character changed pose.
- [ ] One watermark at most, the one the export adds; none drawn inside the picture.
- [ ] Every word on screen, read letter by letter against the script: labels, taglines, signs. Generated text misspells.
- [ ] Typed text: every accented capital (Ç, Ã, É) renders in the same font. Type them in the font and check at 100% before applying.
- [ ] Vertical crop, if the film will play in 9:16: hero, bubble and tagline survive a centre crop (x from 293 to 563 on an 856-pixel-wide frame).
- [ ] Sound: the gag lands, nothing is truncated at the end.

Classify each shot as approved, partly usable or rejected. A sampled contact sheet does not prove anatomy in every frame.

## Repair ladder (in this order)
1. **Edit.** Trim, hold or match the cut on the timeline.
2. **Edit the segment.** If the connector exposes it: "Edit @Video1: between 0:12 and 0:15, ..., keep everything else unchanged", one change at a time.
3. **Regenerate one shot.** Use clean frames from the approved take as its first and last frame, rebuilt as stills without the watermark.

Never regenerate the whole film for one local defect. Never hide a physical error with a dissolve. After a fix, re-check only the dependent shots.

## Defects found in the BOLHAO production
Each row is a symptom seen on screen, its cause and the fix that worked or was prescribed.

| Symptom | Cause | Fix |
|---|---|---|
| The end tagline reads "A imaginação tambên" instead of "também", in the approved draft, the 1080p regeneration and the delivered master | the generator drew the tagline itself, and nobody read it letter by letter | typed text in the edit; in QA, read every word on screen against the script |
| Bubble deflates instead of popping | the beat was not written as a pop | a 4 s localized repair: contact with a branch, pop, reaction, fall, drawn splash |
| One-frame black gap where two acts join | the video stream was shorter than its container | join on the shorter of the two; `qa_take.py` lists black frames |
| One second of morph, then the hero and companions swap sides | first and last frame disagree (companions present in one, absent in the other) | split the take; companions present and on the same side in both frames |
| Two ghost watermarks drift in a corner | keyframes taken from a generated video | keyframes only from clean image stills |
| Adult hands on a child | the insert keyframe had adult hands; a hands-only insert has no face to anchor age | new keyframe with child hands; three-quarter medium with face and hands |
| Cut from the walk straight to opening the gum | the reach and grab were never asked for | the next take opens on the grab ("ALREADY kneeling, hand ALREADY on the piece") |
| Splash turns to glass, then to a cone; the boy vanishes in one frame | splash keyframe already glassy; liquid described as a mass | "glossy, wet, soft" shapes, a one-way sentence, the boy disappears only under the foam |
| Water sprite rises out of the ground like goo | the prompt never said where it comes from | "rises out of the lake, never out of the ground" |
| A log pops out of the water, the shore changes shape | the bridge had no visible cause | lily pads rise under each step, lifted by the sprite |
| Companions vanish, flowers shrink to a few lotus | bridge, flight and flowers asked for in one 6 s take | one transformation per take |
| Bubble pops with no cause and no reaction, 11 frozen frames | the pop beat was not in the take | contact, pop, wide eyes, brief hang, fall |
| Frozen stretches of 16 to 36 frames, eyes closed in the blow | takes longer than their action, no beats, no eye life | shorter takes ending on a beat; "eyes open, moving between targets" |
| 14 frozen frames and 0.4 s of silence at the start | the model starts slowly | trim the head; ambience starts on frame 0 |
| Damp patch on the blanket reads as a shadow | no outline on the patch | "clearly darker damp patch with a soft wet outline" |
| Tagline shows lower-case accents from another font | the font had no Ç, Ã, É capitals | test the glyphs in the font before applying |
| Packshot is a 100% still image for 2.8 s | the end card was a still | a slow push from 100% to 103%, or a separate breeze take with the pack locked |
| Three scores in 30 s, everything above 15.4 kHz missing | music stitched from blocks; native audio at 32 kHz | one continuous score; native audio only for contact foley |
| Takes come out 852 and 856 pixels wide | Auto ratio | lock 16:9 or conform every take to one size |
| Ones in some takes, frozen stretches in others | prompts do not control exposure | do not fix by prompt; judge only in the finished film |
| Paper left on the ground, hands missing while opening leaves | not written as micro-actions | explicit micro-actions with hand, object, verb and count |
| Feet sliding, geography changing on a bridge, a scene change mid-breath | too many events per generation | fewer events per take and a fixed layout |
