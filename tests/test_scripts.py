"""Tests for the skill scripts. Run: python3 -m pytest -q tests

No network, no credits. Media is synthetic (ffmpeg lavfi sources and Pillow drawings).
Requires ffmpeg/ffprobe on PATH and Pillow; numpy, torch and opencv are not needed.
"""
import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path
from xml.dom import minidom

import pytest
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "hand-drawn-2d-animation"
SCRIPTS = SKILL / "scripts"
EXAMPLE = SKILL / "assets" / "examples" / "bolhao_30s_plan.json"
EXAMPLE_PROMPT = SKILL / "assets" / "examples" / "bolhao_30s_prompt.txt"
sys.path.insert(0, str(SCRIPTS))
import master_prompt  # noqa: E402

needs_ffmpeg = pytest.mark.skipif(not (shutil.which("ffmpeg") and shutil.which("ffprobe")), reason="ffmpeg/ffprobe not on PATH")


def run(*args, check=False):
    r = subprocess.run([str(a) for a in args], capture_output=True, text=True)
    if check and r.returncode:
        raise AssertionError(f"{args} failed:\n{r.stdout}\n{r.stderr}")
    return r


def script(name, *args, check=False):
    return run(sys.executable, SCRIPTS / name, *args, check=check)


def ffmpeg(*args):
    run("ffmpeg", "-v", "error", "-y", *args, check=True)


def probe_frames(path):
    r = run("ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
            "stream=nb_read_frames,pix_fmt,width,height", "-of", "json", path, check=True)
    return json.loads(r.stdout)["streams"][0]


@pytest.fixture
def plan():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- master_prompt.py

def test_example_passes_check_and_fits_limit(plan):
    errors, _ = master_prompt.check(plan)
    assert errors == []
    txt = master_prompt.build(plan)
    assert len(txt) <= plan["char_limit"]
    assert "exactly five fingers" in txt and "Cut to shot 2" in txt and "On screen at end" in txt


def test_example_prompt_file_matches_build(plan):
    assert master_prompt.build(plan) == EXAMPLE_PROMPT.read_text(encoding="utf-8")


def test_eight_planted_errors_are_caught(plan):
    r = copy.deepcopy(plan)
    r["characters"]["boy"]["block"] = r["characters"]["boy"]["block"].replace("exactly five fingers", "small fingers")
    r["shots"][4]["action"] += " A glassy splash, Ghibli style."
    r["shots"][1]["cut"]["reason"] = ""
    r["shots"][2]["setup"] = r["shots"][1]["setup"]
    del r["shots"][3]["end_frame"]
    r["shots"][1]["face"] = {"cause": "", "eyes": "happy"}
    errors, _ = master_prompt.check(r)
    assert len(errors) >= 8


def test_hand_bearing_character_needs_exactly_five_fingers(plan):
    r = copy.deepcopy(plan)
    r["characters"]["boy"]["block"] = "The boy from @Image1, small child hands."
    errors, _ = master_prompt.check(r)
    assert any("exactly five fingers" in e for e in errors)
    # a character without hands does not need the statement
    r = copy.deepcopy(plan)
    r["characters"]["companions"]["block"] = "Two tiny spirits."
    assert master_prompt.check(r)[0] == []


def test_four_fingers_without_sheet_approval_fails(plan):
    r = copy.deepcopy(plan)
    r["characters"]["boy"]["fingers"] = 4
    assert any("fingers_approved_on_sheet" in e for e in master_prompt.check(r)[0])


def test_micro_action_in_wide_shot_fails(plan):
    r = copy.deepcopy(plan)
    r["shots"][0]["micro_actions"] = [{"hand": "right", "object": "leaf", "verb": "pushes", "count": "once"}]
    assert any("wide shot" in e for e in master_prompt.check(r)[0])


@pytest.mark.parametrize("name", ["Ghibli", "Miyazaki", "Pixar", "Disney", "DreamWorks", "in the style of",
                                  "Bambi", "Snow White", "Tyrus Wong", "Peter Pan"])
def test_film_studio_director_names_fail(plan, name):
    r = copy.deepcopy(plan)
    r["style"] += f" Like {name}."
    assert any("third-party name" in e for e in master_prompt.check(r)[0])


def test_timestamps_blocked_unless_enabled(plan):
    r = copy.deepcopy(plan)
    r["shots"][0]["action"] += " At 0:03 he stops."
    assert any("timestamp" in e for e in master_prompt.check(r)[0])


