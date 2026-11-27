"""On-screen "computer" pieces, made for the Playwright episode and used by the motion and vlog styles: a ghost cursor
that moves, clicks and types on its own (the episode's motif: the AI is driving), a browser window, form fields and
buttons, a code panel (the x-ray of a button), chat bubbles, a script card. All in layout px on a given layer; plain shapes, no brand
artwork (the word "Zalo" appears as text only).
"""
import skia

from engine import c4, clamp01, ease_out_back, ease_out_cubic, font, nfc, system_font
from engine import rrect as rr  # noqa: F401  (the same rounded rectangle; designs call UI.rr)

INK = (18, 22, 32)
PAPER = (250, 251, 253)
BAR = (233, 237, 243)
LINE = (214, 220, 230)
MUTE = (118, 126, 140)
BLUE = (48, 110, 255)
GREEN = (36, 196, 118)
REDC = (255, 95, 86)
CODE_BG = (16, 20, 30)
RIPPLE = (120, 235, 215)     # the cursor's click ripple; a design may set its own (the motion example: rawstyle.AQUA)


def ease_io(x):
    x = clamp01(x)
    return 3 * x * x - 2 * x * x * x


def mono(size, bold=False):
    """Consolas from the system fonts (code and URLs: ASCII only); falls back to the UI font"""
    return system_font("consolab.ttf" if bold else "consola.ttf", size, "bold" if bold else "medium")


def text(c, s, f, x, y, rgb, a, align="left"):
    s = nfc(s)
    w = f.measureText(s)
    x0 = x - w / 2 if align == "center" else (x - w if align == "right" else x)
    c.drawString(s, x0, y, f, skia.Paint(AntiAlias=True, Color=c4(rgb, a)))
    return w


def typed(s, k):
    """the first part of s for a typing progress k (0..1)"""
    return s[:int(round(len(s) * clamp01(k)))]


def caret(c, x, y, h, t, a, rgb=BLUE):
    if int(t * 2.6) % 2 == 0:
        c.drawRect(skia.Rect.MakeXYWH(x + 3, y - h * 0.82, 4, h), skia.Paint(Color=c4(rgb, a)))


# ----------------------------------------------------------------------------
# the ghost cursor
# ----------------------------------------------------------------------------
ARROW = [(0, 0), (0, 17), (4.2, 13.2), (7.2, 20), (9.8, 18.9), (6.9, 12.2), (12.2, 12.2)]


class Cursor:
    """keys = [(t, x, y)]: the tip is at (x, y) at time t; it rests, then glides to the next key over `move` s on a
    slightly curved path. clicks = [t]: a press and a ripple at the tip."""

    def __init__(self, keys, clicks=(), move=0.4, scale=4.0, t_in=None, t_out=None, ripple=None):
        self.keys = sorted(keys)
        self.clicks = sorted(clicks)
        self.move = move
        self.scale = scale
        self.t_in = self.keys[0][0] if t_in is None else t_in
        self.t_out = self.keys[-1][0] + 0.6 if t_out is None else t_out
        self.ripple = ripple if ripple is not None else RIPPLE

    def pos(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return ks[0][1], ks[0][2]
        for (t0, x0, y0), (t1, x1, y1) in zip(ks, ks[1:]):
            if t < t1:
                d = max(0.05, min(self.move, t1 - t0))
                u = ease_io((t - (t1 - d)) / d)
                mx, my = (x0 + x1) / 2 - (y1 - y0) * 0.14, (y0 + y1) / 2 + (x1 - x0) * 0.14
                return ((1 - u) ** 2 * x0 + 2 * u * (1 - u) * mx + u * u * x1,
                        (1 - u) ** 2 * y0 + 2 * u * (1 - u) * my + u * u * y1)
        return ks[-1][1], ks[-1][2]

    def draw(self, L, t, a=255.0):
        v = clamp01((t - self.t_in) / 0.12) * clamp01((self.t_out - t) / 0.15)
        if v <= 0:
            return
        a *= v
        x, y = self.pos(t)
        c = L.c
        press = 0.0
        for tc in self.clicks:
            u = t - tc
            if 0 <= u < 0.5:
                k = ease_out_cubic(u / 0.5)
                p = skia.Paint(AntiAlias=True, Color=c4(self.ripple, a * (1 - u / 0.5) ** 1.4))
                p.setStyle(skia.Paint.kStroke_Style)
                p.setStrokeWidth(max(2.0, 10 * (1 - k)))
                c.drawCircle(x, y, 14 + 96 * k, p)
                c.drawCircle(x, y, 6 + 40 * k, skia.Paint(AntiAlias=True, Color=c4(self.ripple, a * 0.25 * (1 - u / 0.5))))
            if -0.05 <= u < 0.11:
                press = 1.0
        s = self.scale * (1 - 0.14 * press)
        path = skia.Path()
        for i, (px, py) in enumerate(ARROW):
            if i == 0:
                path.moveTo(x + px * s, y + py * s)
            else:
                path.lineTo(x + px * s, y + py * s)
        path.close()
        sh = skia.Paint(AntiAlias=True, Color=c4((0, 0, 0), a * 0.42))
        sh.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6))
        c.save()
        c.translate(5, 8)
        c.drawPath(path, sh)
        c.restore()
        wp = skia.Paint(AntiAlias=True, Color=c4((255, 255, 255), a))
        wp.setStyle(skia.Paint.kStroke_Style)
        wp.setStrokeWidth(s * 1.9)
        wp.setStrokeJoin(skia.Paint.kRound_Join)
        c.drawPath(path, wp)
        c.drawPath(path, skia.Paint(AntiAlias=True, Color=c4((10, 12, 18), a)))
        L.mark(x - 130, y - 130, x + 150, y + 170)


