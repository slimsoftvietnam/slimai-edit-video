"""Motion effects for the motion style's hook and retention beats (references/motion.md; approved on tập 16).
The user, 2026-11-25: "2s đầu bằng mọi cách phải giữ chân được user… hãy dùng hiệu ứng đẹp, mới lạ và viral nhất bạn
biết trong các video motion, giữ chân user đến giây cuối, hãy tự đề xuất".

- mask_title():   the frame is black and the title's letters are windows onto the video; then the camera flies
                  through a letter into the picture (the "text mask zoom-through" opener).
- backdrop():     the background behind the speaker becomes a flat colour with a slow sunburst (studio swap), for a
                  second or two; sticker(): a white outline around the cut-out speaker, like a paper sticker.
- shockwave(), speedlines(): a ring and radial streaks that leave from behind the speaker on a drop.
- doodles:        underline(), circle(), arrow() drawn on by hand (two marker passes, a little wobble).
- extrude():      a big word with a solid 3D side.
- story_bar():    a thin segmented progress bar (how many parts are left).
- beat_pulses():  tiny camera pulses on the music's beats after a drop.
Everything that must sit behind the speaker is drawn on ctx.behind (the engine cuts it with the person matte).
"""
import math
import random

import cv2
import numpy as np
import skia

import engine as E
import rawstyle as RS
import story as S
from engine import FPS, H, OH, OW, SS, W, c4, clamp01, ease_out_cubic, font, nfc


def ease_in_expo(x):
    x = clamp01(x)
    return 0.0 if x <= 0 else 2 ** (10 * (x - 1))


# ----------------------------------------------------------------------------
# the person matte in screen space (for the sticker outline)
# ----------------------------------------------------------------------------
def src_frame_at(t):
    f = int(round(t * FPS))
    for c in S.CLIPS:
        f0 = int(round(c["out_in"] * FPS))
        if f0 <= f < f0 + c["frames"]:
            return int(round(c["src_in"] * FPS)) + (f - f0)
    c = S.clip_at(t)
    return int(round(c["src_in"] * FPS)) + c["frames"] - 1


def matte_view(ctx, t):
    """the person matte warped to the output frame (uint8, OH x OW), or None"""
    m = E.load_matte(src_frame_at(t))
    if m is None:
        return None
    M = E.view_matrix(ctx.cam, (0, 0))
    return E.matte_to_view(m, M, (OW, OH))


def _over(arr, box, alpha, rgb):
    """premultiplied `rgb` with float alpha (h, w) over the BGRA premul layer array, inside box"""
    x0, y0, x1, y1 = box
    sub = arr[y0:y1, x0:x1].astype(np.float32)
    al = alpha[..., None]
    col = np.array([rgb[2], rgb[1], rgb[0], 255.0], np.float32)
    arr[y0:y1, x0:x1] = np.clip(col * al + sub * (1 - al), 0, 255).astype(np.uint8)


def sticker(ctx, t, a=1.0, r=13, rgb=(255, 255, 255), shadow=0.4, shadow_off=(10, 16)):
    """a white outline around the cut-out speaker (drawn behind them: the person covers its inside), with a soft drop
    shadow, like a paper sticker. a = 0..1"""
    if a <= 0:
        return
    mt = matte_view(ctx, t)
    if mt is None:
        return
    ys, xs = np.where(mt > 40)
    if len(xs) == 0:
        return
    pad = int((r + 30) * SS)
    x0, x1 = max(0, xs.min() - pad), min(OW, xs.max() + pad)
    y0, y1 = max(0, ys.min() - pad), min(OH, ys.max() + pad)
    sub = mt[y0:y1, x0:x1]
    rr = int(r * SS)
    dil = cv2.dilate(sub, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rr + 1, 2 * rr + 1)))
    dil = cv2.GaussianBlur(dil, (0, 0), 1.3 * SS).astype(np.float32) / 255.0
    L = ctx.behind
    if shadow > 0:
        sh = cv2.GaussianBlur(dil, (0, 0), 9 * SS)
        Msh = np.float32([[1, 0, shadow_off[0] * SS], [0, 1, shadow_off[1] * SS]])
        sh = cv2.warpAffine(sh, Msh, (sh.shape[1], sh.shape[0]))
        _over(L.arr, (x0, y0, x1, y1), sh * shadow * a, (0, 0, 0))
    _over(L.arr, (x0, y0, x1, y1), dil * a, rgb)
    L.mark(x0 / SS, y0 / SS, x1 / SS, y1 / SS, pad=0)