def test_micro_action_follows_the_character_possessive(plan):
    assert "His right hand tears" in master_prompt.build(plan)
    r = copy.deepcopy(plan)
    r["possessive"] = "Her"
    txt = master_prompt.build(r)
    assert "Her right hand tears" in txt and "His right hand" not in txt


def test_keyframe_count_must_match_shots(plan):
    r = copy.deepcopy(plan)
    r["references"] = [x for x in r["references"] if x["id"] != "@Image9"]
    assert any("storyboard keyframes" in e for e in master_prompt.check(r)[0])


def test_reference_image_limit(plan):
    assert not any("reference images" in w for w in master_prompt.check(plan)[1])  # nine images: at the hint
    r = copy.deepcopy(plan)
    r["max_reference_images"] = 8
    assert any("reference images" in e for e in master_prompt.check(r)[0])
    r = copy.deepcopy(plan)
    r["references"].append({"id": "@Image10", "role": "only the lake", "file": "lake.png"})
    assert any("reference images" in w for w in master_prompt.check(r)[1])


def test_music_in_generation_drops_no_music(plan):
    assert master_prompt.build(plan).rstrip().endswith("No music.")
    r = copy.deepcopy(plan)
    r["music_in_generation"] = True
    assert "No music." not in master_prompt.build(r)


def test_cli_check_build_storyboard(tmp_path, plan):
    assert script("master_prompt.py", "check", EXAMPLE).returncode == 0
    out = tmp_path / "prompt.txt"
    r = script("master_prompt.py", "build", EXAMPLE, out)
    assert r.returncode == 0 and out.read_text(encoding="utf-8") == EXAMPLE_PROMPT.read_text(encoding="utf-8")
    sb = tmp_path / "sb"
    assert script("master_prompt.py", "storyboard", EXAMPLE, sb).returncode == 0
    assert len(list(sb.glob("SB_*_prompt.txt"))) == len(plan["shots"])
    bad = copy.deepcopy(plan)
    bad["style"] += " Pixar look."
    bad_path = tmp_path / "bad.json"
    bad_path.write_text(json.dumps(bad))
    r = script("master_prompt.py", "check", bad_path)
    assert r.returncode == 1 and "FAILED" in r.stdout


# ---------------------------------------------------------------- qa_take.py and fidelity.py

@pytest.fixture(scope="module")
def synthetic_take(tmp_path_factory):
    """Six flat-color shots with the example plan's durations, plus a tone, concatenated into one take."""
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not on PATH")
    tmp = tmp_path_factory.mktemp("take")
    parts = []
    for i, (c, d) in enumerate(zip(["red", "blue", "green", "yellow", "white", "purple"], [6, 4, 5, 6.5, 3.5, 3])):
        f = tmp / f"c{i}.mp4"
        ffmpeg("-f", "lavfi", "-i", f"color={c}:s=320x180:r=24:d={d}", "-f", "lavfi", "-i",
               f"sine=frequency=440:duration={d}", "-shortest", "-c:v", "libx264", "-c:a", "aac", f)
        parts.append(f)
    concat = tmp / "list.txt"
    concat.write_text("".join(f"file '{x}'\n" for x in parts))
    video = tmp / "take.mp4"
    ffmpeg("-f", "concat", "-safe", "0", "-i", concat, "-c", "copy", video)
    return video


@needs_ffmpeg
def test_qa_finds_the_five_cuts(tmp_path, synthetic_take):
    out = script("qa_take.py", synthetic_take, EXAMPLE, tmp_path / "qa")
    assert out.returncode == 0, out.stderr
    assert out.stdout.count("| ok |") == 5
    assert (tmp_path / "qa" / "QA.md").is_file()
    assert len(list((tmp_path / "qa").glob("shot_*.jpg"))) == 6
    assert "## Black frames\n\n- none" in out.stdout and "band-limited" not in out.stdout


@needs_ffmpeg
def test_qa_flags_black_seam_and_band_limited_audio(tmp_path, synthetic_take):
    """The BOLHAO act seam left one black frame; Seedance 2.5 native audio came at 32 kHz."""
    take = tmp_path / "seam.mp4"
    ffmpeg("-i", synthetic_take, "-vf", "drawbox=x=0:y=0:w=iw:h=ih:color=black:t=fill:enable='eq(n,240)'",
           "-c:v", "libx264", "-c:a", "aac", "-ar", "32000", take)
    out = script("qa_take.py", take, EXAMPLE, tmp_path / "qa")
    assert out.returncode == 0, out.stderr
    assert " s (1 frame(s)): check the seam" in out.stdout and "32000 Hz (band-limited" in out.stdout
    assert "1 black run(s)" in out.stdout


