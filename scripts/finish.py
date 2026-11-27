"""Final delivery: mux picture + soundtrack, verify the file, make a light preview.

python finish.py --project P --fmt tiktok|youtube VIDEO.mp4 OUT_NAME [--outdir DIR] [--no-preview] [--force]

Writes OUT_NAME.mp4 (AAC 320k, BT.709 tags, faststart) and OUT_NAME_preview_1080p.mp4 (under 30 MB, for
sending to a phone; 720p when the video is too long for 1080p at that size), then prints a PASS/FAIL report:
resolution, colour tags, pixel format, loudness, true peak, the frame count against the timeline (plus the end hold),
the soundtrack's length against the picture's, and whether audio_<fmt>/final_audio.wav is newer than what it was
mixed from (design.py and the project modules it imports, timeline.json, beats.json). A stale soundtrack is a FAIL:
mix again, or pass --force to ship it anyway (it is then a WARN). A picture older than those files is a WARN.

OUT_NAME comes from episode.py (EPISODE_VARIANT_vN) and --outdir is the episode folder. When every check passes, the
files of the earlier versions of that deliverable move into ban_cu/, so only the newest stays on top.
"""
import argparse
import ast
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import episode  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--project", required=True)
ap.add_argument("--fmt", choices=["youtube", "tiktok"], required=True)
ap.add_argument("video")
ap.add_argument("name")
ap.add_argument("--outdir", default=None)
ap.add_argument("--no-preview", action="store_true")
ap.add_argument("--force", action="store_true", help="ship a soundtrack older than the design (WARN, not FAIL)")
args = ap.parse_args()

proj = os.path.abspath(args.project)
os.environ.update(EDIT_PROJECT=proj, EDIT_FMT=args.fmt, EDIT_SS="1")
import story  # noqa: E402  (the timeline's length and the end hold, as render.py counts them; the design is not loaded)

EXPECT_F = int(round(story.TOTAL * story.FPS))


def design_files():
    """design.py and the project modules it imports, followed through their own imports"""
    seen, todo = [], ["design"]
    while todo:
        name = todo.pop()
        path = os.path.join(proj, name + ".py")
        if name in seen or not os.path.exists(path):
            continue
        seen.append(name)
        for node in ast.walk(ast.parse(open(path, encoding="utf-8").read())):
            if isinstance(node, ast.Import):
                todo += [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                todo.append(node.module.split(".")[0])
    return [os.path.join(proj, n + ".py") for n in seen]


def newer_inputs(path):
    """the inputs of the edit changed after `path` was written: [(name, time)]"""
    inputs = design_files() + [os.path.join(proj, n) for n in ("timeline.json", "beats.json")]
    t = os.path.getmtime(path)
    return [(os.path.basename(p), os.path.getmtime(p)) for p in inputs if os.path.exists(p) and os.path.getmtime(p) > t]


def hhmm(t):
    return time.strftime("%d/%m %H:%M", time.localtime(t))

outdir = os.path.abspath(args.outdir or os.path.join(proj, "output"))
os.makedirs(outdir, exist_ok=True)
audio = os.path.join(proj, f"audio_{args.fmt}", "final_audio.wav")
out = os.path.join(outdir, args.name + ".mp4")
bsf = "h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0"
abr = "384k" if args.fmt == "youtube" else "320k"     # YouTube's recommendation for stereo
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", args.video, "-i", audio, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                "-bsf:v", bsf, "-c:a", "aac", "-b:a", abr, "-ar", "48000", "-ac", "2", "-movflags", "+faststart", out], check=True)

pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", "-count_frames",
                                "-select_streams", "v:0", out], capture_output=True, encoding="utf-8").stdout)
v = pr["streams"][0]
dur = float(pr["format"]["duration"])
size = os.path.getsize(out)
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", out, "-map", "0:a", "-af", "ebur128=peak=true:framelog=quiet", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
tail = r[r.rfind("Summary:"):]
lufs = float(re.search(r"I:\s+(-?[\d.]+) LUFS", tail).group(1))
peak = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail).group(1))
want = {"youtube": [(3840, 2160), (1920, 1080)], "tiktok": [(1080, 1920)]}[args.fmt]
frames = int(v.get("nb_read_frames") or 0)
wav = json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-select_streams", "a:0",
                                 audio], capture_output=True, encoding="utf-8").stdout)["streams"][0]