# ----------------------------------------------------------------------------
# windows, fields, buttons
# ----------------------------------------------------------------------------
def pop_transform(c, cx, cy, k):
    """scale a window in from 0.72 with a little overshoot (call inside save/restore)"""
    s = 0.72 + 0.28 * ease_out_back(clamp01(k))
    c.translate(cx, cy)
    c.scale(s, s)
    c.translate(-cx, -cy)


def window(L, rect, a, url=None, url_k=1.0, t=0.0, typing=False, r=30, bar=80, tab=None):
    """a light browser window; returns its page rect. url_k = how much of the URL is typed"""
    x0, y0, x1, y1 = rect
    c = L.c
    sh = skia.Paint(AntiAlias=True, Color=c4((0, 0, 0), a * 0.38))
    sh.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 26))
    c.drawRRect(rr(x0 + 4, y0 + 22, x1 - 4, y1 + 22, r), sh)
    c.drawRRect(rr(x0, y0, x1, y1, r), skia.Paint(AntiAlias=True, Color=c4(PAPER, a)))
    c.save()
    c.clipRRect(rr(x0, y0, x1, y1, r), skia.ClipOp.kIntersect, True)
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y0 + bar), skia.Paint(Color=c4(BAR, a)))
    c.restore()
    for i, col in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        c.drawCircle(x0 + 38 + i * 30, y0 + bar / 2, 10, skia.Paint(AntiAlias=True, Color=c4(col, a)))
    ux0, ux1 = x0 + 136, x1 - 30
    c.drawRRect(rr(ux0, y0 + 17, ux1, y0 + bar - 17, 23), skia.Paint(AntiAlias=True, Color=c4((255, 255, 255), a)))
    if url:
        f = mono(29)
        s = typed(url, url_k)
        w = text(c, s, f, ux0 + 22, y0 + bar / 2 + 10, INK, a)
        if typing and url_k < 1:
            caret(c, ux0 + 22 + w, y0 + bar / 2 + 10, 30, t, a)
    if tab:
        text(c, tab, font("semi", 24), x1 - 44, y0 + bar / 2 + 8, MUTE, a, align="right")
    L.mark(x0 - 40, y0 - 30, x1 + 40, y1 + 70)
    return (x0, y0 + bar, x1, y1)


