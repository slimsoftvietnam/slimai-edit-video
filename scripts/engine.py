"""Rendering engine shared by every project and format.

Holds the project config, the 9:16 / 16:9 shot tables, the virtual camera, frame and matte sources,
skia overlay layers, compositing, the sharpening pass and the film finish (halation, grain, vignette).

Env: EDIT_PROJECT (project folder), EDIT_FMT (tiktok | youtube), EDIT_SS (render scale: youtube 2 = 4K).
All layout code works in layout pixels (W x H: 1080x1920 or 1920x1080); layers are scaled to device
pixels (OW x OH), so graphics stay vector-sharp at any render scale.

Skia 87.9 draws overlays; heavy per-pixel work goes through OpenCV uint8 ops, which are ~100x faster
on this build than translucent skia fills or numpy float math.
"""
import bisect
import json
import math
import os
import subprocess
import unicodedata
from collections import OrderedDict

import cv2
import numpy as np
import skia

from imgio import imread

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.environ.get("EDIT_PROJECT", os.getcwd())
CFG = json.load(open(os.path.join(PROJECT, "project.json"), encoding="utf-8"))
FMT = os.environ.get("EDIT_FMT", "youtube")
assert FMT in ("youtube", "tiktok"), FMT
SS = int(os.environ.get("EDIT_SS", "1"))
W, H = (1920, 1080) if FMT == "youtube" else (1080, 1920)
OW, OH = W * SS, H * SS
FPS = int(CFG.get("fps", 30))
SRC_W, SRC_H = int(CFG["src_w"]), int(CFG["src_h"])
BASE = max(H / SRC_H, W / SRC_W)      # layout px per source px at zoom 1.0 (cover fit)
FONT_DIR = os.path.join(SKILL_DIR, "assets", "fonts")
MASTER = os.path.join(PROJECT, "master.mkv")
MATTE_DIR = os.path.join(PROJECT, "matte")
_m = CFG.get("matte", {})
MCX, MCY = _m.get("crop", [0, 0, SRC_W, SRC_H])[:2]
MSCALE = float(_m.get("scale", 2.0))

# ----------------------------------------------------------------------------
# colours (RGB) and fonts
# ----------------------------------------------------------------------------
WHITE = (255, 251, 244)
AMBER = (255, 196, 98)
GOLD = (255, 214, 140)
CORAL = (255, 112, 92)
MINT = (128, 236, 206)
SKY = (150, 205, 255)
INK = (12, 16, 15)

FONTS = {
    "black": ("BeVietnamPro-Black.ttf", None),
    "xbold": ("BeVietnamPro-ExtraBold.ttf", None),
    "bold": ("BeVietnamPro-Bold.ttf", None),
    "semi": ("BeVietnamPro-SemiBold.ttf", None),
    "medium": ("BeVietnamPro-Medium.ttf", None),
    "regular": ("BeVietnamPro-Regular.ttf", None),
    "light": ("BeVietnamPro-Light.ttf", None),
    "italic": ("BeVietnamPro-MediumItalic.ttf", None),
    "serif_i": ("PlayfairDisplay-Italic-VF.ttf", 600),
    "serif_ib": ("PlayfairDisplay-Italic-VF.ttf", 800),
    "serif": ("PlayfairDisplay-VF.ttf", 600),
    "serif_b": ("PlayfairDisplay-VF.ttf", 800),
}
_tf = {}


def typeface(kind):
    if kind not in _tf:
        name, wght = FONTS[kind]
        t = skia.Typeface.MakeFromFile(os.path.join(FONT_DIR, name))
        if wght is not None:
            tag = (ord("w") << 24) | (ord("g") << 16) | (ord("h") << 8) | ord("t")
            co = skia.FontArguments.VariationPosition.Coordinates(
                [skia.FontArguments.VariationPosition.Coordinate(tag, float(wght))])
            args = skia.FontArguments()
            args.setVariationDesignPosition(skia.FontArguments.VariationPosition(co))
            t = t.makeClone(args)
        _tf[kind] = t
    return _tf[kind]


def font(kind, size):
    f = skia.Font(typeface(kind), float(size))
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setHinting(skia.FontHinting.kNone)
    return f


def nfc(s):
    return unicodedata.normalize("NFC", s)