def backdrop(ctx, t, a=1.0, rgb=(22, 60, 200), rgb2=None, cx=W / 2, cy=H * 0.5, rays=14, spin=0.25, reveal=None):
    """the background behind the speaker becomes a flat colour with a slow sunburst. reveal = (x, y, radius): only
    inside that circle (a circular wipe)"""
    if a <= 0:
        return
    L = ctx.behind
    c = L.c
    c.save()
    if reveal is not None:
        p = skia.Path()
        p.addCircle(reveal[0], reveal[1], max(1.0, reveal[2]))
        c.clipPath(p, skia.ClipOp.kIntersect, True)
    c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=c4(rgb, 255 * a)))
    rgb2 = rgb2 or tuple(min(255, int(v * 1.35 + 18)) for v in rgb)
    R = math.hypot(W, H)
    pr = skia.Paint(AntiAlias=True, Color=c4(rgb2, 255 * a))
    for i in range(rays):
        a0 = (i * 2 * math.pi / rays) + t * spin
        a1 = a0 + math.pi / rays
        ray = skia.Path()
        ray.moveTo(cx, cy)
        ray.lineTo(cx + R * math.cos(a0), cy + R * math.sin(a0))
        ray.lineTo(cx + R * math.cos(a1), cy + R * math.sin(a1))
        ray.close()
        c.drawPath(ray, pr)
    # a soft vignette of the base colour keeps the rays calm at the edges
    vg = skia.Paint(AntiAlias=True)
    vg.setShader(skia.GradientShader.MakeRadial(skia.Point(cx, cy), R * 0.62,
                                                [RS.argb(rgb, 0), RS.argb(rgb, int(150 * a))], [0.35, 1.0]))
    c.drawRect(skia.Rect.MakeWH(W, H), vg)
    c.restore()
    L.mark_all()


# ----------------------------------------------------------------------------
# the opener: letters as windows onto the video, then a flight through a letter
# ----------------------------------------------------------------------------
def mask_title(ctx, t, t0, t_zoom, zoom_dur, lines, pivot, kind="black", bg=(6, 8, 12), small=None, max_scale=70.0):
    """lines = [(text, size, baseline_y)], centred. Until t_zoom the frame is `bg` with the letters cut out; from
    t_zoom the camera flies through `pivot` (x, y inside a stroke of a letter) for zoom_dur s. small = (text, size, y,
    rgb): a plain line that is not cut out (it leaves as the flight starts)."""
    if t < t0 or t > t_zoom + zoom_dur:
        return
    k = ease_in_expo((t - t_zoom) / zoom_dur) if t >= t_zoom else 0.0
    s = 1.0 + (max_scale - 1.0) * k
    L = ctx.ui
    c = L.c
    c.saveLayer()
    c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=c4(bg, 255)))
    cut = skia.Paint(AntiAlias=True)
    cut.setBlendMode(skia.BlendMode.kDstOut)
    c.save()
    c.translate(pivot[0], pivot[1])
    c.scale(s, s)
    c.translate(-pivot[0], -pivot[1])
    for (text, size, y) in lines:
        f = font(kind, size)
        w = f.measureText(nfc(text))
        c.drawString(nfc(text), W / 2 - w / 2, y, f, cut)
    c.restore()
    if small is not None and k < 0.35:
        text, size, y, rgb = small
        f = font("bold", size)
        w = f.measureText(nfc(text))
        c.drawString(nfc(text), W / 2 - w / 2, y, f, skia.Paint(AntiAlias=True, Color=c4(rgb, 255 * (1 - k / 0.35))))
    c.restore()
    L.mark_all()


# ----------------------------------------------------------------------------
# energy from behind the speaker
# ----------------------------------------------------------------------------
def shockwave(ctx, t, t0, cx, cy, rgb=(255, 255, 255), dur=0.55, r1=1100.0, width=26.0, layer=None):
    u = (t - t0) / dur
    if u < 0 or u > 1:
        return
    L = layer or ctx.behind
    k = ease_out_cubic(u)
    r = 40 + (r1 - 40) * k
    p = skia.Paint(AntiAlias=True, Color=c4(rgb, 255 * (1 - u) ** 1.5))
    p.setStyle(skia.Paint.kStroke_Style)
    p.setStrokeWidth(max(2.0, width * (1 - 0.7 * u)))
    L.c.drawCircle(cx, cy, r, p)
    p2 = skia.Paint(AntiAlias=True, Color=c4(rgb, 120 * (1 - u) ** 2))
    p2.setStyle(skia.Paint.kStroke_Style)
    p2.setStrokeWidth(max(1.0, width * 0.35))
    L.c.drawCircle(cx, cy, r * 0.72, p2)
    L.mark_all()


