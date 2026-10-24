# Pencil animatic from a finished film

For breakdown videos it is powerful to show "the drawings" next to the final film. When the film was generated, the drawings do not exist, so they are made after, from the film. The goal is a believable rough pencil test: lines only, the character detailed, the background reduced to a few strokes, held drawings.

## What did not work (BOLHAO)
- Line extraction straight on the painted film: the busy background turned into busy lines and the character got lost.
- Desaturate and threshold filters: faded, grey, "too many frames per second".
- 24 new drawings per second: real animatics are held drawings.

## What worked
1. **Simplify the shot first.** Make a lighter, sketchier version of the shot (a video edit or restyle pass that keeps the exact motion and timing, asked for "a rough pencil test on plain paper, background reduced to a few light lines"). Video models tend to keep the hero in colour even when asked for graphite; that is fine, the next step removes colour. BOLHAO did this for 8.5 s of film with a Seedance 2.5 video edit on a third-party surface, at 720p without audio, for about 113 credits: it is a paid step, so it needs a quote and a yes like any generation.
2. **Extract lines** with [Anime2Sketch](https://github.com/Mukosame/Anime2Sketch) (MIT) on every kept frame: `scripts/sketch_lines.py`. On a simplified source it returns clean lines on the character and few strokes behind.
3. **Optional character mask** with [isnet-anime](https://huggingface.co/skytnt/anime-seg) from anime-segmentation (Apache 2.0): `scripts/pencil_animatic.py` keeps full line detail inside the mask, closes the outer contour, and keeps only long thin background lines at low intensity. The matte only knows characters; a prop it misses can be kept by colour. BOLHAO passed `--keep-pink` for the pink bubble. Leave it off when the set has pink flowers or a pink sky, or they become character lines.
4. **Hold the drawings:** 12 drawings per second, each held for two frames (or 8 per second on threes for a rougher feel). Pure black lines on neutral white, or dark graphite on a light warm paper.
5. Check that pose and timing still match the film frame for frame.

Weights are not part of this skill. Download them from the upstream projects and pass their path to the scripts.