@needs_ffmpeg
def test_fidelity_passes_faithful_upscale_and_flags_change(tmp_path, synthetic_take):
    up = tmp_path / "up.mp4"
    ffmpeg("-i", synthetic_take, "-vf", "scale=1280:720:flags=lanczos", "-c:v", "libx264", "-c:a", "copy", up)
    out = script("fidelity.py", synthetic_take, up, tmp_path / "fid")
    assert out.returncode == 0, out.stderr
    assert "no numeric alert" in out.stdout
    changed = tmp_path / "changed.mp4"
    ffmpeg("-i", synthetic_take, "-vf", "scale=1280:720,drawbox=x=200:y=100:w=700:h=450:color=black:t=fill:enable='between(t,8,10)'",
           "-c:v", "libx264", "-c:a", "copy", changed)
    out = script("fidelity.py", synthetic_take, changed, tmp_path / "fid2")
    assert "suspect" in out.stdout
    assert (tmp_path / "fid2" / "FIDELITY.md").is_file()


# ---------------------------------------------------------------- animatic.py

@needs_ffmpeg
def test_animatic_holds_each_board_for_its_shot(tmp_path, plan):
    boards = tmp_path / "boards"
    boards.mkdir()
    for i in range(1, len(plan["shots"]) + 1):
        Image.new("RGB", (320, 180), (40 * i, 80, 160)).save(boards / f"SB_{i:02d}.png")
    out = tmp_path / "animatic.mp4"
    r = script("animatic.py", EXAMPLE, boards, out)
    assert r.returncode == 0, r.stderr
    info = probe_frames(out)
    assert int(info["nb_read_frames"]) == sum(round(s["dur_s"] * 24) for s in plan["shots"])
    assert (info["width"], info["height"]) == (1280, 720)


@needs_ffmpeg
def test_animatic_does_not_drift_on_fractional_durations(tmp_path):
    # per-shot rounding gave 3 x round(24.72) = 75 frames; the cuts belong at round(3.09 * 24) = 74
    p = {"shots": [{"dur_s": 1.03}] * 3}
    (tmp_path / "p.json").write_text(json.dumps(p))
    for i in range(1, 4):
        Image.new("RGB", (64, 36), (60 * i, 80, 160)).save(tmp_path / f"SB_{i:02d}.png")
    out = tmp_path / "a.mp4"
    assert script("animatic.py", tmp_path / "p.json", tmp_path, out).returncode == 0
    assert int(probe_frames(out)["nb_read_frames"]) == 74


# ---------------------------------------------------------------- project.py and compose_layers.py

