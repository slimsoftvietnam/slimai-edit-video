"""Regression check for the skill: run a project copy again and prove the output is the same, bit for bit.

Use it before and after any change to the scripts that should not change a delivered video (a refactor, a cleanup):

python tests/regress.py clone SRC DST              a test copy of a project: big read-only inputs (master, mattes,
                                                   source audio, licensed tracks) hardlinked, everything else copied
python tests/regress.py snapshot SUITE OUT         run SUITE/regress.json with a frozen copy of the skill -> OUT
python tests/regress.py compare A B                every still and file of two snapshots: same or different

SUITE/regress.json (paths in "run" may use {python} {skill} {scripts} {proj}):
{"run": [["{python}", "{scripts}/build_timeline.py", "{proj}"], ...],   steps, in order, run from the project folder
 "stills": [{"fmt": "tiktok", "times": [0.5, 2.0], "every": 3.0}],      frames composed in memory: sha256 of the pixels
 "hash": ["timeline.json", "audio_tiktok/*.wav"]}                       files hashed after the steps

The snapshot keeps its frozen copy of the skill (OUT/skill), so the old code can be run again to look at a difference,
and the working tree can be edited while a snapshot runs. Never point a suite at a real project: the steps rewrite its
files. Steps and stills run with PYTHONHASHSEED=0, so set order cannot make two runs differ.
"""
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

LINK_DIRS = ("matte", "music_work")                      # read-only inputs: every file hardlinked
LINK_EXT = (".mkv", ".wav", ".mp4", ".mov", ".m4a", ".mp3", ".flac")   # big media at the top: hardlinked
SKIP_DIRS = ("render", "audio_tiktok", "audio_youtube", "__pycache__", "thumb_test", "_regress")
SKIP_PREFIX = ("stills", "sheet", "cmp", "seq_", "review")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# ----------------------------------------------------------------------------
# clone
# ----------------------------------------------------------------------------
def clone(src, dst):
    src, dst = os.path.abspath(src), os.path.abspath(dst)
    if os.path.exists(dst):
        sys.exit(f"{dst} exists: pick a new folder")
    n_link = n_copy = 0
    for dirpath, dirnames, filenames in os.walk(src):
        rel = os.path.relpath(dirpath, src)
        top = rel.split(os.sep)[0] if rel != "." else ""
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(SKIP_PREFIX)
                       and not d.endswith("_parts")]
        os.makedirs(os.path.join(dst, rel), exist_ok=True)
        for name in filenames:
            a, b = os.path.join(dirpath, name), os.path.join(dst, rel, name)
            if top in LINK_DIRS or (rel == "." and name.lower().endswith(LINK_EXT)):
                os.link(a, b)
                n_link += 1
            elif rel == "." and name.startswith(SKIP_PREFIX):
                continue
            else:
                shutil.copy2(a, b)
                n_copy += 1
    print(f"{dst}: {n_link} files hardlinked (read-only inputs), {n_copy} copied")


# ----------------------------------------------------------------------------
# snapshot
# ----------------------------------------------------------------------------
def git_rev(root):
    try:
        rev = subprocess.run(["git", "-C", root, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout
        dirty = subprocess.run(["git", "-C", root, "status", "--porcelain"], capture_output=True, text=True).stdout
        return rev.strip() + (" + uncommitted changes" if dirty.strip() else "")
    except OSError:
        return "?"


def frames_of(spec, total):
    ts = list(spec.get("times", []))
    every = spec.get("every")
    if every:
        k = 0
        while k * every < total - 0.05:
            ts.append(round(k * every, 3))
            k += 1
    return sorted(set(round(float(t), 3) for t in ts))


def snapshot(suite, out, skill_root):
    suite, out = os.path.abspath(suite), os.path.abspath(out)
    cfg = json.load(open(os.path.join(suite, "regress.json"), encoding="utf-8"))
    if os.path.exists(out) and os.listdir(out):
        sys.exit(f"{out} is not empty")
    os.makedirs(out, exist_ok=True)
    t_start = time.time()
    frozen = os.path.join(out, "skill")
    shutil.copytree(skill_root, frozen, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "tests"))
    scripts = os.path.join(frozen, "scripts")
    env = dict(os.environ, REGRESS_SKILL=scripts, PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1",
               PYTHONIOENCODING="utf-8")
    subst = {"python": sys.executable, "skill": frozen, "scripts": scripts, "proj": suite}
    log = open(os.path.join(out, "run.log"), "w", encoding="utf-8")
    print(f"frozen skill ({git_rev(skill_root)}) -> {frozen}", flush=True)
    for step in cfg.get("run", []):
        cmd = [part.format(**subst) for part in step]
        print("run", " ".join(os.path.basename(c) if os.path.isabs(c) else c for c in cmd), flush=True)
        log.write("$ " + " ".join(cmd) + "\n")
        log.flush()
        r = subprocess.run(cmd, cwd=suite, env=env, stdout=log, stderr=subprocess.STDOUT)
        if r.returncode != 0:
            sys.exit(f"step failed ({r.returncode}): {' '.join(cmd)}; see {out}/run.log")
    stills = {}
    for spec in cfg.get("stills", []):
        fmt = spec["fmt"]
        res = os.path.join(out, f"stills_{fmt}.json")
        env2 = dict(env, EDIT_PROJECT=suite, EDIT_FMT=fmt, EDIT_SS=str(spec.get("ss", 1)))
        print(f"stills {fmt}", flush=True)
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "_stills", scripts, json.dumps(spec), res,
                            os.path.join(out, f"stills_{fmt}")], cwd=suite, env=env2, stdout=log,
                           stderr=subprocess.STDOUT)
        if r.returncode != 0:
            sys.exit(f"stills failed for {fmt}; see {out}/run.log")
        stills[fmt] = json.load(open(res, encoding="utf-8"))
    files = {}
    keep = os.path.join(out, "files")
    for pat in cfg.get("hash", []):
        hits = sorted(glob.glob(os.path.join(glob.escape(suite), pat)))
        if not hits:
            files[pat] = None                           # an expected file that is missing is a difference too
        for p in hits:
            rel = os.path.relpath(p, suite).replace(os.sep, "/")
            files[rel] = sha(p)
            if p.endswith((".json", ".txt")):           # small text outputs are kept, to diff them later
                os.makedirs(os.path.dirname(os.path.join(keep, rel)), exist_ok=True)
                shutil.copy2(p, os.path.join(keep, rel))
    man = {"suite": suite, "skill": git_rev(skill_root), "made": time.strftime("%Y-%m-%d %H:%M:%S"),
           "seconds": round(time.time() - t_start), "stills": stills, "files": files}
    json.dump(man, open(os.path.join(out, "manifest.json"), "w", encoding="utf-8"), indent=1)
    n = sum(len(v) for v in stills.values())
    print(f"snapshot {out}: {n} stills, {len(files)} files, {man['seconds']} s", flush=True)


