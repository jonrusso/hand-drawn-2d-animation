# Step 4 · The master prompt

The video prompt is assembled from `plan.json` by `scripts/master_prompt.py build`, never written or patched by hand. If something is wrong, fix the plan and rebuild.

## Anatomy, in order
1. **Style.** One paragraph of technique: hand-drawn 2D storybook animation, warm pencil outlines, flat colours, no shading on faces, painterly backgrounds, dark foreground leaves, softer distant layers, light direction, aspect ratio.
2. **References, one role each.** `@Image1: only the boy's face, hair, glasses, outfit and proportions`. `@Image2: only the look of the companions`. `@Image3: only the gum pack design and label, which never change`. A reference that tries to do two jobs does neither.
3. **Identity.** One line per character, with the finger sentence in words.
4. **Keyframes.** `Use @Image4 to @Image9 in order as keyframes, one per shot; they guide composition and pose, they are not panels to animate.`
5. **Camera contract.** `Exactly 6 shots joined by motivated hard cuts, no other cuts, no jump cuts. Each shot keeps a gentle drift, never a frozen frame.` Plus screen direction.
6. **Shots.** For each: setup and move; action with counts; `Because X: first ..., then ..., then ...`; `On screen at end: ...`; `Cut to shot N as ...`.
7. **Acting paragraph.** See [acting](04-acting.md).
8. **Limits.** `No dialogue, speech or voice. No text or watermark. Water and bubble are soft drawn shapes. Same identity and proportions in every shot.`
9. **Sound.** Ambience and contact sounds, ending in `No music.` A whole film in one pass may carry its own score instead (`"music_in_generation": true`): one pass gives one continuous score, which BOLHAO used as its master track. Separate blocks never do; their scores do not stitch.

## Plan fields that change the prompt
| Field | Default | Effect |
|---|---|---|
| `possessive` (plan) or `owner` (micro-action) | `His` | "Her right hand tears the wrapper once." |
| `music_in_generation` | false | drops `No music.` from the sound line |
| `use_timestamps` | false | adds `[0-6s]` ranges to each shot |
| `max_reference_images` | none (warns above 9) | errors when the plan attaches more images than the surface takes |
| `char_limit` | 4000 | errors above it; confirm the real limit on your surface |

Storyboard keyframes must be one per shot: the prompt says "one per shot" and the checker refuses a different count.

## What the checker rejects
- A shot with hands but no explicit finger count ("exactly five fingers on each hand, four fingers plus one thumb").
- A face with no cause, or with fewer than two parts in the order.
- An incomplete micro-action (hand, object, verb, count).
- A cut without a trigger.
- The same camera setup twice in a row; a broken screen direction.
- Words that turn drawn effects into glass or metamorphosis.
- Film, studio or director names.
- A prompt above the generator's character limit.

It also warns on high shot density, micro-actions without counts, and micro-actions in wide shots.

## Timestamps
Timestamps in the prompt ("0-3s: ...") are off by default, and the evidence is split:
- For: the approved BOLHAO take is a 30 s pass of a prompt with contiguous whole-second ranges, and long-generation guides recommend them because, without them, action bunches at the start.
- Against: a note from the same production's short per-shot takes records that time ranges made actions alternate in turns, and the director's rule for those takes was no timestamps. That is why the default is off.

Run the A/B before a long single generation: the same plan built with and without timestamps (two 15 s generations are enough), and keep the one whose cuts `qa_take.py` finds on time. Record the result in the manifest.

## Examples
- `assets/examples/bolhao_v03_integral_prompt.txt`: the v03 integral prompt published with the film. It is the prompt family that produced the approved take (the exact text of the approved revision is not in the project files). It uses time ranges, a generated score and the product shot inside the generation, and has 4,142 characters, so the 4,000 default of `char_limit` was not the generator's real limit.
- `assets/examples/bolhao_30s_plan.json` and the prompt it builds, `assets/examples/bolhao_30s_prompt.txt`: the same story rewritten with this method, six shots, 3,996 characters, passes the checker. It has not been generated yet; treat it as the template, not as proof.

## Never in the prompt
- Names of films, studios or directors. Describe the technique instead.
- Text, logos or packshots you want on screen. Add them in the edit.
- A long list of negatives instead of a clear positive instruction. Fix structural ambiguity first.
