# Step 5 · One generation in CapCut

Spend video credits only now, once, with everything decided.

## Setup
- **Model and mode:** Seedance inside CapCut, the mode that accepts several references (often called Omni or universal reference). Story bible first, one reference per role, then the keyframes in story order.
- **Draft first:** 480p and a fixed 16:9 ratio. The draft is where you judge acting and cuts. If a fixed ratio keeps failing, try Auto ratio once and record it.
- **Length:** the whole film in one pass when the model accepts it (Seedance 2.5 accepted 30 s at the time of writing). Otherwise split into narrative blocks of about 10 to 15 s that end at a natural cut, never in the middle of an action.
- **Driving the plugin from an agent:** an agent (for example Codex or ChatGPT with the CapCut plugin) can build the request, attach references and poll the job. It must keep the generation id, never resubmit a job already sent, and wait for a terminal state before downloading.

## Cost and consent
Check the price in the connector at the time of the job; prices, resolutions and maximum durations change. Quote it to the user and wait for an explicit yes. Record per job: quote, generated and used duration, attempts, credits settled, accepted seconds, and the defect that triggered any revision. Count rejected attempts too. Cost per accepted second is undefined if nothing was accepted.

Historical reference from the BOLHAO production, not a price list: a 30 s draft cost 2,880 credits and a 4 s repair cost 384. That pair does not prove that a method saves a fixed percentage.

## What stays out of the generation
Text, logos, packshots and music. They go in the edit.

## Choosing a strategy
| Strategy | Good for | Risk |
|---|---|---|
| Whole film in one pass | consolidated direction, speed | a new attempt can change every shot |
| Narrative blocks | protecting approved acts | needs continuity at entries and exits and one master music track |
| Localized repair | fixing one shot or insert of an approved film | needs a natural cut to hide the seam |

If the same defect appears in two attempts, stop and diagnose: change staging, reference, beat length or method. More negatives in the prompt are not a fix.
