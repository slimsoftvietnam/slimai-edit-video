"""Deliverables go in one folder per episode, with only the newest version of each on top.

    python episode.py PROJECT OUTPUT VARIANT      # prints the episode folder, then the next free name:
    .../output/01_Phong_van
    01_Phong_van_TikTok_trailer_v2
    python episode.py --next OUTPUT               # the next free episode number, to suggest for a source without one

- The episode is "episode" in project.json, e.g. "01_Phong_van". init_project.py takes it from a source file whose name
  starts with a number ("01_Phong_van.mov"). For any other source, ask the user which episode it is, then set it by
  hand (normalise() shows the form). A video the user does not want numbered gets its name alone ("Phong_van").
- A deliverable is named EPISODE_VARIANT_vN, where VARIANT is TikTok, TikTok_trailer (a trailer or motion cut),
  YouTube_HD (a standard or vlog cut) and so on. Its other files share the stem: _preview_1080p.mp4 (or _720p),
  _cover.jpg, .srt, _chapters.txt, _kit.txt, _thumbnail_A.jpg, _nguon.txt.
- Only the newest version of each variant stays at the top of the episode folder. Once a new version passes,
  finish.py moves the older ones into ban_cu/. Comparison and test images go in so_sanh/.
"""
import argparse
import json
import os
import re
import sys
import unicodedata

OLD_DIR = "ban_cu"         # earlier versions, kept for comparison
COMPARE_DIR = "so_sanh"    # comparison sheets and tests, never published
_LEAD = re.compile(r"^(\d{1,3})[ _.\-]+(.+)$")


def clean(name):
    """ASCII words joined by "_": safe in every path, since cv2 and some tools fail on Vietnamese ones."""
    s = unicodedata.normalize("NFKD", name.replace("đ", "d").replace("Đ", "D"))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")


def normalise(episode):
    """"5 Học AI" -> "05_Hoc_AI"; a name without a number is only cleaned."""
    m = _LEAD.match(episode.strip())
    return f"{int(m.group(1)):02d}_{clean(m.group(2))}" if m else clean(episode)


def from_source(path):
    """"01_Phong_van.mov" -> "01_Phong_van"; None when the file name does not start with a number."""
    stem = os.path.splitext(os.path.basename(path))[0]
    return normalise(stem) if _LEAD.match(stem) else None


def next_episode(output):
    """one above the highest numbered folder in output/: a suggestion, since the user may have planned other numbers."""
    nums = [int(m.group(1)) for d in (os.listdir(output) if os.path.isdir(output) else [])
            if os.path.isdir(os.path.join(output, d)) and (m := re.match(r"^(\d{1,3})_", d))]
    return f"{max(nums or [0]) + 1:02d}"


def _versions(folder, base):
    """(directory, file, version) of every file of base_vN, at the top of folder and in its ban_cu/."""
    rx = re.compile(re.escape(base) + r"_v(\d+)(?=[_.]|$)")
    for sub in (folder, os.path.join(folder, OLD_DIR)):
        if os.path.isdir(sub):
            for f in sorted(os.listdir(sub)):
                m = rx.match(f)
                if m and os.path.isfile(os.path.join(sub, f)):
                    yield sub, f, int(m.group(1))


def next_name(folder, base):
    """base_v1, or one above the highest version in folder and its ban_cu/."""
    return f"{base}_v{max([k for _s, _f, k in _versions(folder, base)] or [0]) + 1}"


def retire(folder, name):
    """name is base_vN: move the files of base_v1 .. v(N-1) from the top of folder into ban_cu/. Other variants are
    untouched. Returns (moved, kept): kept are files left on top because ban_cu/ already has one of that name."""
    m = re.match(r"^(.*)_v(\d+)$", name)
    if not m:
        return [], []
    base, n = m.group(1), int(m.group(2))
    moved, kept = [], []
    for sub, f, k in list(_versions(folder, base)):
        if sub != folder or k >= n:
            continue
        dst = os.path.join(folder, OLD_DIR, f)
        if os.path.exists(dst):
            kept.append(f)
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        os.rename(os.path.join(folder, f), dst)
        moved.append(f)
    return moved, kept


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project", nargs="?")
    ap.add_argument("output", nargs="?", help="the root of all deliverables, <working dir>/output")
    ap.add_argument("variant", nargs="?", help="TikTok, TikTok_trailer, YouTube_HD ...")
    ap.add_argument("--next", metavar="OUTPUT", help="print the next free episode number in OUTPUT")
    args = ap.parse_args()
    if args.next:
        print(next_episode(args.next))
        sys.exit(0)
    if not args.variant:
        ap.error("give PROJECT OUTPUT VARIANT, or --next OUTPUT")
    cfg = json.load(open(os.path.join(args.project, "project.json"), encoding="utf-8"))
    ep = cfg.get("episode")
    if not ep:
        sys.exit(f'project.json has no "episode". Ask the user which episode this is (next free number: '
                 f'{next_episode(args.output)}), then set it, e.g. "episode": "{next_episode(args.output)}_Ten_video".')
    folder = os.path.join(os.path.abspath(args.output), ep)
    print(folder)
    print(next_name(folder, f"{ep}_{clean(args.variant)}"))