def _stills(scripts, spec_json, res, preview_dir):
    """child process (env EDIT_PROJECT / EDIT_FMT / EDIT_SS set): compose each frame as render.py --stills does."""
    spec = json.loads(spec_json)
    sys.path.insert(0, scripts)
    import cv2
    import hashlib as hl

    import render as R
    os.makedirs(preview_dir, exist_ok=True)
    ctx = R.Ctx()
    out = {}
    for t in frames_of(spec, R.D.TOTAL):
        f = int(round(t * R.FPS))
        ci = R.clip_index_for_frame(f)
        c = R.CLIPS[ci] if ci is not None else R.D.clip_at(f / R.FPS)
        src_f = c["src_f0"] + (f - c["out_f0"]) if ci is not None else c["src_f0"] + c["frames"] - 1
        rd = R.E.ClipReader(src_f, 1)
        frame = rd.next()
        rd.close()
        img = R.compose(frame, src_f, f / R.FPS, f, ctx)
        out[f"{t:.3f}"] = hl.sha256(repr(img.shape).encode() + img.tobytes()).hexdigest()
        small = cv2.resize(img, (img.shape[1] // 2, img.shape[0] // 2), interpolation=cv2.INTER_AREA)
        cv2.imencode(".jpg", small)[1].tofile(os.path.join(preview_dir, f"{t:08.3f}.jpg"))
    json.dump(out, open(res, "w", encoding="utf-8"), indent=1)


# ----------------------------------------------------------------------------
# compare
# ----------------------------------------------------------------------------
def compare(a, b):
    A = json.load(open(os.path.join(a, "manifest.json"), encoding="utf-8"))
    B = json.load(open(os.path.join(b, "manifest.json"), encoding="utf-8"))
    bad = 0
    for fmt in sorted(set(A["stills"]) | set(B["stills"])):
        sa, sb = A["stills"].get(fmt, {}), B["stills"].get(fmt, {})
        keys = sorted(set(sa) | set(sb), key=float)
        diff = [k for k in keys if sa.get(k) != sb.get(k)]
        print(f"stills {fmt}: {len(keys) - len(diff)}/{len(keys)} the same")
        for k in diff:
            print(f"   DIFFERENT  t={k}" + ("" if k in sa and k in sb else "  (only in one snapshot)"))
        bad += len(diff)
    fa, fb = A["files"], B["files"]
    keys = sorted(set(fa) | set(fb))
    diff = [k for k in keys if fa.get(k) != fb.get(k) or fa.get(k) is None]
    print(f"files: {len(keys) - len(diff)}/{len(keys)} the same")
    for k in diff:
        print(f"   DIFFERENT  {k}" + ("  (missing)" if fa.get(k) is None or fb.get(k) is None else ""))
    bad += len(diff)
    print("SAME" if bad == 0 else f"{bad} DIFFERENCES")
    return bad


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "clone" and len(a) == 3:
        clone(a[1], a[2])
    elif a[0] == "snapshot" and len(a) in (3, 5):
        snapshot(a[1], a[2], os.path.abspath(a[4]) if len(a) == 5 and a[3] == "--skill" else ROOT)
    elif a[0] == "compare" and len(a) == 3:
        sys.exit(1 if compare(a[1], a[2]) else 0)
    elif a[0] == "_stills":
        _stills(*a[1:5])
    else:
        sys.exit(__doc__)