def speedlines(ctx, t, t0, cx, cy, rgb=(255, 255, 255), dur=0.5, n=26, seed=3, layer=None):
    u = (t - t0) / dur
    if u < 0 or u > 1:
        return
    L = layer or ctx.behind
    rnd = random.Random(seed)
    k = ease_out_cubic(u)
    for i in range(n):
        ang = rnd.uniform(0, 2 * math.pi)
        r0 = rnd.uniform(160, 420) + 900 * k
        ln = rnd.uniform(120, 420) * (1 - 0.5 * u)
        wdt = rnd.uniform(3, 9)
        p = skia.Paint(AntiAlias=True, Color=c4(rgb, 200 * (1 - u) ** 1.3))
        p.setStrokeWidth(wdt)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        L.c.drawLine(cx + r0 * math.cos(ang), cy + r0 * math.sin(ang),
                     cx + (r0 + ln) * math.cos(ang), cy + (r0 + ln) * math.sin(ang), p)
    L.mark_all()


# ----------------------------------------------------------------------------
# hand-drawn marks
# ----------------------------------------------------------------------------
def _draw_poly(c, pts, k, rgb, a, width, seed=1):
    """the first fraction k of a polyline, as two marker passes with a little wobble"""
    n = max(2, int(len(pts) * clamp01(k)))
    rnd = random.Random(seed)
    for pas in range(2):
        path = skia.Path()
        for i, (x, y) in enumerate(pts[:n]):
            jx, jy = (rnd.uniform(-1.6, 1.6), rnd.uniform(-1.6, 1.6)) if pas else (0.0, 0.0)
            if i == 0:
                path.moveTo(x + jx, y + jy)
            else:
                path.lineTo(x + jx, y + jy)
        p = skia.Paint(AntiAlias=True, Color=c4(rgb, a * (1.0 if pas == 0 else 0.55)))
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(width * (1.0 if pas == 0 else 0.6))
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
        c.drawPath(path, p)


def underline(L, t, t0, x0, x1, y, rgb=RS.AQUA, a=255.0, width=11.0, dur=0.28, seed=1, waves=2.5, amp=7.0):
    k = ease_out_cubic(clamp01((t - t0) / dur))
    if k <= 0:
        return
    pts = [(x0 + (x1 - x0) * u, y + amp * math.sin(u * waves * 2 * math.pi) + 5 * u) for u in np.linspace(0, 1, 40)]
    _draw_poly(L.c, pts, k, rgb, a, width, seed)
    L.mark(x0 - 20, y - 30, x1 + 20, y + 40)


def circle(L, t, t0, cx, cy, rx, ry, rgb=RS.ORANGE, a=255.0, width=10.0, dur=0.4, seed=2, turns=1.12, start=-2.2):
    k = ease_out_cubic(clamp01((t - t0) / dur))
    if k <= 0:
        return
    pts = []
    for u in np.linspace(0, 1, 70):
        ang = start + u * turns * 2 * math.pi
        gr = 1.0 + 0.07 * u                       # the loop opens a little: it does not close on itself
        pts.append((cx + rx * gr * math.cos(ang), cy + ry * gr * math.sin(ang)))
    _draw_poly(L.c, pts, k, rgb, a, width, seed)
    L.mark(cx - rx * 1.2 - 20, cy - ry * 1.2 - 20, cx + rx * 1.2 + 20, cy + ry * 1.2 + 20)


def arrow(L, t, t0, x0, y0, x1, y1, bend=0.25, rgb=RS.ORANGE, a=255.0, width=10.0, dur=0.35, seed=4, head=34.0):
    k = ease_out_cubic(clamp01((t - t0) / dur))
    if k <= 0:
        return
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    nx, ny = -(y1 - y0), (x1 - x0)
    qx, qy = mx + nx * bend, my + ny * bend
    pts = []
    for u in np.linspace(0, 1, 40):
        pts.append(((1 - u) ** 2 * x0 + 2 * u * (1 - u) * qx + u * u * x1,
                    (1 - u) ** 2 * y0 + 2 * u * (1 - u) * qy + u * u * y1))
    _draw_poly(L.c, pts, k, rgb, a, width, seed)
    if k > 0.85:
        kh = clamp01((k - 0.85) / 0.15)
        ang = math.atan2(y1 - qy, x1 - qx)
        for da in (2.55, -2.55):
            _draw_poly(L.c, [(x1, y1), (x1 + head * kh * math.cos(ang + da), y1 + head * kh * math.sin(ang + da))],
                       1.0, rgb, a, width, seed + 1)
    L.mark(min(x0, x1, qx) - 60, min(y0, y1, qy) - 60, max(x0, x1, qx) + 60, max(y0, y1, qy) + 60)


