"""SRT captions (same corrected words as the burned-in captions) and the YouTube chapter list.

python export_captions.py --project P --fmt youtube NAME [--outdir DIR]   -> NAME.srt, NAME_chapters.txt
"""
import argparse
import os
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--project", required=True)
ap.add_argument("--fmt", choices=["youtube", "tiktok"], default="youtube")
ap.add_argument("name")
ap.add_argument("--outdir", default=None)
ARGS = ap.parse_args()
os.environ["EDIT_PROJECT"] = os.path.abspath(ARGS.project)
os.environ["EDIT_FMT"] = ARGS.fmt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import story as D  # noqa: E402

D.load_design()
outdir = os.path.abspath(ARGS.outdir or os.path.join(ARGS.project, "output"))
os.makedirs(outdir, exist_ok=True)


def ts(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


rows = []
prev = 0.0
for i, ln in enumerate(D.LINES, 1):
    a = max(prev, ln[0]["s"] - 0.05)  # no overlaps: YouTube would stack two cues
    b = ln[0]["line_end"]
    prev = b
    rows.append(f"{i}\n{ts(a)} --> {ts(b)}\n{' '.join(x['disp'] for x in ln)}\n")
open(os.path.join(outdir, ARGS.name + ".srt"), "w", encoding="utf-8").write("\n".join(rows))

ch = sorted(D.YT_CHAPTERS)
bad = [t for t, n in zip(ch, ch[1:] + [(D.TOTAL, "")]) if n[0] - t[0] < 10]
if ch and (ch[0][0] != 0 or len(ch) < 3 or bad):
    print("WARNING: YouTube chapters need a 0:00 start, at least 3 entries and >= 10 s each:", bad)
open(os.path.join(outdir, ARGS.name + "_chapters.txt"), "w", encoding="utf-8").write(
    "\n".join(f"{D.fmt_ts(t)} {title}" for t, title in ch) + "\n")
print(f"{len(rows)} caption cues, {len(ch)} chapters -> {outdir}")