@needs_ffmpeg
def test_project_ledger_and_layer_compositing(tmp_path):
    root = tmp_path / "project"
    script("project.py", "init", root, check=True)
    before = (root / "manifest.json").read_bytes()
    assert script("project.py", "init", root).returncode != 0, "init must refuse an existing folder"
    assert (root / "manifest.json").read_bytes() == before
    script("project.py", "context", root, check=True)
    assert (root / "CONTEXT.md").read_text()

    bg = Image.new("RGBA", (160, 80), "#153948")
    d = ImageDraw.Draw(bg)
    for x in range(0, 160, 8):
        d.rectangle((x, 0, x + 3, 79), fill="#719b6d")
    bg.save(tmp_path / "bg.png")
    (tmp_path / "pose").mkdir()
    for i in range(24):
        im = Image.new("RGBA", (128, 72))
        ImageDraw.Draw(im).rectangle((30 + i, 24, 42 + i, 42), fill="red")
        im.save(tmp_path / f"pose/{i:04d}.png")
    spec = {"width": 128, "height": 72, "fps": 24, "frames": 48,
            "layers": [{"file": "bg.png", "depth": 1}, {"sequence": "pose/{index:04d}.png", "exposure": 2, "depth": 0}],
            "camera": {"from": [0, 0], "to": [24, 0]}}
    (tmp_path / "scene.json").write_text(json.dumps(spec))
    out = root / "08_delivery" / "test.mp4"
    script("compose_layers.py", tmp_path / "scene.json", out, check=True)
    assert out.with_suffix(".exposure.json").is_file()

    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(out), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    size = 128 * 72 * 3
    assert len(raw) == 48 * size
    f0, f1, f2 = (Image.frombytes("RGB", (128, 72), raw[size * k:size * (k + 1)]) for k in range(3))

    def red_bbox(im):
        pts = [(x, y) for y in range(20, 45) for x in range(20, 70)
               if (lambda c: c[0] > 140 and c[1] < 90 and c[2] < 90)(im.getpixel((x, y)))]
        return min(x for x, _ in pts), max(x for x, _ in pts)

    # the character is held for two frames (on twos) while the camera keeps moving
    assert red_bbox(f0)[0] == red_bbox(f1)[0]
    assert red_bbox(f2)[0] == red_bbox(f1)[0] + 1
    assert abs(red_bbox(f0)[1] - red_bbox(f1)[1]) <= 1
    assert f0.crop((0, 0, 128, 15)).tobytes() != f1.crop((0, 0, 128, 15)).tobytes()

    (tmp_path / "pose/0023.png").unlink()
    assert script("compose_layers.py", tmp_path / "scene.json", tmp_path / "missing.mp4").returncode != 0
    assert not (tmp_path / "missing.mp4").exists()

    spec["layers"] = spec["layers"][:1]
    spec["camera"]["to"] = [200, 0]
    (tmp_path / "bad.json").write_text(json.dumps(spec))
    assert script("compose_layers.py", tmp_path / "bad.json", tmp_path / "bad.mp4").returncode != 0
    assert not (tmp_path / "bad.mp4").exists()

    m = json.loads((root / "manifest.json").read_text())
    m["master"] = {"width": 128, "height": 72, "fps": 24}
    m["deliverables"] = [{"file": "08_delivery/test.mp4"}]
    (root / "manifest.json").write_text(json.dumps(m))
    assert script("project.py", "verify", root).returncode == 0
    m["deliverables"] = [{"file": "no.mp4"}]
    (root / "manifest.json").write_text(json.dumps(m))
    assert script("project.py", "verify", root).returncode != 0

    # a finish at another size passes when it declares its size, and fails against the draft master otherwise
    m["master"] = {"width": 854, "height": 480, "fps": 24}
    m["deliverables"] = [{"file": "08_delivery/test.mp4"}]
    (root / "manifest.json").write_text(json.dumps(m))
    assert script("project.py", "verify", root).returncode != 0
    m["deliverables"] = [{"file": "08_delivery/test.mp4", "width": 128, "height": 72}]
    (root / "manifest.json").write_text(json.dumps(m))
    assert script("project.py", "verify", root).returncode == 0


def test_project_cache_key_is_order_independent(tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps({"x": 1, "y": [1, 2]}))
    b.write_text(json.dumps({"y": [1, 2], "x": 1}))
    ka = script("project.py", "cache-key", a, check=True).stdout.strip()
    assert ka == script("project.py", "cache-key", b, check=True).stdout.strip() and len(ka) == 64


# ---------------------------------------------------------------- timing_chart.py and lettering.py

@needs_ffmpeg
@pytest.mark.parametrize("mode", ["ruler", "column"])
def test_timing_chart_renders_alpha_layer(tmp_path, mode):
    cfg = {"w": 480, "h": 320, "fps": 24, "total": 24, "drawings": [[0, 1], [6, 2], [12, 3], [18, 0]], "keys": [1, 3],
           "names": {"1": "anticipation"}, "ruler": {"x0": 40, "x1": 440, "y": 160}, "stamp": {"x": 400, "y": 60}}
    if mode == "column":
        cfg.update({"mode": "column", "column": {"x": 200, "y0": 20, "y1": 300}, "hold": 6, "duration_frames": 18})
    (tmp_path / "t.json").write_text(json.dumps(cfg))
    out = tmp_path / "t.mov"
    r = script("timing_chart.py", tmp_path / "t.json", out)
    assert r.returncode == 0, r.stderr
    info = probe_frames(out)
    assert int(info["nb_read_frames"]) == (18 if mode == "column" else 24)
    assert info["pix_fmt"].startswith("yuva")