def highlight(L, t, t0, x0, x1, y, h, rgb=(255, 226, 60), a=235.0, dur=0.22):
    """a highlighter swipe behind a word (draw it before the word)"""
    k = ease_out_cubic(clamp01((t - t0) / dur))
    if k <= 0:
        return
    c = L.c
    c.save()
    c.translate((x0 + x1) / 2, y)
    c.rotate(-1.6)
    c.translate(-(x0 + x1) / 2, -y)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0 - 10, y - h, x0 - 10 + (x1 - x0 + 20) * k, y + h * 0.18), 8, 8),
                skia.Paint(AntiAlias=True, Color=c4(rgb, a)))
    c.restore()
    L.mark(x0 - 30, y - h - 20, x1 + 30, y + h * 0.4 + 20)


# ----------------------------------------------------------------------------
# type
# ----------------------------------------------------------------------------
def extrude(c, text, f, x, y, a, rgb, side=(12, 16, 28), depth=16, edge=None):
    """a word with a solid 3D side going down-right (drawn back to front), then its face"""
    text = nfc(text)
    for i in range(int(depth), 0, -1):
        c.drawString(text, x + i * 0.9, y + i, f, skia.Paint(AntiAlias=True, Color=c4(side, a)))
    if edge is not None:
        ep = skia.Paint(AntiAlias=True, Color=c4(edge, a))
        ep.setStyle(skia.Paint.kStroke_Style)
        ep.setStrokeWidth(max(2.0, f.getSize() * 0.03))
        ep.setStrokeJoin(skia.Paint.kRound_Join)
        c.drawString(text, x, y, f, ep)
    c.drawString(text, x, y, f, skia.Paint(AntiAlias=True, Color=c4(rgb, a)))
    return f.measureText(text)


# ----------------------------------------------------------------------------
# retention
# ----------------------------------------------------------------------------
def story_bar(ctx, t, parts, t_in, t_out, y=258.0, x0=70.0, x1=1010.0, h=9.0, gap=10.0, rgb=RS.WHITE, fill=RS.AQUA):
    """parts = [(t0, t1)] in story order: a thin segmented bar, each segment filling while its part plays"""
    a = clamp01((t - t_in) / 0.3) * clamp01((t_out - t) / 0.2)
    if a <= 0:
        return
    L = ctx.front
    c = L.c
    n = len(parts)
    w = (x1 - x0 - gap * (n - 1)) / n
    for i, (p0, p1) in enumerate(parts):
        xs = x0 + i * (w + gap)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(xs, y + 3, w, h), h / 2, h / 2),
                    skia.Paint(AntiAlias=True, Color=c4((0, 0, 0), 90 * a)))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(xs, y, w, h), h / 2, h / 2),
                    skia.Paint(AntiAlias=True, Color=c4(rgb, 105 * a)))
        k = clamp01((t - p0) / max(0.05, p1 - p0))
        if k > 0:
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(xs, y, max(h, w * k), h), h / 2, h / 2),
                        skia.Paint(AntiAlias=True, Color=c4(fill, 255 * a)))
    L.mark(x0 - 10, y - 10, x1 + 10, y + h + 16)


def beat_pulses(t0, n, beat, amt=0.018, every=1):
    """tiny camera pulses on the music's beats from t0 (story.PUNCHES entries)"""
    for i in range(0, n, every):
        S.PUNCHES.append((t0 + i * beat - 0.02, amt, 0.05, 0.02, max(0.12, beat * 0.55)))


def glyph_point(lines, want, kind="black"):
    """a point well inside a glyph of the centred lines [(text, size, baseline_y)], as near `want` as possible: the
    pivot for mask_title's flight (the camera has to pass through a letter, not through the black between them)"""
    paths = []
    for (text, size, y) in lines:
        f = font(kind, size)
        gl = f.textToGlyphs(nfc(text))
        w = f.measureText(nfc(text))
        xs = f.getXPos(gl, W / 2 - w / 2)
        for g, x in zip(gl, xs):
            p = f.getPath(g)
            if p is not None:
                p.offset(x, y)
                paths.append(p)

    def inside(px, py):
        return any(p.contains(px, py) for p in paths)

    best = None
    for r in range(0, 420, 8):
        n = max(1, int(r / 5))
        for k in range(n):
            ang = 2 * math.pi * k / n
            px, py = want[0] + r * math.cos(ang), want[1] + r * math.sin(ang)
            if inside(px, py):
                if all(inside(px + dx, py + dy) for dx, dy in ((14, 0), (-14, 0), (0, 14), (0, -14))):
                    return (px, py)
                best = best or (px, py)
    return best or want
