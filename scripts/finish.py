"""Final delivery: mux picture + soundtrack, verify the file, make a light preview.

python finish.py --project P --fmt tiktok|youtube VIDEO.mp4 OUT_NAME [--outdir DIR] [--no-preview]

Writes OUT_NAME.mp4 (AAC 320k, BT.709 tags, faststart) and OUT_NAME_preview_720p.mp4 (under 30 MB, for
sending to a phone), then prints a PASS/FAIL report: resolution, frame count, colour tags, loudness, true peak.
"""
import argparse
import json
import os
import re
import subprocess
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--project", required=True)
ap.add_argument("--fmt", choices=["youtube", "tiktok"], required=True)
ap.add_argument("video")
ap.add_argument("name")
ap.add_argument("--outdir", default=None)
ap.add_argument("--no-preview", action="store_true")
args = ap.parse_args()

proj = os.path.abspath(args.project)
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
checks = [
    ("resolution", (v["width"], v["height"]) in want, f"{v['width']}x{v['height']}"),
    ("colour tags", v.get("color_primaries") == "bt709" and v.get("color_transfer") == "bt709" and v.get("color_space") == "bt709",
     f"{v.get('color_primaries')}/{v.get('color_transfer')}/{v.get('color_space')}"),
    ("pixel format", v.get("pix_fmt") == "yuv420p", v.get("pix_fmt")),
    ("loudness -14 LUFS", abs(lufs + 14) <= 0.5, f"{lufs:.1f} LUFS"),
    ("true peak", peak <= -0.9, f"{peak:.1f} dBFS"),
]
ok = True
for name, passed, val in checks:
    ok &= passed
    print(f"{'PASS' if passed else 'FAIL'}  {name}: {val}")
print(f"file: {out}\n      {dur:.1f} s, {v.get('nb_read_frames')} frames, {size / 1e6:.0f} MB, {size * 8 / dur / 1e6:.1f} Mbps")

if not args.no_preview:
    pv = os.path.join(outdir, args.name + "_preview_720p.mp4")
    scale = "scale=1280:720" if v["width"] > v["height"] else "scale=720:1280"
    br = int(min(1650, (27.5e6 * 8 / dur - 128e3) / 1000))     # stay under the 30 MiB phone limit
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
sys.exit(0 if ok else 1)