@needs_ffmpeg
def test_lettering_renders_alpha_card(tmp_path):
    cfg = {"w": 270, "h": 480, "fps": 24, "dur": 1.5, "elements": [
        {"text": "hello", "size": 40, "y": 200, "t": 0.1, "anim": "pop", "color": "#FFFFFF", "glow": 6, "breathe": True},
        {"text": "world", "size": 30, "y": 260, "t": 0.3, "anim": "rise", "gradient": ["#FFD45C", "#FF7A3C"], "shadow": True, "exit": 1.2},
        {"text": "typed", "size": 24, "y": 320, "t": 0.2, "anim": "type", "color": "#E0E0E0"}]}
    (tmp_path / "l.json").write_text(json.dumps(cfg))
    out = tmp_path / "l.mov"
    r = script("lettering.py", tmp_path / "l.json", out)
    assert r.returncode == 0, r.stderr
    info = probe_frames(out)
    assert int(info["nb_read_frames"]) == 36 and info["pix_fmt"].startswith("yuva")


# ---------------------------------------------------------------- breakdown_reel.py

@needs_ffmpeg
def test_breakdown_reel_writes_xmeml_and_preview(tmp_path):
    for name, c in (("a.mp4", "red"), ("b.mp4", "blue")):
        ffmpeg("-f", "lavfi", "-i", f"color={c}:s=320x180:r=24:d=2", "-c:v", "libx264", "-pix_fmt", "yuv420p", tmp_path / name)
    ffmpeg("-f", "lavfi", "-i", "sine=frequency=330:duration=3", "-c:a", "pcm_s16le", tmp_path / "guide.wav")
    cfg = {"name": "reel", "output_dir": str(tmp_path / "out"), "w": 360, "h": 640, "label_size": 18, "margin_x": 20,
           "safe_bottom": 600,
           "sections": [
               {"type": "bands", "start": 0, "dur": 1.5, "bands": [
                   {"file": str(tmp_path / "a.mp4"), "label": "film"}, {"file": str(tmp_path / "b.mp4"), "label": "lines"}]},
               {"type": "full", "start": 1.5, "dur": 1.0, "file": str(tmp_path / "a.mp4"), "in": 0.5, "label": "final"}],
           "audio": [{"file": str(tmp_path / "guide.wav"), "start": 0, "dur": 2.5}],
           "markers": [{"name": "music in", "t": 0.5}]}
    (tmp_path / "reel.json").write_text(json.dumps(cfg))
    r = script("breakdown_reel.py", tmp_path / "reel.json")
    assert r.returncode == 0, r.stderr
    xml_text = (tmp_path / "out" / "reel.xml").read_text(encoding="utf-8")
    assert "<xmeml" in xml_text and "Basic Motion" in xml_text and "<marker>" in xml_text
    doc = minidom.parseString(xml_text.encode("utf-8"))
    assert len(doc.getElementsByTagName("clipitem")) == 8  # background, 2 bands, full shot, 3 labels, 1 audio
    info = probe_frames(tmp_path / "out" / "reel_preview.mp4")
    assert (info["width"], info["height"]) == (360, 640)
    assert int(info["nb_read_frames"]) == 60


# ---------------------------------------------------------------- model-backed scripts: setup messages

def test_sketch_lines_explains_missing_anime2sketch(tmp_path):
    r = script("sketch_lines.py", tmp_path / "no_repo", "film.mp4", "out.mp4")
    assert r.returncode == 2
    assert "github.com/Mukosame/Anime2Sketch" in r.stdout and "improved.bin" in r.stdout


def test_pencil_animatic_explains_missing_isnet_model(tmp_path):
    r = script("pencil_animatic.py", "film.mp4", "depth.mp4", "out.mp4", "--style", "isnet", "--lines", "l.mp4")
    assert r.returncode == 2
    assert "huggingface.co/skytnt/anime-seg" in r.stdout and "isnetis.onnx" in r.stdout


def test_pencil_animatic_keeps_pink_only_when_asked():
    cv2 = pytest.importorskip("cv2")
    np = pytest.importorskip("numpy")
    import pencil_animatic
    hsv = cv2.cvtColor(np.full((4, 4, 3), (180, 60, 230), np.uint8), cv2.COLOR_BGR2HSV)  # saturated pink, BGR
    assert not pencil_animatic.pink_mask(hsv).any()
    pencil_animatic.KEEP_PINK = True
    try:
        assert pencil_animatic.pink_mask(hsv).all()
    finally:
        pencil_animatic.KEEP_PINK = False


def test_depth_map_explains_missing_video_depth_anything(tmp_path):
    r = script("depth_map.py", tmp_path / "no_repo", "film.mp4", tmp_path / "out", "--cuts", "0,24")
    assert r.returncode == 2
    assert "github.com/DepthAnything/Video-Depth-Anything" in r.stdout and "video_depth_anything_vits.pth" in r.stdout
