# Credits and style lineage

## Visual inspiration
The look this skill aims for was studied from the hand-painted feature animation of Walt Disney Animation Studios:

- **Tyrus Wong** (1910 to 2016), the Chinese American painter whose atmospheric, impressionistic inspirational paintings defined the look of Disney's *Bambi* (1942): soft painted forests, selective detail, mist and light carrying the mood, the character set into a calm painted world. He is the main reference for this style.
- The hand-painted backgrounds and storybook warmth of Disney's *Snow White and the Seven Dwarfs* (1937).

They are credited here because this is where the style comes from. The skill never puts film, studio or artist names in generation prompts, ships no frames or characters from those films, and describes only technique: soft pencil line, flat character colour, painterly backgrounds, dark foreground, soft distance, light living in the world. This project is not affiliated with or endorsed by Disney.


### Intellectual property
- This repository contains no artwork, frames, characters or audio from Tyrus Wong or Disney. Only their names appear, as credit.
- The licenses of this repository (Apache 2.0 for code, CC BY 4.0 for docs and our own example images) cover only our own material. They grant no rights over anyone else's work.
- Studying and describing a style is fine. Reproducing protected characters, frames or designs is not, whether the use is personal or commercial.
- When you share work made with this skill, keep the credit to the inspiration and keep the prompts free of film, studio and artist names.

## Tools
CapCut, the ChatGPT plugin for CapCut, Codex and Seedance were used to plan, prompt and generate the example film (BOLHAO). Check each provider's current terms for commercial use of generated output.

## Open source
| Project | Use | License |
|---|---|---|
| [Video Depth Anything](https://github.com/DepthAnything/Video-Depth-Anything) | depth map pass (Small model) | Apache 2.0 (Small only; Base/Large CC BY-NC 4.0) |
| [Anime2Sketch](https://github.com/Mukosame/Anime2Sketch) | line extraction for the pencil animatic | MIT |
| [anime-segmentation / isnet-anime](https://github.com/SkyTNT/anime-segmentation) | character mask | Apache 2.0 |
| [PyTorch](https://pytorch.org) | model runtime | BSD-3-Clause |
| [ONNX Runtime](https://onnxruntime.ai) | mask runtime | MIT |
| [OpenCV](https://opencv.org) | contours | Apache 2.0 |
| [FFmpeg](https://ffmpeg.org) | video I/O, timing checks | LGPL 2.1+ |
| [Pillow](https://python-pillow.org), [NumPy](https://numpy.org) | images, timing charts, lettering | HPND, BSD-3-Clause |

## AI-generated examples
The example images and plan in `assets/examples/` were made with AI image and video tools under human direction. They are offered under CC BY 4.0 to the extent they are copyrightable.
