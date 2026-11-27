"""Graded master holding only the frames the edit uses (source order) + master_index.json. The frames are the
clips of timeline.json plus its "extra" ranges (B-roll drawn over a speaking clip, set in select.json).

python build_master.py PROJECT [--crf 6] [--denoise | --no-denoise] [--look iphone]
python build_master.py PROJECT --dry          (print the master index it would build; nothing is written)

Quality path: 10-bit source -> float RGB -> film LUT (float, tetrahedral) -> near-lossless 4:4:4.
There is no 8-bit step before the grade, which is where the old pipeline lost gradients and detail.
The "iphone" look on an HLG source skips the LUT: film_look.iphone_vf() decodes and tone-maps it in ffmpeg.
A film look runs a temporal denoise first: a static shot has no real frame-to-frame change, so removing the
codec's "boil" gives the sharpening pass and the platform encoder cleaner input. The "iphone" look keeps the
picture as the phone recorded it, so it skips the denoise unless --denoise asks for it.

The master is written as master.tmp.mkv and takes its name only once its frame count is right, so a failed build
leaves the old master in place; project.json gets the new look only then too. ffmpeg's select expression takes at
most 100 ranges (101 between() terms fail to parse), so a cut with more joins the ranges with the shortest gaps:
the master then holds a few frames the edit does not use, and master_index.json still maps every used frame.
"""
import argparse
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import film_look  # noqa: E402

MAX_RANGES = 100     # ffmpeg 7: an expression of 101 between() terms fails to parse ("Error while parsing expression")


def plan_ranges(tl, fps, max_ranges=MAX_RANGES):
    """the source ranges the master holds -> (ranges [[a, b)], index [[source frame, count, master position]], frames)"""
    ranges = sorted([(int(round(c["src_in"] * fps)), int(round(c["src_in"] * fps)) + c["frames"]) for c in tl["clips"]] +
                    [(int(round(t * fps)), int(round(t * fps)) + int(n)) for (t, n) in tl.get("extra", [])])   # B-roll overlays
    merged = []
    for a, b in ranges:
        if merged and a <= merged[-1][1] + 2:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    while len(merged) > max_ranges:           # join the two ranges with the shortest gap between them
        k = min(range(len(merged) - 1), key=lambda i: merged[i + 1][0] - merged[i][1])
        merged[k][1] = max(merged[k][1], merged[k + 1][1])
        del merged[k + 1]
    index, pos = [], 0
    for a, b in merged:
        index.append([a, b - a, pos])
        pos += b - a
    return merged, index, pos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--crf", type=float, default=6)
    ap.add_argument("--no-denoise", action="store_true")
    ap.add_argument("--denoise", action="store_true", help="temporal denoise even for the iphone look")
    ap.add_argument("--look", default=None)
    ap.add_argument("--dry", action="store_true", help="print the master index only")
    args = ap.parse_args()

    proj = os.path.abspath(args.project)
    cfg_path = os.path.join(proj, "project.json")
    cfg = json.load(open(cfg_path, encoding="utf-8"))
    tl = json.load(open(os.path.join(proj, "timeline.json"), encoding="utf-8"))
    FPS = cfg["fps"]
    merged, index, pos = plan_ranges(tl, FPS)
    if args.dry:
        print(json.dumps(index))
        return
    look = args.look or cfg.get("look", "iphone")
    transfer = cfg["transfer"]
    rin = "full" if cfg.get("color_range") == "pc" else "limited"
    natural = film_look.iphone_vf(transfer, rin, out_range="limited", dither=True) if look == "iphone" else None
    lut = f"look_{look}_{transfer}.cube"
    if not natural:
        film_look.write_cube(os.path.join(proj, lut), look, transfer)
    sel = "+".join(f"between(n,{a},{b - 1})" for a, b in merged)

    matrix = "2020_ncl" if transfer in ("hlg", "pq") else "709"
    denoise = args.denoise or (look != "iphone" and not args.no_denoise)
    den = "atadenoise=0a=0.015:0b=0.03:1a=0.015:1b=0.03:2a=0.015:2b=0.03:s=7," if denoise else ""
    if natural:
        grade = natural + ",format=yuv444p,"
    else:
        grade = (f"zscale=filter=lanczos:min={matrix}:rin={rin}:r=full,format=gbrpf32le,"
                 f"lut3d=file={lut}:interp=tetrahedral,"
                 "zscale=m=709:r=limited:d=error_diffusion,format=yuv444p,")
    vf = (f"fps={FPS},select='{sel}',setpts=N/{FPS}/TB,{den}{grade}"
          "setparams=range=tv:color_primaries=bt709:color_trc=bt709:colorspace=bt709")
    t0 = time.time()
    tmp = os.path.join(proj, "master.tmp.mkv")
    cmd = ["ffmpeg", "-v", "error", "-stats", "-y", "-i", cfg["source"], "-an", "-vf", vf, "-fps_mode", "passthrough",
           "-c:v", "libx264", "-preset", "medium", "-crf", str(args.crf), "-g", "15", "-colorspace", "bt709",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", "master.tmp.mkv"]
    subprocess.run(cmd, cwd=proj, check=True)
    n = int(subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                            "stream=nb_read_packets", "-of", "csv=p=0", tmp],
                           capture_output=True, text=True).stdout.strip().split(",")[0])
    if n != pos:
        os.remove(tmp)
        sys.exit(f"the new master had {n} frames, expected {pos}: the old master.mkv is unchanged")
    os.replace(tmp, os.path.join(proj, "master.mkv"))
    with open(os.path.join(proj, "master_index.json.tmp"), "w") as fh:
        json.dump(index, fh)
    os.replace(os.path.join(proj, "master_index.json.tmp"), os.path.join(proj, "master_index.json"))
    if args.look:
        cfg["look"] = look
        json.dump(cfg, open(cfg_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    size = os.path.getsize(os.path.join(proj, "master.mkv"))
    print(f"master.mkv: {pos} frames in {len(index)} ranges, {size / 1e9:.2f} GB, {time.time() - t0:.0f} s, look {look}/{transfer}")


if __name__ == "__main__":
    main()
