# Step 3 · Shots, storyboard and animatic

## Contents
1. Shot density and scale
2. What every shot needs
3. Colour script
4. Storyboard keyframes
5. Animatic and timing
6. Exposure sheet (X-sheet)
7. Commands

## 1. Shot density and scale
The shot list is the contract. For 30 seconds of acting, plan **3 to 7 shots, about 4 to 6 seconds each**. Below 3 s a shot, video models skip or shuffle actions. Measured on hand-drawn features, the median shot is about 4.6 s, with half of all shots between 3 and 6.6 s; comedy cuts faster (about 3.3 s median). If the piece needs a faster comedy rhythm, cut faster in the edit by trimming the approved take, never by asking the generator for more shots.

Target mix for six shots: 2 wide (place and arrival), 3 medium (action and hand business), 1 close or insert (the emotion or the hand). Faces and hands never depend on a wide shot: at draft resolution the face disappears. Hand micro-actions only in medium shots or closer.

After a climax, a longer held shot of 6 to 8 s lets the moment land.

These are planning targets, not limits. The approved BOLHAO take has seven shots: three under 2.5 s (the grab and a close insert of the same hands, cut on the action) and one continuous 15.6 s shot that carries the bridge, the flight, the pop and the fall in one camera move. Short shots hold when they continue one action across the cut; a long shot holds when the geography never changes inside it.

## 2. What every shot needs

| Field | Example |
|---|---|
| place | mossy stump at the lakeshore |
| camera | medium shot, slow push-in. Never the same setup twice in a row |
| screen direction | outdoors he always moves left to right |
| action | his right hand tears the end of the wrapper once |
| micro-actions | hand, object, verb, count |
| face | because the first taste surprises him: first his eyes widen and dart up, then one eyebrow lifts higher than the other, then lips closed, chewing twice |
| end frame | cheeks full, wrapper in his left hand |
| cut out | cut to shot 3 as he draws a deep breath |

The face is always: a cause, then eyes, then eyebrows, then mouth. Asymmetry (one eyebrow higher) and a half-beat late reaction read as alive.

Hands in wide shots stay busy or still: holding something, in pockets, behind the back. Never gesturing. Describe grips with fingers together ("fingers wrapped together around the cup, thumb on top"), never "spreads his fingers": every separate finger on screen is another chance to miscount.

## 3. Colour script (optional)
Each shot may carry `light` (bright, medium, dark) and `temperature` (warm, neutral, cold). Write the arc before generating. Example: warm and bright in the forest, cooler over the lake, warm morning in the bedroom. The climax can darken; the end brightens. Two consecutive shots in the same place must not jump in brightness without a reason; `qa_take.py` measures it.

## 4. Storyboard keyframes
One keyframe per shot, generated with the story bible attached as references and the same style and character blocks as the video prompt (`master_prompt.py storyboard` writes these prompts). Each keyframe becomes that shot's guide in the generation ("Use @Image4 to @Image9 in order as keyframes, one per shot; they guide composition and pose, they are not panels to animate").

## 5. Animatic and timing
Put the keyframes on the timeline at their real durations with a guide track and play it at full speed. Fix rhythm here, where a change costs nothing. `animatic.py` builds it automatically from the plan.

An animatic proves rhythm and staging; a slideshow does not prove the animation works. More panels do not force a generator to obey them all.

## 6. Exposure sheet (X-sheet)
One row per drawing change, master at 24 fps. Columns: frame, time, action beat, thought (without it the pose is empty), type (key, breakdown, in-between, hold), drawing code, exposure (1, 2, 3 or hold length), eyes (target and blink; eyes arrive before the head), mouth, hands and contact (which point stays fixed), secondary (hair, cloth, steam, and on which drawing it starts), camera, sound, note.

Rules:
- Fill it before generating. It is the contract the model will not keep by itself; it writes the beats of the prompt and checks the result.
- Density varies inside a gesture: calm action can sit on threes, the peak on twos, ones only for very fast action (jump, fall, startle).
- Every hold longer than 8 frames needs a written reason in "thought". Otherwise it is a dead frame.
- `timing_chart.py` renders the exposure as an animated overlay (frame ruler, circled keys, breakdowns, exposure brackets, cursor) for breakdown videos.

## 7. Commands
```sh
python3 scripts/master_prompt.py check plan.json
python3 scripts/master_prompt.py storyboard plan.json storyboard/
python3 scripts/animatic.py plan.json storyboard/ animatic.mp4 guide_track.wav
```