# ----------------------------------------------------------------------------
# easing
# ----------------------------------------------------------------------------
def clamp01(x):
    return 0.0 if x < 0 else (1.0 if x > 1 else x)


def ease_out_cubic(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def ease_in_cubic(x):
    x = clamp01(x)
    return x ** 3


def ease_in_out_cubic(x):
    x = clamp01(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out_back(x, s=1.70158):
    x = clamp01(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def ease_out_expo(x):
    x = clamp01(x)
    return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)


def ease_in_out_sine(x):
    x = clamp01(x)
    return -(math.cos(math.pi * x) - 1) / 2


def spring(x, damping=7.0, freq=2.2):
    """0->1 with a soft overshoot settle."""
    if x <= 0:
        return 0.0
    return 1 - math.exp(-damping * x) * math.cos(2 * math.pi * freq * x)


def env(t, t0, t1, fade_in=0.18, fade_out=0.18):
    """visibility 0..1 for an element living in [t0, t1]."""
    if t < t0 or t > t1:
        return 0.0
    a = clamp01((t - t0) / fade_in) if fade_in > 0 else 1.0
    b = clamp01((t1 - t) / fade_out) if fade_out > 0 else 1.0
    return min(a, b)


def lerp(a, b, x):
    return a + (b - a) * x


# ----------------------------------------------------------------------------
# skia helpers
# ----------------------------------------------------------------------------
def col(rgb, a=255):
    return skia.Color(int(rgb[0]), int(rgb[1]), int(rgb[2]), int(max(0, min(255, a))))


def fill(rgb, a=255, blur=0.0):
    """Paint for fills. Translucent solid colours go through a 2-stop gradient shader (fast path)."""
    p = skia.Paint(AntiAlias=True)
    c = col(rgb, a)
    if a >= 255:
        p.setColor(c)
    else:
        p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(1, 0)], [c, c]))
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def stroke(rgb, a=255, width=2.0, blur=0.0, cap="round"):
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=float(width))
    p.setColor(col(rgb, a))
    p.setStrokeCap(skia.Paint.kRound_Cap if cap == "round" else skia.Paint.kButt_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


class Layer:
    """Transparent overlay surface: drawn in layout px, stored in device px, tracks what was touched."""

    def __init__(self):
        # skia draws straight into this array: no second buffer and no readback, which matters at 4K
        self.arr = np.zeros((OH, OW, 4), np.uint8)
        self.surf = skia.Surface(self.arr, skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType)
        self.c = self.surf.getCanvas()
        self.c.scale(SS, SS)
        self.dirty = None

    def begin(self):
        # full clear (0.3 ms): a partial clear leaves behind any pixel drawn outside its mark
        self.c.clear(skia.ColorTRANSPARENT)
        self.dirty = None

    def mark(self, x0, y0, x1, y1, pad=40):
        x0, y0 = max(0, int(x0 - pad)), max(0, int(y0 - pad))
        x1, y1 = min(W, int(x1 + pad)), min(H, int(y1 + pad))
        if x1 <= x0 or y1 <= y0:
            return
        if self.dirty is None:
            self.dirty = [x0, y0, x1, y1]
        else:
            d = self.dirty
            self.dirty = [min(d[0], x0), min(d[1], y0), max(d[2], x1), max(d[3], y1)]

    def mark_all(self):
        self.dirty = [0, 0, W, H]

    def pixels(self):
        """(BGRA premul array, device box of what was marked)."""
        if self.dirty is None:
            return None, None
        return self.arr, tuple(v * SS for v in self.dirty)


def text_width(text, fnt, tracking=0.0):
    text = nfc(text)
    if not text:
        return 0.0
    g = fnt.textToGlyphs(text)
    ws = fnt.getWidths(g)
    return float(sum(ws) + tracking * (len(ws) - 1))


def draw_text(layer, text, fnt, x, y, rgb=WHITE, a=255, align="center", tracking=0.0,
              shadow=0.0, shadow_a=150, glow=None, glow_blur=18, glow_a=200, scale=1.0,
              per_char=None, gradient=None, outline=None):
    """Draw a single line. (x, y) = anchor at baseline. per_char(i, n) may return
    (dx, dy, sc, alpha_mult) for glyph animations. Returns (x0, y0, x1, y1)."""
    text = nfc(text)
    if not text or a <= 0:
        return None
    c = layer.c
    g = fnt.textToGlyphs(text)
    ws = fnt.getWidths(g)
    total = sum(ws) + tracking * (len(ws) - 1)
    m = fnt.getMetrics()
    asc, desc = -m.fAscent, m.fDescent
    if align == "center":
        x0 = x - total * scale / 2
    elif align == "right":
        x0 = x - total * scale
    else:
        x0 = x
    c.save()
    c.translate(x0, y)
    c.scale(scale, scale)
    chars = list(text)
    xs = []
    cur = 0.0
    for wv in ws:
        xs.append(cur)
        cur += wv + tracking

    def paint_pass(paint_fn):
        n = len(chars)
        if per_char is None and tracking == 0.0:
            p = paint_fn(1.0)
            if p is not None:
                c.drawString(text, 0, 0, fnt, p)
            return
        for i, ch in enumerate(chars):
            dx, dy, sc, am = (0, 0, 1, 1) if per_char is None else per_char(i, n)
            if am <= 0.003:
                continue
            p = paint_fn(am)
            if p is None:
                continue
            if sc != 1.0:
                c.save()
                cx_ = xs[i] + ws[i] / 2 + dx
                c.translate(cx_, dy - asc * 0.35)
                c.scale(sc, sc)
                c.drawString(ch, -ws[i] / 2, asc * 0.35, fnt, p)
                c.restore()
            else:
                c.drawString(ch, xs[i] + dx, dy, fnt, p)

    if shadow > 0:
        paint_pass(lambda am: fill((0, 0, 0), shadow_a * a / 255 * am, blur=shadow))
    if glow is not None:
        paint_pass(lambda am: fill(glow, glow_a * a / 255 * am, blur=glow_blur))
    if outline is not None:
        orgb, ow = outline
        paint_pass(lambda am: stroke(orgb, a * am, width=ow))
    if gradient is not None:
        top_rgb, bot_rgb = gradient

        def gp(am):
            p = skia.Paint(AntiAlias=True)
            p.setShader(skia.GradientShader.MakeLinear(
                [skia.Point(0, -asc), skia.Point(0, desc * 0.3)],
                [col(top_rgb, a * am), col(bot_rgb, a * am)]))
            return p
        paint_pass(gp)
    else:
        paint_pass(lambda am: fill(rgb, a * am))
    c.restore()
    pad = max(shadow, glow_blur if glow else 0) * 2 + 10
    bx0, bx1 = x0 - pad, x0 + total * scale + pad
    by0, by1 = y - asc * scale - pad, y + desc * scale + pad
    # mark from the real glyph extents: stacked Vietnamese diacritics (Ấ, Ế, Ỗ) rise above the
    # font ascent; extra headroom for per-glyph pop/rise animation
    bnds = fnt.getBounds(g)
    gtop = max(asc, -min(r.top() for r in bnds)) if bnds else asc
    gbot = max(desc, max(r.bottom() for r in bnds)) if bnds else desc
    hr = 0.12 * fnt.getSize() * scale if per_char is not None else 0.0
    layer.mark(bx0 - hr, y - gtop * scale - pad - hr, bx1 + hr, y + gbot * scale + pad + hr, pad=8)
    return (bx0, by0, bx1, by1)


def rrect(x0, y0, x1, y1, r):
    return skia.RRect.MakeRectXY(skia.Rect(x0, y0, x1, y1), r, r)


# ----------------------------------------------------------------------------
# speakers and shots
# ----------------------------------------------------------------------------
# face centre x, face centre y, head-top y (source px); head box keeps depth words off the other person
FACE = {k: (float(v["face"][0]), float(v["face"][1]), float(v["head_top"])) for k, v in CFG["speakers"].items()}
HEADBOX = {k: tuple(float(x) for x in v["box"]) for k, v in CFG["speakers"].items()}

# (zoom, how far the speaker sits off-centre, vertical face position). Deliberately wide: the viewer
# keeps both people in frame on 16:9 and never gets a tight face shot; a 1080p source stays crisp.
_TABLE = {
    "youtube": {"wide": (1.08, 0.16, 0.46), "med": (1.17, 0.12, 0.45), "close": (1.28, 0.08, 0.43)},
    "tiktok": {"wide": (1.00, 0.03, 0.50), "med": (1.07, 0.03, 0.47), "close": (1.15, 0.03, 0.45)},
}
ZKNEE = {"youtube": 1.34, "tiktok": 1.21}[FMT]   # stacked push-ins compress above this zoom
PIP_ZOOM = {"youtube": 1.6, "tiktok": 1.0}[FMT]  # framing inside the PiP card (tiktok: whole wide shot)


def _side(fx):
    return max(-1.0, min(1.0, (fx / SRC_W - 0.5) / 0.18))


SHOTS = {}
for _k, (_fx, _fy, _t) in FACE.items():
    for _n, (_z, _off, _sy) in _TABLE[FMT].items():
        SHOTS[f"{_k}_{_n}"] = dict(spk=_k, z=_z, sx=0.5 + _off * _side(_fx), sy=_sy)
    if FMT == "youtube":
        SHOTS[f"TWO_{_k}"] = dict(spk=_k, z=1.0, cx=SRC_W / 2, cy=SRC_H / 2)
    else:
        SHOTS[f"TWO_{_k}"] = dict(SHOTS[f"{_k}_wide"])


def clamp_cam(cx, cy, z):
    s = z * BASE
    w_src, h_src = W / s, H / s
    cx = min(max(cx, w_src / 2), SRC_W - w_src / 2) if w_src < SRC_W else SRC_W / 2
    cy = min(max(cy, h_src / 2), SRC_H - h_src / 2) if h_src < SRC_H else SRC_H / 2
    return (cx, cy, z)


def shot_cam(name):
    s = SHOTS[name]
    fx, fy, _ = FACE[s["spk"]]
    z = s["z"]
    if "cy" in s:
        return clamp_cam(s["cx"], s["cy"], z)
    k = z * BASE
    return clamp_cam(fx - (s["sx"] - 0.5) * W / k, fy - (s["sy"] - 0.5) * H / k, z)


def card_view(spk, cw, ch):
    """what the PiP card shows: source centre and layout px per source px."""
    fx, fy, _ = FACE[spk]
    s = PIP_ZOOM * max(cw / SRC_W, ch / SRC_H)
    w_src, h_src = cw / s, ch / s
    if FMT == "youtube":
        cx, cy = fx - 0.02 * _side(fx) * w_src, fy + 0.08 * h_src
    else:
        # the whole wide shot; a portrait source cannot fit its height into a landscape card, so follow the face
        cx, cy = SRC_W / 2, (SRC_H / 2 if h_src >= SRC_H * 0.98 else fy + 0.15 * h_src)
    cx = min(max(cx, w_src / 2), SRC_W - w_src / 2) if w_src < SRC_W else SRC_W / 2
    cy = min(max(cy, h_src / 2), SRC_H - h_src / 2) if h_src < SRC_H else SRC_H / 2
    return cx, cy, s


def src_to_screen(cam, x, y):
    """source px -> layout px. cam = (cx, cy, z[, ox, oy]); (ox, oy) is the view centre on screen."""
    s = cam[2] * BASE
    ox, oy = (cam[3], cam[4]) if len(cam) > 3 else (W / 2, H / 2)
    return (ox + (x - cam[0]) * s, oy + (y - cam[1]) * s)


def view_matrix(cam, rect):
    """2x3 source px -> device px of a canvas whose top-left is rect's corner (rect in layout px)."""
    s = cam[2] * BASE * SS
    ox, oy = (cam[3], cam[4]) if len(cam) > 3 else (W / 2, H / 2)
    return np.array([[s, 0, (ox - rect[0]) * SS - s * cam[0]], [0, s, (oy - rect[1]) * SS - s * cam[1]]], np.float64)


# ----------------------------------------------------------------------------
# sources
# ----------------------------------------------------------------------------
_index = None


def master_pos(src_f):
    """position of a source frame inside master.mkv, which holds only the frames the edit uses."""
    global _index
    if _index is None:
        p = os.path.join(PROJECT, "master_index.json")
        _index = json.load(open(p)) if os.path.exists(p) else []
    if not _index:
        return src_f
    i = bisect.bisect_right([r[0] for r in _index], src_f) - 1
    if i < 0:
        return 0
    f0, n, pos = _index[i]
    return pos + min(src_f - f0, n - 1)


class ClipReader:
    """Sequential frame reader for one source range of the master."""

    def __init__(self, src_frame0, nframes):
        self.n = nframes
        self.i = 0
        pos = master_pos(src_frame0)
        # -v fatal: close() kills ffmpeg mid-clip on purpose, which would log a harmless broken pipe
        # -threads 2: compositing is far slower than decoding, and each decoder thread holds whole frames
        cmd = ["ffmpeg", "-v", "fatal", "-threads", "2", "-ss", f"{max(0, pos / FPS - 0.0005):.4f}", "-i", MASTER,
               "-frames:v", str(nframes), "-f", "rawvideo", "-pix_fmt", "bgr24",
               "-sws_flags", "lanczos+accurate_rnd+full_chroma_int", "-"]
        self.p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=SRC_W * SRC_H * 3 * 2)
        self.last = None

    def next(self):
        if self.i < self.n:
            buf = self.p.stdout.read(SRC_W * SRC_H * 3)
            if len(buf) == SRC_W * SRC_H * 3:
                self.last = np.frombuffer(buf, np.uint8).reshape(SRC_H, SRC_W, 3)
        self.i += 1
        return self.last

    def close(self):
        try:
            self.p.stdout.close()
            self.p.kill()
        except Exception:
            pass


