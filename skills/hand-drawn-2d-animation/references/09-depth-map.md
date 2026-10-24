# Depth map pass (local, free)

A depth map of the finished film is useful twice: as a striking comparison band in breakdown videos, and as an extra spatial reference when regenerating at higher resolution.

## Tool
[Video Depth Anything](https://github.com/DepthAnything/Video-Depth-Anything), **Small** model. Code and the Small checkpoint are Apache 2.0; the Base and Large checkpoints are non-commercial (CC BY-NC 4.0). Use Small for any commercial work.

Measured on BOLHAO: 720 frames (30 s at 24 fps) processed in about 2 minutes of inference and writing on an Apple M-series GPU (PyTorch MPS, FP32). Zero credits.

## Command
```sh
python3 scripts/depth_map.py ~/src/Video-Depth-Anything film.mp4 depth_out/ --cuts 0,46,105,146,179,553,656,720
ffmpeg -framerate 24 -i depth_out/depth_%04d.png -vf scale=1920:1080 -pix_fmt yuv420p depth.mp4
```
`--cuts` are the frame boundaries of the real shots of your film, from 0 to the last frame (the list above is BOLHAO's; take yours from the real cuts that `qa_take.py` reports, times the fps). The script writes 16-bit PNGs, the raw float32 values per shot, a comparison still per shot and a manifest with the source and checkpoint hashes, the upstream commit and the timing. It reuses finished shots if it is run again. The BOLHAO run used upstream commit 4f5ae23172ba60fd7bc11ef671cca678842c7072 and input size 518.

## Procedure
1. Start from the approved film. Record its hash, fps, duration and real cuts.
2. **Reset the temporal state at every real cut.** Never smooth depth across a cut.
3. Keep raw float32 values and 16-bit PNGs. For the visible video: white near, black far, **fixed contrast per shot** (for example 1st and 99th percentile of the shot), not per frame, so the map does not pump.
4. Keep the synchronized RGB alongside. Depth has no colour, face, letters or audio.
5. Inspect silhouettes, occlusions, transparency and stability. Known artefacts: printed text becomes false relief; a transparent bubble gets an estimated surface. It is relative inverse depth, not metres and not a true Z channel.
6. A 1080p depth video made from a 480p source is a spatial resample; it does not recover detail.

## Using depth in a generator
If the video tool only accepts images or videos as references (no dedicated depth or ControlNet input), depth goes in as a visual reference next to the colour references. That can help structure, but it is not a proven geometric lock. Check the total reference duration limit: an original clip plus its depth clip can exceed it.

## Alternatives
Depth Anything 3 Small/Base and Depth Anything V2 Small are also Apache 2.0 (per-frame models can flicker). Some temporal depth models restrict commercial use; read each license.
