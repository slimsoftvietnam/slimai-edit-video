"""Render a project in one format.

python render.py --project P --fmt youtube --parallel 3 OUT.mp4            (1080p, N worker processes + concat)
python render.py --project P --fmt tiktok  --parallel 3 OUT.mp4
python render.py --project P --fmt youtube --ss 2 --parallel 3 OUT.mp4     (4K, only when asked for: much slower)
    Parallel renders work through ~10 s chunks kept in OUT_parts/. Run the same command again after an
    interruption and finished chunks are kept, unless the design, timeline or settings changed.
python render.py --project P --fmt tiktok  --range 10 20 OUT.mp4           (one process, a time range)
python render.py --project P --fmt youtube --stills DIR 3.2 10.5 ...       (JPEG stills for layout review)
python render.py --project P --fmt youtube --stills DIR auto               (two stills per registered event)
"""
import argparse
import glob
import hashlib
import math
import os
import shutil
import subprocess
import sys
import time
from multiprocessing import Process, Queue

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--fmt", choices=["youtube", "tiktok"], required=True)
    ap.add_argument("--ss", type=int, default=1, help="render scale (youtube 2 = 3840x2160)")
    ap.add_argument("--parallel", type=int, default=0)
    ap.add_argument("--range", nargs=2, type=float)
    ap.add_argument("--crf", type=float, default=None)
    ap.add_argument("--stills", nargs="+", help="DIR t1 t2 ...")
    ap.add_argument("out", nargs="?")
    ARGS = ap.parse_args()
    os.environ["EDIT_PROJECT"] = os.path.abspath(ARGS.project)
    os.environ["EDIT_FMT"] = ARGS.fmt
    os.environ["EDIT_SS"] = str(ARGS.ss)
    if ARGS.crf is not None:
        os.environ["EDIT_CRF"] = str(ARGS.crf)

import cv2  # noqa: E402
import numpy as np  # noqa: E402

import engine as E  # noqa: E402
import story as D  # noqa: E402
from imgio import imwrite  # noqa: E402

D.load_design()
FPS = E.FPS
W, H, SS, OW, OH = E.W, E.H, E.SS, E.OW, E.OH
CLIPS = D.CLIPS
for c in CLIPS:
    c["src_f0"] = int(round(c["src_in"] * FPS))
    c["out_f0"] = int(round(c["out_in"] * FPS))
TOTAL_F = int(round(D.TOTAL * FPS))


# ----------------------------------------------------------------------------
# shot segments (clip shots + overrides), transitions
# ----------------------------------------------------------------------------
def _shot_raw(t):
    for (a, b, s) in D.SHOT_OVERRIDES:
        if a <= t < b:
            return s
    return D.clip_at(t)["shot"]


def build_segments():
    pts = sorted(set([c["out_in"] for c in CLIPS] + [a for a, b, s in D.SHOT_OVERRIDES] +
                     [b for a, b, s in D.SHOT_OVERRIDES] + [0.0, D.TOTAL]))
    pts = [p for p in pts if 0 <= p <= D.TOTAL]
    segs = []
    for a, b in zip(pts[:-1], pts[1:]):
        if b - a < 1e-6:
            continue
        s = _shot_raw((a + b) / 2)
        if segs and segs[-1][2] == s:
            segs[-1][1] = b
        else:
            segs.append([a, b, s])
    # absorb ultra-short segments (< 0.5 s) into the previous one to avoid flicker
    out = []
    for sg in segs:
        if out and sg[1] - sg[0] < 0.5 and E.SHOTS[sg[2]]["spk"] == E.SHOTS[out[-1][2]]["spk"]:
            out[-1][1] = sg[1]
        else:
            out.append(sg)
    return out


SEGS = build_segments()


def seg_at(t):
    for i, s in enumerate(SEGS):
        if s[0] <= t < s[1]:
            return i
    return len(SEGS) - 1


def punch(t):
    z = 0.0
    for (tp, amt, att, hold, rel) in D.PUNCHES:
        if t < tp or t > tp + att + hold + rel:
            continue
        if t < tp + att:
            f = E.ease_out_cubic((t - tp) / att)
        elif t < tp + att + hold:
            f = 1.0
        else:
            f = 1 - E.ease_in_out_sine((t - tp - att - hold) / rel)
        z += amt * f
    return z


