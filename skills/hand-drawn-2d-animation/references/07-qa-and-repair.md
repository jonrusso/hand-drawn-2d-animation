# Step 6 · QA and repair

## Automatic pass
```sh
python3 scripts/qa_take.py take.mp4 plan.json qa/
```
It compares real cuts with planned cuts (0.5 s tolerance), flags extra cuts (dissolves, jumps), frozen stretches over 8 frames, audio drops, and brightness or temperature jumps between shots in the same place. It writes one sheet per shot and the frames before and after every cut.

## Human pass
Watch once at full speed, then frame by frame at every cut.
- [ ] Five fingers on every visible hand; a hidden hand is not a missing hand.
- [ ] The face changes in the planned order.
- [ ] Every cut has its trigger, and there are no extra cuts.
- [ ] No frozen frame over a third of a second without a reason.
- [ ] Water and bubbles look drawn, not glassy.
- [ ] Objects stay in place between angles; feet in contact do not slide.
- [ ] The background is a layout: trees, ground and horizon do not redraw because the character changed pose.
- [ ] Sound: the gag lands, nothing is truncated at the end.

Classify each shot as approved, partly usable or rejected. A sampled contact sheet does not prove anatomy in every frame.

## Repair ladder (in this order)
1. **Edit.** Trim, hold or match the cut on the timeline.
2. **Edit the segment.** If the connector exposes it: "Edit @Video1: between 0:12 and 0:15, ..., keep everything else unchanged", one change at a time.
3. **Regenerate one shot.** Use clean frames from the approved take as its first and last frame.

Never regenerate the whole film for one local defect. Never hide a physical error with a dissolve. After a fix, re-check only the dependent shots.

## Real defects found in the BOLHAO production
- A bubble that deflated instead of popping: fixed with a 4 s localized repair that showed a fast pop and a drawn splash.
- A one-frame black gap between two acts: the video stream was shorter than the container said. Always join on the shorter of stream and container duration.
- Feet sliding on contact, geography changing on a bridge, a scene change in the middle of a breath: solved by fewer events per generation and a fixed layout.
- Paper left on the ground, hands missing while opening leaves: written as explicit micro-actions in the next plan.