_matte_cache = {}


def load_matte(src_frame):
    if src_frame in _matte_cache:
        return _matte_cache[src_frame]
    p = os.path.join(MATTE_DIR, f"{src_frame:06d}.png")
    m = imread(p, cv2.IMREAD_GRAYSCALE) if os.path.exists(p) else None
    if len(_matte_cache) > 64:
        _matte_cache.clear()
    _matte_cache[src_frame] = m
    return m


def matte_to_view(m_small, M, size):
    """warp a stored matte (crop at 1/MSCALE) through the view matrix -> uint8 of `size` (w, h)."""
    A = np.array([[MSCALE, 0, MCX], [0, MSCALE, MCY], [0, 0, 1]], np.float64)
    M3 = np.vstack([M, [0, 0, 1]]) @ A
    return cv2.warpAffine(m_small, M3[:2], size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


# ----------------------------------------------------------------------------
# compositing (all arrays same size, uint8)
# ----------------------------------------------------------------------------
def over_premul(out, ov):
    """premultiplied BGRA `ov` over BGR `out`, in place."""
    a = ov[..., 3]
    if cv2.countNonZero(a) == 0:
        return
    inv = cv2.bitwise_not(a)
    r = cv2.multiply(out, cv2.merge([inv, inv, inv]), scale=1 / 255.0)
    out[:] = cv2.add(r, np.ascontiguousarray(ov[..., :3]))


def behind_premul(out, ov, matte):
    """composite ov behind the person: ov is attenuated by (1 - matte)."""
    o = np.ascontiguousarray(ov)
    if cv2.countNonZero(o[..., 3]) == 0:
        return
    k = cv2.bitwise_not(np.ascontiguousarray(matte))
    o = cv2.multiply(o, cv2.merge([k, k, k, k]), scale=1 / 255.0)
    inv = cv2.bitwise_not(o[..., 3])
    r = cv2.multiply(out, cv2.merge([inv, inv, inv]), scale=1 / 255.0)
    out[:] = cv2.add(r, np.ascontiguousarray(o[..., :3]))


_corner_cache = OrderedDict()


def corner_alpha(r):
    """alpha of the top-left corner of a rounded rect (ceil(r) x ceil(r) float32)."""
    key = round(r, 1)
    if key not in _corner_cache:
        ri = int(math.ceil(key))
        yy, xx = np.mgrid[0:ri, 0:ri].astype(np.float32)
        dx, dy = key - (xx + 0.5), key - (yy + 0.5)
        _corner_cache[key] = np.where((dx > 0) & (dy > 0), np.clip(key - np.hypot(dx, dy) + 0.5, 0, 1), 1.0).astype(np.float32)
        if len(_corner_cache) > 64:
            _corner_cache.popitem(last=False)
    return _corner_cache[key]


def round_mask(w, h, r):
    m = np.ones((h, w), np.float32)
    r = min(r, w / 2, h / 2)
    if r >= 0.5:
        a = corner_alpha(r)
        ri = a.shape[0]
        m[:ri, :ri] = a
        m[:ri, w - ri:] = a[:, ::-1]
        m[h - ri:, :ri] = a[::-1, :]
        m[h - ri:, w - ri:] = a[::-1, ::-1]
    return m


def glass(out, x0, y0, x1, y1, r=34, sigma=16, tint=(18, 22, 20), tint_a=0.34, alpha=1.0, bright=1.0):
    """Frosted-glass panel over `out` (coordinates in layout px)."""
    x0, y0, x1, y1, r, sigma = int(x0 * SS), int(y0 * SS), int(x1 * SS), int(y1 * SS), r * SS, sigma * SS
    if alpha <= 0.01 or x1 - x0 < 4 or y1 - y0 < 4:
        return
    pad = int(sigma * 3)
    X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(OW, x1 + pad), min(OH, y1 + pad)
    roi = out[Y0:Y1, X0:X1]
    small = cv2.resize(roi, ((X1 - X0) // 2, (Y1 - Y0) // 2), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), sigma / 2)
    bl = cv2.resize(small, (X1 - X0, Y1 - Y0), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    bl = bl * (1 - tint_a) * bright + np.array(tint[::-1], np.float32) * tint_a
    cx0, cy0 = max(x0, 0), max(y0, 0)
    cx1, cy1 = min(x1, OW), min(y1, OH)
    m = round_mask(x1 - x0, y1 - y0, r)[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0][..., None] * alpha
    sub_bl = bl[cy0 - Y0:cy1 - Y0, cx0 - X0:cx1 - X0]
    tgt = out[cy0:cy1, cx0:cx1].astype(np.float32)
    out[cy0:cy1, cx0:cx1] = np.clip(sub_bl * m + tgt * (1 - m), 0, 255).astype(np.uint8)


_SMOKE = np.clip((np.arange(256, dtype=np.float32) / 255.0) ** 1.5 * 255.0 + 0.5, 0, 255).astype(np.uint8)


def glass_from(src, out, x0, y0, x1, y1, r, alpha):
    """Frosted card showing the (already blurred) stage background at full brightness."""
    x0, y0, x1, y1, r = int(x0 * SS), int(y0 * SS), int(x1 * SS), int(y1 * SS), r * SS
    if alpha <= 0.01 or x1 - x0 < 4 or y1 - y0 < 4:
        return
    cx0, cy0, cx1, cy1 = max(x0, 0), max(y0, 0), min(x1, OW), min(y1, OH)
    m = round_mask(x1 - x0, y1 - y0, r)[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0][..., None] * alpha
    # smoked glass: a bright sky behind the panel is pulled down harder than the dark trees, so coloured text stays
    # readable wherever the panel happens to sit
    bl = cv2.LUT(src[cy0:cy1, cx0:cx1], _SMOKE).astype(np.float32) * 0.62 + np.array((20, 22, 18), np.float32) * 0.38
    tgt = out[cy0:cy1, cx0:cx1].astype(np.float32)
    out[cy0:cy1, cx0:cx1] = np.clip(bl * m + tgt * (1 - m), 0, 255).astype(np.uint8)


# ----------------------------------------------------------------------------
# sharpening
# ----------------------------------------------------------------------------
DETAIL = float(os.environ.get("EDIT_DETAIL", "1.0"))
_K3 = np.ones((3, 3), np.uint8)
_scratch = {}


def _buf(name, shape):
    """reused float buffers: fresh 33 MB allocations every frame cost page faults, badly so when RAM is short."""
    b = _scratch.get(name)
    if b is None or b.shape != shape:
        b = _scratch[name] = np.empty(shape, np.float32)
    return b


def detail(img, s, iters=3):
    """Luma-only Richardson-Lucy deconvolution matched to the upscale factor `s` (device px per source
    px). Undoes the softness the zoom adds; coring leaves codec noise alone and a local min/max clamp
    stops the halos that make ordinary sharpening look digital."""
    if DETAIL <= 0 or s < 0.9:
        return img
    ycc = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    shape = ycc.shape[:2]
    y, est, conv, tmp = _buf("y", shape), _buf("est", shape), _buf("conv", shape), _buf("tmp", shape)
    np.copyto(y, ycc[..., 0], casting="unsafe")
    y *= 1 / 255.0
    psf = max(0.7, 0.55 * s)
    est[:] = y
    for _ in range(iters):
        cv2.GaussianBlur(est, (0, 0), psf, dst=conv)
        conv += 1e-3
        cv2.divide(y, conv, dst=tmp)
        cv2.GaussianBlur(tmp, (0, 0), psf, dst=tmp)
        cv2.multiply(est, tmp, dst=est)
    cv2.subtract(est, y, dst=est)                     # est now holds the detail signal
    np.clip(est, -0.004, 0.004, out=tmp)              # coring: small differences are codec noise
    est -= tmp
    if DETAIL != 1.0:
        est *= DETAIL
    est += y
    cv2.erode(y, _K3, dst=conv)
    conv -= 0.03
    cv2.dilate(y, _K3, dst=tmp)
    tmp += 0.03
    cv2.max(est, conv, dst=est)                       # local min/max clamp: no halos
    cv2.min(est, tmp, dst=est)
    est *= 255.0
    ycc[..., 0] = cv2.convertScaleAbs(est)
    return cv2.cvtColor(ycc, cv2.COLOR_YCrCb2BGR)


# ----------------------------------------------------------------------------
# film finish
# ----------------------------------------------------------------------------
class Finish:
    """Halation (warm glow bleeding from highlights into dark edges), vignette, luminance-weighted grain."""

    def __init__(self, vignette=0.20, grain=1.3, halation=0.7, seed=3):
        self.hal = halation
        yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
        nx, ny = (xx - OW / 2) / (OW / 2), (yy - OH * 0.46) / (OH / 2)
        v = 1 - vignette * np.clip((np.sqrt(nx ** 2 * 0.9 + ny ** 2) - 0.55) / 0.9, 0, 1) ** 1.6
        self.vig = np.clip(v * 255, 0, 255).astype(np.uint8)[..., None].repeat(3, axis=2)
        self.pos = self.neg = None
        if grain > 0:
            # one noise field, read at a different offset each frame: looks random, costs one frame of memory
            rng = np.random.default_rng(seed)
            self.pad = 96 * SS
            sigma = 0.55 * SS   # fine 35 mm-like grain; stays fine after the 4K -> 1080p player downscale
            g = rng.standard_normal((OH + self.pad, OW + self.pad)).astype(np.float32)
            g = cv2.GaussianBlur(g, (0, 0), sigma)
            g = g / g.std() * grain
            self.pos = np.clip(g, 0, 255).astype(np.uint8)
            self.neg = np.clip(-g, 0, 255).astype(np.uint8)
        # grain response: strongest in the mids, fades in deep shadow and bright highlights
        lum = np.arange(256, dtype=np.float32) / 255.0
        self.lut = np.clip((0.25 + 3.0 * lum * (1 - lum)) * 255, 0, 255).astype(np.uint8)

    def __call__(self, img, f):
        if self.hal > 0:
            small = cv2.resize(img, (OW // 8, OH // 8), interpolation=cv2.INTER_AREA)
            red = np.ascontiguousarray(small[..., 2])
            hl = cv2.GaussianBlur(cv2.subtract(red, np.full_like(red, 205)), (0, 0), 2.4)
            hl = cv2.resize(hl, (OW, OH), interpolation=cv2.INTER_LINEAR)
            hl = cv2.multiply(hl, np.full_like(hl, 255), scale=self.hal * 1.6 / 255.0)
            glow = cv2.merge([cv2.multiply(hl, np.full_like(hl, 8), scale=1 / 255.0),
                              cv2.multiply(hl, np.full_like(hl, 70), scale=1 / 255.0), hl])
            # screen: bright areas take almost no extra light, dark edges next to them do
            img = cv2.add(img, cv2.multiply(glow, cv2.bitwise_not(img), scale=1 / 255.0))
        img = cv2.multiply(img, self.vig, scale=1 / 255.0)
        if self.pos is not None:
            small = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (OW // 8, OH // 8), interpolation=cv2.INTER_AREA)
            m = cv2.resize(cv2.LUT(small, self.lut), (OW, OH), interpolation=cv2.INTER_LINEAR)
            dx, dy = (f * 7919) % self.pad, (f * 104729) % self.pad
            p = cv2.multiply(self.pos[dy:dy + OH, dx:dx + OW], m, scale=1 / 255.0)
            q = cv2.multiply(self.neg[dy:dy + OH, dx:dx + OW], m, scale=1 / 255.0)
            img = cv2.add(cv2.subtract(img, cv2.merge([q, q, q])), cv2.merge([p, p, p]))
        return img
