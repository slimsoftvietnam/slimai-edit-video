"""QA helpers: contact sheets of a rendered video, or of stills from render.py --stills.

python review.py sheet  VIDEO OUT.jpg t0 t1 step cols       evenly spaced frames
python review.py seq    VIDEO OUT.jpg t_center n_frames     consecutive frames (check a transition)
python review.py stills DIR OUTPREFIX [cols rows tile_w]    stills -> OUTPREFIX_00.jpg, _01.jpg, ...
"""
import glob
import os
import subprocess
import sys

import cv2
import numpy as np

from imgio import imread, imwrite


def tile_size(video):
    w, h = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                           "-of", "csv=p=0", video], capture_output=True, text=True).stdout.strip().split(",")[:2]
    return (384, 216) if int(w) > int(h) else (270, 480)


def frames_at(video, times, scale):
    out = []
    for t in times:
        cmd = ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-vf",
               f"scale={scale[0]}:{scale[1]}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
        b = subprocess.run(cmd, capture_output=True).stdout
        if len(b) < scale[0] * scale[1] * 3:
            out.append(np.zeros((scale[1], scale[0], 3), np.uint8))
            continue
        out.append(np.frombuffer(b, np.uint8).reshape(scale[1], scale[0], 3).copy())
    return out


def grid(ims, labels, cols):
    for im, lb in zip(ims, labels):
        cv2.putText(im, lb, (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
        cv2.rectangle(im, (0, 0), (im.shape[1] - 1, im.shape[0] - 1), (30, 30, 30), 1)
    while len(ims) % cols:
        ims.append(np.zeros_like(ims[0]))
        labels.append("")
    rows = [np.hstack(ims[i:i + cols]) for i in range(0, len(ims), cols)]
    return np.vstack(rows)


def stills_sheets(d, prefix, cols, rows, tw):
    files = sorted(glob.glob(os.path.join(d, "*.jpg")))
    if not files:
        sys.exit(f"no stills in {d}")
    h0, w0 = imread(files[0]).shape[:2]
    th = tw * h0 // w0
    n = cols * rows
    for si in range(0, len(files), n):
        sheet = np.full((rows * (th + 34), cols * tw, 3), 20, np.uint8)
        for j, f in enumerate(files[si:si + n]):
            r, c = divmod(j, cols)
            y, x = r * (th + 34), c * tw
            sheet[y + 34:y + 34 + th, x:x + tw] = cv2.resize(imread(f), (tw, th), interpolation=cv2.INTER_AREA)
            cv2.putText(sheet, os.path.basename(f)[6:-4], (x + 8, y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        imwrite(f"{prefix}_{si // n:02d}.jpg", sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
    print("sheets:", (len(files) + n - 1) // n, "stills:", len(files))


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "stills":
        cols = int(sys.argv[4]) if len(sys.argv) > 4 else 4
        rows = int(sys.argv[5]) if len(sys.argv) > 5 else 3
        tw = int(sys.argv[6]) if len(sys.argv) > 6 else 480
        stills_sheets(sys.argv[2], sys.argv[3], cols, rows, tw)
    elif mode == "sheet":
        video, out = sys.argv[2], sys.argv[3]
        t0, t1, step, cols = float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6]), int(sys.argv[7])
        ts = list(np.arange(t0, t1, step))
        ims = frames_at(video, ts, tile_size(video))
        imwrite(out, grid(ims, [f"{t:.1f}" for t in ts], cols), [cv2.IMWRITE_JPEG_QUALITY, 85])
    elif mode == "seq":
        video, out = sys.argv[2], sys.argv[3]
        tc, n = float(sys.argv[4]), int(sys.argv[5])
        ts_ = tile_size(video)
        cmd = ["ffmpeg", "-v", "error", "-ss", f"{max(0, tc - n / 60):.3f}", "-i", video, "-frames:v", str(n),
               "-vf", f"scale={ts_[0]}:{ts_[1]}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
        b = subprocess.run(cmd, capture_output=True).stdout
        fr = np.frombuffer(b, np.uint8).reshape(-1, ts_[1], ts_[0], 3).copy()
        start = max(0, tc - n / 60)
        imwrite(out, grid(list(fr), [f"{start + i / 30:.2f}" for i in range(len(fr))], min(5 if ts_[0] > ts_[1] else 10, n)),
                    [cv2.IMWRITE_JPEG_QUALITY, 85])
    else:
        sys.exit(__doc__)