def field(L, x, y, w, h, label, value, k, a, t=0.0, focus=False, password=False, size=34):
    """a labelled input; value typed up to k"""
    c = L.c
    if label:
        text(c, label, font("semi", 25), x + 4, y - 14, MUTE, a)
    c.drawRRect(rr(x, y, x + w, y + h, 16), skia.Paint(AntiAlias=True, Color=c4((255, 255, 255), a)))
    bp = skia.Paint(AntiAlias=True, Color=c4(BLUE if focus else LINE, a))
    bp.setStyle(skia.Paint.kStroke_Style)
    bp.setStrokeWidth(4 if focus else 3)
    c.drawRRect(rr(x, y, x + w, y + h, 16), bp)
    s = typed(value, k)
    f = font("semi", size)
    if password:                                # dots drawn as circles (the font may lack the bullet)
        tw = 0.0
        for i in range(len(s)):
            c.drawCircle(x + 22 + size * 0.2 + i * size * 0.52, y + h / 2, size * 0.17, skia.Paint(AntiAlias=True, Color=c4(INK, a)))
            tw = (i + 1) * size * 0.52
    else:
        tw = text(c, s, f, x + 22, y + h / 2 + size * 0.36, INK, a)
    if focus:
        caret(c, x + 22 + tw, y + h / 2 + size * 0.36, size, t, a)
    L.mark(x - 10, y - 50, x + w + 10, y + h + 10)


def button(L, x, y, w, h, label, a, press=0.0, rgb=BLUE, done=0.0, size=34):
    """a filled button; press 0..1 squeezes it, done 0..1 turns it green with a tick"""
    c = L.c
    col = tuple(int(rgb[i] + (GREEN[i] - rgb[i]) * clamp01(done)) for i in range(3))
    c.save()
    s = 1 - 0.05 * press
    c.translate(x + w / 2, y + h / 2)
    c.scale(s, s)
    c.translate(-(x + w / 2), -(y + h / 2))
    sh = skia.Paint(AntiAlias=True, Color=c4(col, a * 0.35 * (1 - press)))
    sh.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12))
    c.drawRRect(rr(x + 6, y + 12, x + w - 6, y + h + 10, h / 2), sh)
    c.drawRRect(rr(x, y, x + w, y + h, 18), skia.Paint(AntiAlias=True, Color=c4(col, a)))
    f = font("bold", size)
    text(c, label, f, x + w / 2, y + h / 2 + size * 0.36, (255, 255, 255), a, align="center")
    c.restore()
    L.mark(x - 20, y - 20, x + w + 20, y + h + 30)


def tick(L, x, y, r, a, k=1.0, rgb=GREEN):
    """a round badge with a tick that draws itself (k 0..1)"""
    if k <= 0:
        return
    c = L.c
    s = 0.6 + 0.4 * ease_out_back(clamp01(k * 1.6))
    c.drawCircle(x, y, r * s, skia.Paint(AntiAlias=True, Color=c4(rgb, a)))
    p = skia.Paint(AntiAlias=True, Color=c4((255, 255, 255), a))
    p.setStyle(skia.Paint.kStroke_Style)
    p.setStrokeWidth(r * 0.24)
    p.setStrokeCap(skia.Paint.kRound_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    kk = clamp01((k - 0.25) / 0.75)
    pts = [(-0.42, 0.02), (-0.12, 0.32), (0.44, -0.3)]
    path = skia.Path()
    path.moveTo(x + pts[0][0] * r, y + pts[0][1] * r)
    if kk <= 0.4:
        u = kk / 0.4
        path.lineTo(x + (pts[0][0] + (pts[1][0] - pts[0][0]) * u) * r, y + (pts[0][1] + (pts[1][1] - pts[0][1]) * u) * r)
    else:
        u = (kk - 0.4) / 0.6
        path.lineTo(x + pts[1][0] * r, y + pts[1][1] * r)
        path.lineTo(x + (pts[1][0] + (pts[2][0] - pts[1][0]) * u) * r, y + (pts[1][1] + (pts[2][1] - pts[1][1]) * u) * r)
    c.drawPath(path, p)
    L.mark(x - r - 8, y - r - 8, x + r + 8, y + r + 8)


def cross(L, x, y, r, a, k=1.0, rgb=REDC, width=None):
    """a red X that draws itself"""
    if k <= 0:
        return
    c = L.c
    p = skia.Paint(AntiAlias=True, Color=c4(rgb, a))
    p.setStyle(skia.Paint.kStroke_Style)
    p.setStrokeWidth(width or r * 0.3)
    p.setStrokeCap(skia.Paint.kRound_Cap)
    k1, k2 = clamp01(k * 2), clamp01(k * 2 - 1)
    c.drawLine(x - r, y - r, x - r + 2 * r * k1, y - r + 2 * r * k1, p)
    if k2 > 0:
        c.drawLine(x + r, y - r, x + r - 2 * r * k2, y - r + 2 * r * k2, p)
    L.mark(x - r - 20, y - r - 20, x + r + 20, y + r + 20)


# ----------------------------------------------------------------------------
# code, chat, cards
# ----------------------------------------------------------------------------
def code_panel(L, rect, a, lines, size=34, k=1.0, title=None):
    """a dark panel of code; lines = [[(text, rgb), ...]], typed up to k over all characters"""
    x0, y0, x1, y1 = rect
    c = L.c
    sh = skia.Paint(AntiAlias=True, Color=c4((0, 0, 0), a * 0.4))
    sh.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 22))
    c.drawRRect(rr(x0 + 4, y0 + 18, x1 - 4, y1 + 18, 26), sh)
    c.drawRRect(rr(x0, y0, x1, y1, 26), skia.Paint(AntiAlias=True, Color=c4(CODE_BG, a)))
    y = y0 + 56
    if title:
        text(c, title, font("semi", 24), x0 + 30, y0 + 40, (130, 140, 160), a)
        y = y0 + 92
    total = sum(len(s) for ln in lines for s, _ in ln)
    budget = int(round(total * clamp01(k)))
    f = mono(size)
    for ln in lines:
        x = x0 + 30
        for s, rgb in ln:
            take = max(0, min(len(s), budget))
            budget -= take
            if take > 0:
                x += text(c, s[:take], f, x, y, rgb, a)
        y += size * 1.42
    L.mark(x0 - 30, y0 - 20, x1 + 30, y1 + 60)


