# Step 5 · One generation in CapCut

Spend video credits only now, once, with everything decided. The numbers below were observed in the BOLHAO production in October 2026; plugins, models and prices change, so check them in the connector at the time of the job.

## Setup
- **Model and mode:** Seedance inside CapCut, the mode that accepts several references (often called Omni or universal reference). Story bible first, one reference per role, then the keyframes in story order. In the plugin version used, a job took either first and last frame or Omni references, not both.
- **Draft first:** 480p, 16:9. A fixed 16:9 request failed four times in a row (credits returned, no error code); Auto ratio with a single attempt went through and returned 852x480. Auto gave 852 and 856 pixel widths between takes, so conform every take to one size in the edit and record the ratio in the manifest.
- **Length:** the whole film in one pass when the model accepts it (Seedance 2.5 accepted 30 s at the time of writing). Otherwise split into narrative blocks of about 10 to 15 s that end at a natural cut, never in the middle of an action.
- **References:** Seedance 2.0 takes at most 9 images; on Seedance 2 in CapCut the reference videos added up to about 15 s in total. Set `max_reference_images` in the plan for your surface.

## First and last frame
- **Both frames must agree:** same characters present, on the same sides, same scale, light and set. A 6 s take that started with the boy alone on the shore and ended with him flying with two companions spent a second morphing, translucent and warped, then jumped the axis: the boy and both companions swapped sides. Another take with mismatched frames dissolved the tree stump into a new composition and was rejected after 576 credits. If the frames cannot agree, use the first frame only.
- **Open with "ALREADY":** "Opens on the start frame: he is ALREADY kneeling by the stump, his right hand ALREADY on the gum piece." Then one camera move, the action with cause before effect, and the explicit final position.
- **Expect a slow start and a dead tail.** The opening take sat nearly frozen for 14 frames at the head, with 0.4 s of silence; trim it. A take longer than its action freezes at the end (16 and 28 frozen frames in BOLHAO); end each take on a final beat, such as an idea or a breath, and keep only 0.5 to 1 s of settle to trim.

## Keyframes
- Clean stills from the image tool, 16:9, at the generator's working size (BOLHAO used 1672x941), approved before use.
- Never a frame exported from a generated video: it carries the platform watermark, the model redraws it and the export adds another, so two ghost watermarks drifted on screen for five seconds.
- The keyframe's hands become the take's hands. An insert keyframe with adult hands gave adult hands on a child; a hands-only insert has no face to anchor the age. Prefer a three-quarter medium shot with face and hands together.

## Words that change physics
- **Say where things come from.** The water sprite came out of the ground like goo until the prompt said "rises out of the lake, never out of the ground".
- **Every transformation needs a visible cause first.** A bridge that appears without one becomes a log that pops out of the water and a shore that changes shape. "A lily pad rises flat under each boot, lifted by the water sprite" worked.
- **One transformation per take.** A 6 s take asked for a bridge, a flight and opening flowers; the companions vanished and the flowers shrank to a few lotus in the foreground.
- **Liquids are glossy, wet and soft,** never a block or a solid. A splash described as a mass turned into glass and then a cone. Close the splash with a one-way sentence: "This is the final state: the splash does not fall back and does not reverse."

## Driving the plugin from an agent
An agent (for example Codex or ChatGPT with the CapCut plugin) can build the request, attach references and poll the job. In BOLHAO:
- **One attempt, then stop.** Write it in the request: "Make ONE attempt. On error, stop and report the exact message; do not retry, change model or start other jobs." Without it, the agent resubmitted a failing 16:9 job four times on its own.
- Keep the generation id and the exact link to its card. A job already sent is polled, never sent again; a retry the user authorized keeps the same unique key.
- Wait for a terminal state and for the charge to settle (the card reports no further action) before recording the cost. A hold is not a charge.
- Read the credit balance in one place: the video studio and the design studio showed different balances at the same moment.
- Do not interrupt the agent mid-job: an interruption deleted an (empty) result card.
- "Could not generate. Credits returned." comes without a cause. The plugin chat once blamed copyright and that was never confirmed. Change one thing (ratio, reference or action) and try once more; do not guess.
- Download with the editor's own button and record the real file: a 5 s request returned 5.125 s.
- Before editing the timeline, check the draft state against your local version; if it is stale, read the snapshot and let the user's edits win. Save on the current base and use the readback as the next base. "Saved" does not prove the right cut plays: check order, trims, duration and sound.

## Cost and consent
Quote the price in the connector and wait for an explicit yes. Record per job: quote, generated and used duration, attempts, credits settled, accepted seconds, and the defect that triggered any revision. Count rejected attempts too. Cost per accepted second is undefined if nothing was accepted.

Historical reference from BOLHAO, not a price list: Seedance 2.5 at 480p settled 96 credits per generated second (384 for 4 s, 480 for 5 s, 576 for 6 s, 2,880 for 30 s). Third-party sources put 1080p at about four times 480p. A round of five 4 to 5 s repair takes was estimated at 2,112 credits before any retry. None of this proves that a method saves a fixed percentage.

## What stays out of the generation
Typed text (titles, taglines, captions, CTA) and, for any film made in blocks, music. They go in the edit.

## Choosing a strategy
| Strategy | Good for | Risk |
|---|---|---|
| Whole film in one pass | consolidated direction, speed, one continuous score | a new attempt can change every shot |
| Narrative blocks | protecting approved acts | needs agreeing frames at entries and exits and one master music track |
| Localized repair | fixing one shot or insert of an approved film | needs a natural cut to hide the seam |

Change one thing per attempt and write down why. If the same defect appears in two attempts, stop and diagnose: change staging, reference, beat length or method. More negatives in the prompt are not a fix.
