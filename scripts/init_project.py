"""Create a project folder for one source video: probe it, write project.json, extract the audio.

python init_project.py SOURCE.mov PROJECT_DIR [--look cine_warm] [--language vi] [--prompt "..."]
"""
import argparse
import json
import os
import subprocess

ap = argparse.ArgumentParser()
ap.add_argument("source")
ap.add_argument("project")
ap.add_argument("--look", default="cine_warm", choices=["cine_warm", "teal_orange", "neutral"])
ap.add_argument("--language", default="vi")
ap.add_argument("--prompt", default="Cuộc trò chuyện về AI, công nghệ, kinh doanh và cuộc sống. ChatGPT, Claude, AI agent, automation.")
ap.add_argument("--fps", type=int, default=0, help="output frame rate (default: source, capped at 30)")
args = ap.parse_args()

src = os.path.abspath(args.source)
proj = os.path.abspath(args.project)
os.makedirs(proj, exist_ok=True)
pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", src],
                               capture_output=True, encoding="utf-8").stdout)
v = next(s for s in pr["streams"] if s["codec_type"] == "video")
w, h = int(v["width"]), int(v["height"])
for sd in v.get("side_data_list", []):      # phones store portrait clips as rotated landscape
    if abs(int(sd.get("rotation", 0) or 0)) == 90:
        w, h = h, w
num, den = (v.get("avg_frame_rate") or "30/1").split("/")
src_fps = float(num) / max(float(den), 1)
fps = args.fps or (30 if src_fps > 31 else max(24, round(src_fps)))
trc = v.get("color_transfer", "")
transfer = {"arib-std-b67": "hlg", "smpte2084": "pq"}.get(trc, "sdr")
cfg_path = os.path.join(proj, "project.json")
cfg = json.load(open(cfg_path, encoding="utf-8")) if os.path.exists(cfg_path) else {}
cfg.update({
    "name": os.path.basename(proj), "source": src, "src_w": w, "src_h": h, "fps": fps, "transfer": transfer,
    "pix_fmt": v.get("pix_fmt"), "color_space": v.get("color_space", ""), "color_range": v.get("color_range", "tv"),
    "duration": float(pr["format"]["duration"]), "bit_rate_mbps": round(float(pr["format"].get("bit_rate", 0)) / 1e6, 1),
    "look": cfg.get("look", args.look), "language": args.language, "whisper_prompt": cfg.get("whisper_prompt", args.prompt),
})
cfg.setdefault("speakers", {})
json.dump(cfg, open(cfg_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

for rate, name in ((48000, "audio48k.wav"), (16000, "audio16k.wav")):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-ac", "1", "-ar", str(rate), "-c:a", "pcm_s16le",
                    os.path.join(proj, name)], check=True)

print(f"project: {proj}")
print(f"source: {w}x{h} {src_fps:.2f} fps, {transfer.upper()}, {v.get('pix_fmt')}, {cfg['bit_rate_mbps']} Mbps, {cfg['duration']:.1f} s")
short = min(w, h)
up_v, up_h = max(1920 / h, 1080 / w), max(1080 / h, 1920 / w)   # least upscale for the 9:16 and the 16:9 version
for name, up in (("vertical", up_v), ("horizontal", up_h)):
    if up > 1.01:
        print(f"note: the {name} version will be upscaled at least {up:.2f}x from this {w}x{h} source; shoot higher resolution for fully native sharpness.")
if h > w:
    print("note: portrait source: a 16:9 version can only be a tight crop on the face. Prefer the vertical version alone.")
if cfg["bit_rate_mbps"] < 15 and short >= 1080:
    print(f"note: {cfg['bit_rate_mbps']} Mbps is a thin source; fine texture (grass, knitwear) is limited by its compression.")
