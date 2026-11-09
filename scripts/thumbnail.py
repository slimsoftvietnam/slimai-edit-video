"""YouTube thumbnails (1280x720) with the same engine: depth text behind the speaker, subject pop.

python thumbnail.py --project P [--outdir DIR]     runs P/thumbs.py, which defines THUMBS = {"file.jpg": fn}
Each fn returns compose(source_frame, cam_for(zoom, face_x, face_y), behind_fn, front_fn, keep_x0).
Use a frame that exists in the master (a frame from the timeline). See examples/repo-ai-agent/thumbs.py.
"""
import argparse
import os
import sys

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--outdir", default=None)
    ARGS = ap.parse_args()
    os.environ["EDIT_PROJECT"] = os.path.abspath(ARGS.project)
os.environ["EDIT_FMT"] = "youtube"
os.environ["EDIT_SS"] = "1"

import cv2  # noqa: E402
import numpy as np  # noqa: E402

import engine as E  # noqa: E402
from engine import INK, WHITE, W, H, draw_text, fill, font, rrect, stroke, text_width  # noqa: E402
from gfx import icon  # noqa: E402
from imgio import imwrite  # noqa: E402


def source(sf):
    r = E.ClipReader(sf, 1)
    f = r.next().copy()
    r.close()
    return f


def cam_for(z, fx_screen, fy_screen, spk=None):
    spk = spk or next(iter(E.FACE))
    fx, fy, _ = E.FACE[spk]
    return E.clamp_cam(fx - (fx_screen - W / 2) / (z * E.BASE), fy - (fy_screen - H / 2) / (z * E.BASE), z)


def pop(img, matte, keep_x0):
    """darken / desaturate everything except the person right of keep_x0 (screen px)."""
    m = matte.astype(np.float32) / 255.0
    if keep_x0 > 0:
        m[:, :int(keep_x0)] *= np.linspace(0, 1, int(keep_x0))[None, :] ** 3
    m = cv2.GaussianBlur(m, (0, 0), 6)[..., None]
    f = img.astype(np.float32)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)[..., None]
    sat = g + (f - g) * 1.12
    sat = (sat - 128) * 1.06 + 128
    # keep the background's colour: dimming a graded sunset much further turns it to mud at thumbnail size
    dim = sat * 0.84
    out = dim * (1 - m) + sat * m
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1 - 0.22 * np.clip(((xx - W * 0.62) / W) ** 2 * 2.2 + ((yy - H * 0.45) / H) ** 2 * 2.0 - 0.08, 0, 1)
    return np.clip(out * v[..., None], 0, 255).astype(np.uint8)


def compose(sf, cam, draw_behind, draw_front, keep_x0=0):
    fr = source(sf)
    M = E.view_matrix(cam, (0, 0))
    base = cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    base = E.detail(base, cam[2] * E.BASE)
    mt = E.matte_to_view(E.load_matte(sf), M, (W, H))
    base = pop(base, mt, keep_x0)
    behind, front = E.Layer(), E.Layer()
    behind.begin()
    front.begin()
    draw_behind(behind)
    bp, bb = behind.pixels()
    if bp is not None:
        y0, y1, x0, x1 = bb[1], bb[3], bb[0], bb[2]
        E.behind_premul(base[y0:y1, x0:x1], bp[y0:y1, x0:x1], mt[y0:y1, x0:x1])
    draw_front(front)
    fp, fb = front.pixels()
    if fp is not None:
        y0, y1, x0, x1 = fb[1], fb[3], fb[0], fb[2]
        E.over_premul(base[y0:y1, x0:x1], fp[y0:y1, x0:x1])
    return cv2.resize(base, (1280, 720), interpolation=cv2.INTER_AREA)


def pill(L, x, y, text, size, accent, icon_kind=None):
    f = font("bold", size)
    tw = text_width(text, f)
    ic = size * 1.1 if icon_kind else 0
    padx, h = size * 0.8, size * 2.0
    w = tw + ic + (size * 0.45 if icon_kind else 0) + padx * 2
    c = L.c
    c.drawRRect(rrect(x, y - h / 2, x + w, y + h / 2, h / 2), fill(INK, 215))
    c.drawRRect(rrect(x, y - h / 2, x + w, y + h / 2, h / 2), stroke(accent, 255, width=4))
    tx = x + padx
    if icon_kind:
        icon(c, icon_kind, tx + ic / 2, y, ic, accent, 255, sw=size * 0.12)
        tx += ic + size * 0.45
    m = f.getMetrics()
    draw_text(L, text, f, tx, y + (-m.fAscent - m.fDescent) / 2, rgb=WHITE, align="left")
    L.mark(x, y - h, x + w, y + h)


if __name__ == "__main__":
    sys.path.insert(0, E.PROJECT)
    sys.modules["thumbnail"] = sys.modules["__main__"]   # thumbs.py imports the helpers from here
    import thumbs
    outdir = os.path.abspath(ARGS.outdir or os.path.join(E.PROJECT, "output"))
    os.makedirs(outdir, exist_ok=True)
    for name, fn in thumbs.THUMBS.items():
        p = os.path.join(outdir, name)
        imwrite(p, fn(), [cv2.IMWRITE_JPEG_QUALITY, 92])
        print(p, os.path.getsize(p) // 1024, "KB")