def bubble(L, x, y, w, s, a, mine=True, size=32, k=1.0, max_chars=None):
    """a chat bubble with its top-left (or top-right when mine) corner at (x, y); returns its height"""
    c = L.c
    f = font("medium", size)
    s = nfc(s)
    tw = min(w - 44, f.measureText(s))
    bw, bh = tw + 44, size * 1.9
    x0 = x - bw if mine else x
    col = BLUE if mine else (236, 239, 244)
    c.save()
    sc = 0.7 + 0.3 * ease_out_back(clamp01(k))
    c.translate(x, y + bh / 2)
    c.scale(sc, sc)
    c.translate(-x, -(y + bh / 2))
    c.drawRRect(rr(x0, y, x0 + bw, y + bh, 26), skia.Paint(AntiAlias=True, Color=c4(col, a * clamp01(k * 2))))
    text(c, s, f, x0 + 22, y + bh / 2 + size * 0.36, (255, 255, 255) if mine else INK, a * clamp01(k * 2))
    c.restore()
    L.mark(x0 - 20, y - 10, x0 + bw + 20, y + bh + 10)
    return bh


def card(L, rect, a, r=30, rgb=PAPER, shadow=0.36):
    x0, y0, x1, y1 = rect
    c = L.c
    sh = skia.Paint(AntiAlias=True, Color=c4((0, 0, 0), a * shadow))
    sh.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 24))
    c.drawRRect(rr(x0 + 4, y0 + 20, x1 - 4, y1 + 20, r), sh)
    c.drawRRect(rr(x0, y0, x1, y1, r), skia.Paint(AntiAlias=True, Color=c4(rgb, a)))
    L.mark(x0 - 40, y0 - 30, x1 + 40, y1 + 70)


def pill(L, cx, y, s, a, size=34, rgb=(12, 16, 24), fg=(255, 255, 255), k=1.0, icon=None):
    """a small dark pill with text, centred at cx (baseline y); pops in with k"""
    if k <= 0:
        return
    c = L.c
    f = font("bold", size)
    w = f.measureText(nfc(s))
    c.save()
    sc = 0.7 + 0.3 * ease_out_back(clamp01(k))
    c.translate(cx, y - size * 0.3)
    c.scale(sc, sc)
    c.translate(-cx, -(y - size * 0.3))
    c.drawRRect(rr(cx - w / 2 - 26, y - size * 1.05, cx + w / 2 + 26, y + size * 0.5, size * 0.78),
                skia.Paint(AntiAlias=True, Color=c4(rgb, a * 0.88 * clamp01(k * 2))))
    text(c, s, f, cx, y, fg, a * clamp01(k * 2), align="center")
    c.restore()
    L.mark(cx - w / 2 - 50, y - size * 1.4, cx + w / 2 + 50, y + size * 0.8)