WHIP_PRE, WHIP_POST = 0.12, 0.20
JUMP = 1.03


def pip_amount(t):
    for (a, b) in D.PIP:
        if a <= t <= b + D.PIP_T:
            return E.ease_in_out_cubic(min(1.0, (t - a) / D.PIP_T, (b + D.PIP_T - t) / D.PIP_T))
    return 0.0


def pip_rect(p):
    x0, y0, x1, y1 = D.PIP_RECT
    return (x0 * p, y0 * p, W + (x1 - W) * p, H + (y1 - H) * p)


def camera(t):
    """-> cam (cx, cy, z, ox, oy), whip speed px/frame, overlay alpha, pip amount, view rect (layout px)."""
    i = seg_at(t)
    a, b, shot = SEGS[i]
    cx, cy, z = E.shot_cam(shot)
    # slow push-in across the segment
    z *= 1 + 0.03 * E.ease_in_out_sine(E.clamp01((t - a) / max(0.5, b - a)))
    # settle after same-speaker cut
    if i > 0 and E.SHOTS[SEGS[i - 1][2]]["spk"] == E.SHOTS[shot]["spk"]:
        z *= 1 + 0.025 * (1 - E.ease_out_cubic(E.clamp01((t - a) / 0.35)))
    # jump cuts inside a segment: alternate a small punch-in so cuts read as intentional
    cuts = [c["out_in"] for c in CLIPS if a + 0.05 < c["out_in"] <= t and c["frames"] >= 12]
    if len(cuts) % 2 == 1:
        z *= JUMP
    z *= 1 + punch(t)
    if t > D.DUR:
        z *= 1 + 0.05 * E.ease_in_out_sine((t - D.DUR) / D.END_HOLD)
    # push-ins, jump-cut punches and word punches must not stack into a tight face shot
    if z > E.ZKNEE:
        z = E.ZKNEE + (z - E.ZKNEE) * 0.5
    # handheld drift (source px)
    cx += 1.6 * math.sin(2 * math.pi * 0.21 * t + 0.7) + 0.7 * math.sin(2 * math.pi * 0.53 * t + 2.1)
    cy += 1.0 * math.sin(2 * math.pi * 0.17 * t + 1.3) + 0.5 * math.sin(2 * math.pi * 0.47 * t + 0.2)
    speed = 0.0
    ov_a = 1.0
    # whip pans at speaker changes
    for j in (i, i + 1):
        if 0 < j < len(SEGS):
            tb = SEGS[j][0]
            sa, sb = SEGS[j - 1][2], SEGS[j][2]
            if E.SHOTS[sa]["spk"] != E.SHOTS[sb]["spk"] and tb - WHIP_PRE <= t < tb + WHIP_POST:
                u = (t - (tb - WHIP_PRE)) / (WHIP_PRE + WHIP_POST)
                e = E.ease_in_out_cubic(u)
                A_, B_ = E.shot_cam(sa), E.shot_cam(sb)
                cx = A_[0] + (B_[0] - A_[0]) * e
                cy = A_[1] + (B_[1] - A_[1]) * e
                z = A_[2] + (B_[2] - A_[2]) * e
                e2 = E.ease_in_out_cubic(min(1, u + 0.02))
                speed = abs(B_[0] - A_[0]) * (e2 - e) / (0.02 * (WHIP_PRE + WHIP_POST)) / FPS
                ov_a = 1 - E.clamp01(math.sin(math.pi * u) * 1.7)
    cx, cy, z = E.clamp_cam(cx, cy, z)
    p = pip_amount(t)
    if p <= 0:
        return (cx, cy, z, W / 2, H / 2), speed, ov_a, 0.0, (0, 0, W, H)
    # picture-in-picture: the view rect shrinks; the source window glides to what the card shows.
    # Vertical formats open up from the 9:16 crop to the whole wide shot on the way.
    rect = pip_rect(p)
    rw, rh = rect[2] - rect[0], rect[3] - rect[1]
    cw, ch = D.PIP_RECT[2] - D.PIP_RECT[0], D.PIP_RECT[3] - D.PIP_RECT[1]
    spk = E.SHOTS[SEGS[i][2]]["spk"]
    vcx, vcy, vs = E.card_view(spk, cw, ch)
    vcx += 1.2 * math.sin(2 * math.pi * 0.19 * t + 0.4)
    vcy += 0.8 * math.sin(2 * math.pi * 0.23 * t + 1.1)
    h_src = H / (z * E.BASE) + (ch / vs - H / (z * E.BASE)) * p
    s = rh / h_src
    w_src = rw / s
    if w_src > E.SRC_W:
        s, w_src, h_src = rw / E.SRC_W, E.SRC_W, rh / (rw / E.SRC_W)
    cx, cy = cx + (vcx - cx) * p, cy + (vcy - cy) * p
    cx = min(max(cx, w_src / 2), E.SRC_W - w_src / 2)
    cy = min(max(cy, h_src / 2), E.SRC_H - h_src / 2)
    return (cx, cy, s / E.BASE, (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2), speed * (1 - p), ov_a, p, rect


# ----------------------------------------------------------------------------
# frame context
# ----------------------------------------------------------------------------
class Ctx:
    def __init__(self):
        self.behind = E.Layer()
        self.mid = E.Layer()      # diagram content: sits on the stage, under the PiP speaker card
        self.front = E.Layer()
        self.ui = E.Layer()
        self.reset()

    def reset(self):
        self.glass = []
        self.cctv = 0.0
        self.leak = None
        self.end = 0.0
        self.caption_box = None
        self.cap_y = D.CAP_Y
        self.pip = 0.0
        self.pip_rect = None


FINISH = None


# the "iphone" look (the default) is the camera's own colour: no film grain, halation, vignette or light leaks
NATURAL = E.CFG.get("look", "iphone") == "iphone"


def get_finish():
    global FINISH
    if FINISH is None:
        look = E.CFG.get("finish", {})
        # platform codecs eat grain first: TikTok's low bitrate gets the lightest coat
        grain = float(os.environ.get("EDIT_GRAIN", look.get("grain", 0.0 if NATURAL else (1.3 if D.YT else 1.0))))
        hal = float(os.environ.get("EDIT_HALATION", look.get("halation", 0.0 if NATURAL else 0.7)))
        FINISH = E.Finish(vignette=look.get("vignette", 0.0 if NATURAL else 0.20), grain=grain, halation=hal)
    return FINISH


def make_leak():
    lw, lh = OW * 3 // 8, OH // 8
    yy, xx = np.mgrid[0:lh, 0:lw].astype(np.float32)
    img = np.zeros((lh, lw, 3), np.float32)
    uw, uh = OW / 8, OH / 8
    for (cx, cy, rx, ry, rgb, a) in ((uw * 1.5, uh * 0.35, uw * 0.48, uh * 0.85, (255, 150, 60), 1.0),
                                    (uw * 1.2, uh * 0.6, uw * 0.35, uh * 0.65, (255, 200, 120), 0.7),
                                    (uw * 1.85, uh * 0.25, uw * 0.28, uh * 0.46, (255, 110, 70), 0.6)):
        d = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
        img += (np.exp(-d * 1.4) * a)[..., None] * np.array(rgb[::-1], np.float32)[None, None, :]
    return np.clip(img, 0, 255).astype(np.uint8)


LEAK = make_leak()


def scrim_u8():
    y0, y1 = max(0, (D.CAP_Y - 230)) * SS, min(H, D.CAP_Y + 190) * SS
    yy, xx = np.mgrid[y0:y1, 0:OW].astype(np.float32)
    rx, ry = D.SCRIM_R
    d = ((xx / SS - W / 2) / rx) ** 2 + ((yy / SS - (D.CAP_Y - 22)) / ry) ** 2
    m = np.clip((1 - 0.30 * np.exp(-d * 1.6)) * 255, 0, 255).astype(np.uint8)
    return y0, y1, cv2.merge([m, m, m])


SC_Y0, SC_Y1, SCRIM = scrim_u8()


def warp_view(frame, cam, rect, speed, p):
    """source frame -> canvas covering `rect` (device px), plus the matrix that did it."""
    x0, y0, x1, y1 = [int(round(v * SS)) for v in rect]
    w, h = x1 - x0, y1 - y0
    M = E.view_matrix(cam, (x0 / SS, y0 / SS))
    s = cam[2] * E.BASE * SS
    if s >= 0.75:
        img = cv2.warpAffine(frame, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        if speed >= 2.0:
            # horizontal motion blur = camera travel during a 1.2-frame shutter (device px)
            k = int(speed * s * 1.2)
            if k >= 3:
                k1 = max(3, k // 2 * 2 + 1)
                img = cv2.blur(img, (k1, 1), borderType=cv2.BORDER_REFLECT)
                img = cv2.blur(img, (max(3, (k1 // 2) | 1), 1), borderType=cv2.BORDER_REFLECT)
        elif p < 0.5:
            img = E.detail(img, s)
    else:
        # strong downscale into the card: supersample, then area-average for a crisp small picture
        img = cv2.warpAffine(frame, M * 2.0, (w * 2, h * 2), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        img = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
    return img, M, (x0, y0, x1, y1)


def make_stage(frame, spk):
    """blurred wide shot at full and at half brightness: the backdrop while the speaker sits in the card."""
    cx, cy, z = E.shot_cam(f"{spk}_wide")
    small = cv2.resize(frame, (E.SRC_W // 4, E.SRC_H // 4), interpolation=cv2.INTER_AREA)
    s = z * E.BASE * SS / 8 * 4
    M = np.array([[s, 0, OW / 16 - s * cx / 4], [0, s, OH / 16 - s * cy / 4]], np.float64)
    low = cv2.warpAffine(small, M, (OW // 8, OH // 8), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    bright = cv2.resize(cv2.GaussianBlur(low, (0, 0), 3.0), (OW, OH), interpolation=cv2.INTER_LINEAR)
    return bright, cv2.multiply(bright, np.full_like(bright, 128), scale=1 / 255.0)


def pip_stage(frame, view, vbox, ctx, p):
    bright, stage = make_stage(frame, ctx.spk)
    for g in ctx.glass:
        E.glass_from(bright, stage, *g)
    mp, mb = ctx.mid.pixels()
    if mp is not None:
        E.over_premul(stage[mb[1]:mb[3], mb[0]:mb[2]], mp[mb[1]:mb[3], mb[0]:mb[2]])
    x0, y0, x1, y1 = vbox
    # soft drop shadow, only around the card
    pad = 72 * SS
    X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(OW, x1 + pad), min(OH, y1 + 18 * SS + pad)
    sh = np.zeros(((Y1 - Y0) // 4 + 1, (X1 - X0) // 4 + 1), np.float32)
    cv2.rectangle(sh, ((x0 - X0) // 4, (y0 - Y0 + 18 * SS) // 4), ((x1 - X0) // 4, (y1 - Y0 + 18 * SS) // 4), 1.0, -1)
    sh = cv2.resize(cv2.GaussianBlur(sh, (0, 0), 7 * SS), (X1 - X0, Y1 - Y0), interpolation=cv2.INTER_LINEAR)
    k = np.clip(255 * (1 - 0.6 * p * sh), 0, 255).astype(np.uint8)
    stage[Y0:Y1, X0:X1] = cv2.multiply(stage[Y0:Y1, X0:X1], cv2.merge([k, k, k]), scale=1 / 255.0)
    # paste the card, blending only its rounded corners
    w, h = x1 - x0, y1 - y0
    r = min(28 * p * SS, w / 2, h / 2)
    corners = []
    if r >= 0.5:
        a = E.corner_alpha(r)
        ri = a.shape[0]
        for (cy_, cx_, ac) in ((0, 0, a), (0, w - ri, a[:, ::-1]), (h - ri, 0, a[::-1, :]), (h - ri, w - ri, a[::-1, ::-1])):
            corners.append((cy_, cx_, ac[..., None], stage[y0 + cy_:y0 + cy_ + ri, x0 + cx_:x0 + cx_ + ri].astype(np.float32)))
    stage[y0:y1, x0:x1] = view
    for (cy_, cx_, ac, bg) in corners:
        ri = ac.shape[0]
        fg = view[cy_:cy_ + ri, cx_:cx_ + ri].astype(np.float32)
        stage[y0 + cy_:y0 + cy_ + ri, x0 + cx_:x0 + cx_ + ri] = (fg * ac + bg * (1 - ac)).astype(np.uint8)
    return stage


def apply_cctv(img, v):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g3 = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR).astype(np.float32)
    f = img.astype(np.float32)
    mono = g3 * np.array([0.95, 1.05, 0.92], np.float32)  # BGR: slight green tint
    mix = f * (1 - 0.65 * v) + mono * (0.65 * v)
    mix[::4 * SS] *= 1 - 0.10 * v
    mix = (mix - 128) * (1 + 0.12 * v) + 128
    return np.clip(mix, 0, 255).astype(np.uint8)


def compose(frame, src_f, t, f, ctx):
    if src_f is not None:
        E.use_take(src_f / FPS)
    cam, speed, ov_a, pp, rect = camera(t)
    ctx.reset()
    ctx.cam = cam
    ctx.pip, ctx.pip_rect = pp, (rect if pp > 0 else None)
    ctx.spk = E.SHOTS[SEGS[seg_at(t)][2]]["spk"]
    for L in (ctx.behind, ctx.mid, ctx.front, ctx.ui):
        L.begin()
    D.draw(ctx, t)
    view, M, vbox = warp_view(frame, cam, rect, speed, pp)
    x0, y0, x1, y1 = vbox
    bp, bb = ctx.behind.pixels()
    if bp is not None:
        ix0, iy0, ix1, iy1 = max(bb[0], x0), max(bb[1], y0), min(bb[2], x1), min(bb[3], y1)
        if ix1 > ix0 and iy1 > iy0:
            ov = bp[iy0:iy1, ix0:ix1]
            if ov_a < 1.0:
                ov = cv2.multiply(np.ascontiguousarray(ov), np.full_like(ov, int(255 * ov_a)), scale=1 / 255.0)
            sub = view[iy0 - y0:iy1 - y0, ix0 - x0:ix1 - x0]
            m = E.load_matte(src_f) if src_f is not None else None
            if m is not None:
                mt = E.matte_to_view(m, M, (x1 - x0, y1 - y0))[iy0 - y0:iy1 - y0, ix0 - x0:ix1 - x0]
                E.behind_premul(sub, ov, mt)
            else:
                E.over_premul(sub, ov)
    base = pip_stage(frame, view, vbox, ctx, pp) if pp > 0 else view
    if ctx.cctv > 0:
        base = apply_cctv(base, ctx.cctv)
    if ctx.leak is not None and not NATURAL:
        p, strength = ctx.leak
        a = math.sin(math.pi * p) * strength
        lw = OW // 8
        x0_ = int((1 - p) * 2 * lw)
        lk = cv2.resize(LEAK[:, x0_:x0_ + lw], (OW, OH), interpolation=cv2.INTER_LINEAR)
        lk = cv2.multiply(lk, np.full_like(lk, int(a * 255)), scale=1 / 255.0)
        inv = cv2.multiply(cv2.bitwise_not(base), cv2.bitwise_not(lk), scale=1 / 255.0)
        base = cv2.bitwise_not(inv)
    if ctx.end > 0:
        e = ctx.end
        bl = cv2.GaussianBlur(cv2.resize(base, (OW // 4, OH // 4), interpolation=cv2.INTER_AREA), (0, 0), 3 * e + 0.1)
        bl = cv2.resize(bl, (OW, OH), interpolation=cv2.INTER_LINEAR)
        base = cv2.addWeighted(base, 1 - e, bl, e, 0)
        base = cv2.multiply(base, np.full_like(base, int(255 * (1 - 0.45 * e))), scale=1 / 255.0)
    if pp <= 0:
        for g in ctx.glass:
            gx0, gy0, gx1, gy1, r, a = g
            E.glass(base, gx0, gy0, gx1, gy1, r=r, sigma=18, alpha=a, tint_a=0.38, bright=0.92)
        mp, mb = ctx.mid.pixels()
        if mp is not None:
            E.over_premul(base[mb[1]:mb[3], mb[0]:mb[2]], mp[mb[1]:mb[3], mb[0]:mb[2]])
    if ctx.caption_box is not None:
        base[SC_Y0:SC_Y1] = cv2.multiply(base[SC_Y0:SC_Y1], SCRIM, scale=1 / 255.0)
    base = get_finish()(base, f)
    fp, fb = ctx.front.pixels()
    if fp is not None:
        ov = fp[fb[1]:fb[3], fb[0]:fb[2]]
        if ov_a < 1.0:
            ov = cv2.multiply(np.ascontiguousarray(ov), np.full_like(ov, int(255 * ov_a)), scale=1 / 255.0)
        E.over_premul(base[fb[1]:fb[3], fb[0]:fb[2]], ov)
    up, ub = ctx.ui.pixels()
    if up is not None:
        E.over_premul(base[ub[1]:ub[3], ub[0]:ub[2]], up[ub[1]:ub[3], ub[0]:ub[2]])
    return base


# ----------------------------------------------------------------------------
# frame loop
# ----------------------------------------------------------------------------
def clip_index_for_frame(f):
    for i, c in enumerate(CLIPS):
        if c["out_f0"] <= f < c["out_f0"] + c["frames"]:
            return i
    return None


def encoder(out_path):
    # quality-first mezzanine: the platform re-encodes anyway, so what matters is giving it clean detail
    crf = os.environ.get("EDIT_CRF", "15" if SS == 1 else "18")
    # few threads and a shorter lookahead at 4K: compositing is the bottleneck, and every frame x264 holds costs
    # tens of MB, enough to push a 16 GB machine into paging
    tune = "rc-lookahead=50:ref=4:bframes=4:threads=4" if SS == 1 else "rc-lookahead=25:ref=3:bframes=3:threads=3"
    params = f"aq-mode=3:aq-strength=0.8:deblock=-1,-1:psy-rd=1.0,0.12:{tune}"
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{OW}x{OH}", "-r", str(FPS),
           "-i", "-", "-vf", "scale=out_color_matrix=bt709:flags=lanczos+accurate_rnd+full_chroma_int,format=yuv420p",
           "-c:v", "libx264", "-preset", "slow", "-crf", crf, "-profile:v", "high", "-colorspace", "bt709",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", "-x264-params", params, out_path]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


_CTX = None


def render_range(f0, f1, out_path, log_every=150):
    global _CTX
    cv2.setNumThreads(int(os.environ.get("EDIT_CV_THREADS", "4")))
    _CTX = _CTX or Ctx()
    ctx = _CTX
    enc = encoder(out_path)
    reader, cur_clip, last_frame, last_src = None, None, None, None
    tstart = time.time()
    for f in range(f0, f1):
        t = f / FPS
        ci = clip_index_for_frame(f)
        if ci is not None:
            c = CLIPS[ci]
            if ci != cur_clip:
                if reader:
                    reader.close()
                off = f - c["out_f0"]
                reader = E.ClipReader(c["src_f0"] + off, c["frames"] - off)
                cur_clip = ci
            frame = reader.next()
            src_f = c["src_f0"] + (f - c["out_f0"])
            last_frame, last_src = frame, src_f
        else:
            if last_frame is None:
                # a chunk that starts in a gap (a trailer card) or in the end hold: freeze the clip before it
                c = D.clip_at(t)
                rd = E.ClipReader(c["src_f0"] + c["frames"] - 1, 1)
                last_frame = rd.next()
                rd.close()
                last_src = c["src_f0"] + c["frames"] - 1
            frame, src_f = last_frame, last_src
        out = compose(frame, src_f, t, f, ctx)
        enc.stdin.write(out.data if out.flags.c_contiguous else out.tobytes())
        if (f - f0 + 1) % log_every == 0:
            el = time.time() - tstart
            print(f"[{os.path.basename(out_path)}] frame {f - f0}/{f1 - f0}  {el / max(1, f - f0 + 1) * 1000:.0f} ms/f", flush=True)
    if reader:
        reader.close()
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError(f"encoder failed for {out_path}")


def event_times():
    """for `--stills DIR auto`: two moments per registered event + the end card, de-duplicated."""
    ts = set()
    for (t0, t1, _fn) in D.EVENTS:
        t0, t1 = max(0.0, t0), min(D.TOTAL - 0.05, t1)
        for u in (0.35, 0.82):
            ts.add(round(t0 + (t1 - t0) * u, 2))
    return sorted(ts)


def stills(outdir, times):
    os.makedirs(outdir, exist_ok=True)
    ctx = Ctx()
    for t in times:
        f = int(round(t * FPS))
        ci = clip_index_for_frame(f)
        c = CLIPS[ci] if ci is not None else D.clip_at(f / FPS)
        src_f = c["src_f0"] + (f - c["out_f0"]) if ci is not None else c["src_f0"] + c["frames"] - 1
        rd = E.ClipReader(src_f, 1)
        frame = rd.next()
        rd.close()
        out = compose(frame, src_f, f / FPS, f, ctx)
        imwrite(os.path.join(outdir, f"still_{t:07.2f}.jpg"), out, [cv2.IMWRITE_JPEG_QUALITY, 92])


def _worker(jobs):
    """take chunks until the queue is empty; a chunk only gets its final name once it is complete."""
    while True:
        job = jobs.get()
        if job is None:
            return
        f0, f1, path = job
        t0 = time.time()
        render_range(f0, f1, path + ".tmp.mp4", log_every=10 ** 9)
        os.replace(path + ".tmp.mp4", path)
        print(f"chunk {f0}-{f1} done, {(time.time() - t0) / (f1 - f0) * 1000:.0f} ms/f", flush=True)


def chunk_bounds(size=300):
    """chunk edges near every `size` frames, moved onto a nearby cut when there is one (a keyframe belongs there)."""
    cuts = [c["out_f0"] for c in CLIPS]
    bounds = [0]
    while bounds[-1] + size * 3 // 2 < TOTAL_F:
        target = bounds[-1] + size
        near = [c for c in cuts if abs(c - target) <= size // 3]
        bounds.append(min(near, key=lambda c: abs(c - target)) if near else target)
    return bounds + [TOTAL_F]


def signature():
    """chunks are reusable only if nothing that shapes the picture has changed."""
    settings = [E.FMT, SS] + [os.environ.get(k) for k in ("EDIT_CRF", "EDIT_GRAIN", "EDIT_HALATION", "EDIT_DETAIL")]
    h = hashlib.sha1(repr(settings).encode())
    here = os.path.dirname(os.path.abspath(__file__))
    files = [os.path.join(E.PROJECT, n) for n in ("design.py", "timeline.json", "project.json", "master_index.json")]
    files += [os.path.join(here, n) for n in ("engine.py", "story.py", "gfx.py", "render.py")]
    for p in files:
        with open(p, "rb") as fh:
            h.update(fh.read())
    h.update(str(os.path.getsize(E.MASTER)).encode())
    return h.hexdigest()


def render_parallel(out, n):
    parts_dir = os.path.splitext(out)[0] + "_parts"
    os.makedirs(parts_dir, exist_ok=True)
    sig_path = os.path.join(parts_dir, "signature.txt")
    sig = signature()
    if not os.path.exists(sig_path) or open(sig_path).read() != sig:
        for p in glob.glob(os.path.join(glob.escape(parts_dir), "*.mp4")):
            os.remove(p)
        with open(sig_path, "w") as fh:
            fh.write(sig)
    for p in glob.glob(os.path.join(glob.escape(parts_dir), "*.tmp.mp4")):
        os.remove(p)
    bounds = chunk_bounds()
    chunks = [(a, b, os.path.join(parts_dir, f"part_{a:06d}_{b:06d}.mp4")) for a, b in zip(bounds[:-1], bounds[1:])]
    todo = [c for c in chunks if not os.path.exists(c[2])]
    print(f"{len(chunks)} chunks, {len(chunks) - len(todo)} already done", flush=True)
    jobs = Queue()
    for c in todo:
        jobs.put(c)
    for _ in range(n):
        jobs.put(None)
    procs = [Process(target=_worker, args=(jobs,)) for _ in range(n)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    missing = [c[2] for c in chunks if not os.path.exists(c[2])]
    if missing:
        sys.exit(f"{len(missing)} chunks failed; run the same command again to resume")
    lst = os.path.join(parts_dir, "list.txt")
    with open(lst, "w", encoding="utf-8") as fh:
        for c in chunks:
            escaped = os.path.abspath(c[2]).replace("'", "'\\''")
            fh.write(f"file '{escaped}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    shutil.rmtree(parts_dir)
    print("done", out, flush=True)


if __name__ == "__main__":
    if ARGS.stills:
        ask = ARGS.stills[1:]
        stills(ARGS.stills[0], event_times() if ask == ["auto"] else [float(x) for x in ask])
    elif ARGS.parallel:
        render_parallel(ARGS.out, ARGS.parallel)
    else:
        t0, t1 = ARGS.range if ARGS.range else (0.0, D.TOTAL)
        render_range(int(round(t0 * FPS)), int(round(t1 * FPS)), ARGS.out)