wav_s = int(wav["duration_ts"]) / int(wav["sample_rate"])
pic_s = frames / story.FPS
stale = newer_inputs(audio)
late = ", ".join(f"{n} ({hhmm(t)})" for n, t in stale)
checks = [
    ("resolution", (v["width"], v["height"]) in want, f"{v['width']}x{v['height']}"),
    ("colour tags", v.get("color_primaries") == "bt709" and v.get("color_transfer") == "bt709" and v.get("color_space") == "bt709",
     f"{v.get('color_primaries')}/{v.get('color_transfer')}/{v.get('color_space')}"),
    ("pixel format", v.get("pix_fmt") == "yuv420p", v.get("pix_fmt")),
    ("loudness -14 LUFS", abs(lufs + 14) <= 0.5, f"{lufs:.1f} LUFS"),
    ("true peak", peak <= -0.9, f"{peak:.1f} dBFS"),
    ("frame count", frames == EXPECT_F, f"{frames} (timeline + end hold: {EXPECT_F})"),
    ("soundtrack length", abs(wav_s - pic_s) <= 1.0 / story.FPS, f"{wav_s:.3f} s for {pic_s:.3f} s of picture"),
    ("soundtrack up to date", not stale or "warn",
     f"final_audio.wav ({hhmm(os.path.getmtime(audio))}) is older than {late}: mix again, or --force" if stale else
     "final_audio.wav is newer than the design, timeline.json and beats.json"),
]
if stale and not args.force:
    checks[-1] = (checks[-1][0], False, checks[-1][2])
old_pic = newer_inputs(args.video)
if old_pic:
    checks.append(("picture up to date", "warn", f"{os.path.basename(args.video)} is older than "
                   + ", ".join(n for n, _t in old_pic) + ": render again if that change touches the picture"))
ok = True
for name, passed, val in checks:
    ok &= bool(passed)
    print(f"{'WARN' if passed == 'warn' else 'PASS' if passed else 'FAIL'}  {name}: {val}")
print(f"file: {out}\n      {dur:.1f} s, {v.get('nb_read_frames')} frames, {size / 1e6:.0f} MB, {size * 8 / dur / 1e6:.1f} Mbps")

if not args.no_preview:
    # the user judges the edit on a phone: 1080p while the bitrate allows it, 720p for a long video, under 30 MiB
    br = int((28.5e6 * 8 / dur - 160e3) / 1000)
    hd = br >= 1200
    br = min(br, 6000 if hd else 1650)
    long_side, short_side = (1920, 1080) if hd else (1280, 720)
    pv = os.path.join(outdir, f"{args.name}_preview_{short_side}p.mp4")
    scale = f"scale={long_side}:{short_side}" if v["width"] > v["height"] else f"scale={short_side}:{long_side}"
    log = os.path.join(outdir, "x264pass")
    base = ["ffmpeg", "-v", "error", "-y", "-i", out, "-vf", f"{scale}:flags=lanczos", "-c:v", "libx264", "-preset", "slow",
            "-b:v", f"{br}k", "-passlogfile", log]
    subprocess.run(base + ["-pass", "1", "-an", "-f", "null", "NUL" if os.name == "nt" else "/dev/null"], check=True)
    subprocess.run(base + ["-pass", "2", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", pv], check=True)
    for f in os.listdir(outdir):
        if f.startswith("x264pass"):
            os.remove(os.path.join(outdir, f))
    print(f"preview: {pv} ({os.path.getsize(pv) / 1e6:.0f} MB)")
if ok:
    moved, kept = episode.retire(outdir, args.name)
    if moved:
        print(f"earlier versions moved into {episode.OLD_DIR}/: {', '.join(moved)}")
    if kept:
        print(f"left on top, {episode.OLD_DIR}/ already has a file of that name: {', '.join(kept)}")
sys.exit(0 if ok else 1)
