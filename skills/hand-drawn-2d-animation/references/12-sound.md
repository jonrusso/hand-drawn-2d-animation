# Sound

- **One master music track for the whole film,** with known origin and licence, independent from any clip generated in blocks. Never paste two different generated scores together and call it continuity. A whole film generated in one pass has one continuous score; it can be the master (BOLHAO used it), as long as the picture edit keeps its timing.
- In block generations ask only for ambience and contact sounds, no music. That does not guarantee a clean stem; inspect.
- Separate music, ambience, foley and voice. Analyse the real track; do not infer tempo from the prompt. Place cues on frames: anticipation, push, landing, discovery, blow, pop, splash, reaction, sting.
- A comic ending: build the expectation, leave room to perceive, then punctuate the reaction. Do not cover the expression with an accent before the audience understands it. Embarrassment, never humiliation.
- Review music alone, effects alone, and the mix against picture. Check attacks on the frame, ambience changes at cuts, clipping, and a truncated ending. Any re-edit means re-checking accents.
- Social posts: a reference song used as a guide in the edit is not a licence. Pick licensed music in the platform, or use your own track. Branded or sponsored posts may not get the platform's music library.

## What the generated audio really is (measured on BOLHAO)
- **One mixed track per video,** not stems. Left and right are almost the same signal (correlation 0.95 to 0.99), so splitting the channels separates nothing.
- **The sample rate limits the sound.** The 30 s Seedance 2.5 pass came at 32 kHz, so nothing above 16 kHz exists: everything above about 15.4 kHz was missing and the mix sounded muffled. Converting to 48 kHz adds no highs. `qa_take.py` reports the rate.
- **Two acts generated apart are two different mixes.** The 15 s acts differed by 7.2 LU in loudness, about 10 dB in stereo width and 9 to 13 dB in brightness at 4 to 12 kHz. A crossfade at the seam only blends two full mixes for a moment; it does not make one score. Use one continuous source across the seam.
- **Source separation is a diagnostic.** HTDemucs splits music into drums, bass, other and vocals; on cartoon effects, water and ambience it leaks. Use its stems to find and lift a single event (a chew, a blow, a contact), compare with the original mix, and never declare the native stems recovered.
- Decode to PCM WAV for editing; it avoids another lossy pass but does not undo the source's AAC.

## Mix
1. **Score first.** One continuous track locked to the picture cut and approved alone: enters on the discovery, rises with the magic, stops at the pop, a short silence in the bedroom, returns on the end card and resolves before the last frame (the final hit no later than 0.8 s before the end, with its tail).
2. **Then effects on the score's grid:** one ambience per place, contact foley on the frame of contact (paper, chews, blows, the pop on the frame of contact with the branch, the splash on the frame of entry, fabric at the cut to the bedroom).
3. **From block generations use only contact foley,** never their music, risers or pseudo-voices.
4. **Targets for Reels:** about -14 LUFS integrated, -1 dBTP true peak, LRA near 6 LU. BOLHAO's first cut measured -21.3 LUFS, LRA 10.2 LU, with holes down to -36.7 LUFS before the splash and -41 to -49 in the bedroom.
5. Deliver stems as WAV 48 kHz 24-bit when they exist, plus the mixed preview. Say which tracks are truly separate and which are one mixed track.
6. **Listen on the director's own chain** and on speakers. A Bluetooth headset in microphone mode sounds muffled and will mislead the review.
