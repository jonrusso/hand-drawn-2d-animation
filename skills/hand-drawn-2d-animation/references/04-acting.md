# Acting that feels human

These rules separate a cartoon that breathes from an AI clip that floats. They come from frame studies of hand-drawn feature films and from production notes; this file keeps only the technique, no frames or characters from those films. Write the rules into each shot in plain words.

## The rules
1. **Acting comes from everyday life.** Eating, drinking, waiting, getting tired, taking care of someone. Every scene gets a small physical task (spoon, mug, paper, bucket) that the character does while thinking.
2. **Children copy and get it wrong first.** They repeat another character's gesture a moment later and miss the first time: whole fist on the spoon, both hands on the cup, the whole arm raised.
3. **Age lives in amplitude.** A child reacts with the whole body; an adult with eyebrows, head and mouth. In a shot with both, the contrast is mandatory.
4. **The listener acts.** Give reaction beats to whoever is listening, each one different from the last.
5. **One physical mistake per sequence.** A stumble, a fall, an object too big, sleep winning in the middle of a meal. The mistake shows weight and a real body.
6. **Received weight.** When someone jumps on, hugs or hands over something heavy, the other one steps back, bends or loses balance.
7. **The hold comes after the action, and it is alive.** Blink, breath, hair settling. A hold longer than 8 frames without a written reason is a dead frame.
8. **Scale tells the story.** Furniture and objects bigger than the child: chin at table height, a mug the size of the face.
9. **Flat character, light in the world.** Flat colour, no cel shadow on the face, soft blush. Lamp and sun live in the background, in effects and in a light layer. The identity colour never changes.
10. **Water, steam and bubbles are drawn.** Closed masses in 3 or 4 tones with an outline, foam as shapes, a few big drops. Never glass, ice or photographic fluid.
11. **Objects are landmarks.** Functional objects stay in the same place from every angle and tie the geography together.
12. **Food and desired objects are heroes.** More detail and colour than the rest of the frame, and a moment of waiting before use.
13. **Hand line, not machine line.** Slightly thick, free pencil line, few lines per shape, brown and coloured per area.
14. **Observed behaviour of real people.** The acting repertoire comes from observing a real person of the character's age, not other cartoons.
15. **Nothing slides as one piece.** A big moving object (boat, wave, bubble) is redrawn along its path; a single image dragged across the screen gives the cut-out away.
16. **Density varies inside the gesture.** Calm action needs fewer drawings; the peak of the gesture needs more.
17. **The emotional peak can be quiet.** After a climax, a still, alive wonder (eyes open and still, small mouth, one slow blink) weighs more than a grimace.
18. **A hand on the face expresses without opening the mouth.** Rubbing an eye, covering the face, peeking through fingers. In video models this avoids an open mouth that turns into a voice.
19. **Comedy is contrast.** A big reaction next to a small one; the calm child in the middle of the adults' panic.
20. **Caricature is for secondary adults.** The hero stays on model.

## The acting paragraph for video prompts
Paste into any shot with a face, adapting the action. No timestamps, no dialogue.

```text
He acts like a real child, not a performer: his whole body joins every feeling, he grips things with his whole fist, uses both hands for anything heavy, copies what the other person just did a moment later, and gets one small thing physically wrong before getting it right. Between actions he never freezes: he breathes, blinks, his eyes reach the next target before his head turns, and his hair and feathers settle a moment after he stops.
```

## Reviewing a take (questions in order)
1. What physical task does the character do in this shot?
2. Where is the imitation, the mistake or the received weight?
3. Does the listener react, and does the reaction change beat to beat?
4. Is there a hold over 8 frames without a reason?
5. Does the amplitude of the gesture match the age?
6. Is the face flat, with the light coming from the world?
7. Are water, steam and bubbles drawn, with no glass?
8. Do functional objects stay in place between angles?

A "no" without a reason becomes a correction in the prompt or the X-sheet before generating again.

## Limits
Frame studies at about two captures per second cannot measure exposure or spacing. "Threes for calm, twos at the peak" is a hypothesis to test on a pilot shot, not a contract. Video models follow these rules as intention, not as a guarantee: check the result frame by frame.
