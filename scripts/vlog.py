"""The vlog style's design kit (references/vlog.md): a calm, chaptered YouTube edit cut on the music's beat.

A vlog design starts with `from vlog import *`, which also brings everything `from story import *` gives, then calls
setup() once. beat_fit.py has already put every cut on the beat grid (beats.json); this module gives the design the
same clock, so graphics, reframes and transitions land on beats too:

- gb(n), q(t), qb(t), bar(ch, n, beat), on(clip, word): times on the grid. on() is a word's time moved to the nearest
  half beat (at most 0.18 s away at 82 BPM): use it for everything that should hit with the music.
- setup(titles, ...): the style's fixed behaviour: shots that alternate wide / medium every two bars (cuts on bar
  lines), chapter cards on the B-roll before each chapter, a chapter tag in each chapter's first seconds, captions
  off over B-roll, a small push on every chapter's downbeat, light leaks at the cards, soft automatic cues, clean
  cuts into and out of B-roll, the YouTube chapter list, and the B-roll drawn over speech (overlays in beats.json).
- drawing pieces in the warm palette: plate, mini (a titled plate for the top band), paper (a page of the travel
  journal), chip_row, side_chip, step_row, arrow_h, strike_line, code_lines, shade, rule, underline, tilt, scaled.
- ARRANGE: the music's sections per chapter, for vlog_music.py; QUIET: extra windows where vlog_mix.py mutes the
  clip's own sound.

For mock software pieces (a browser window, fields, buttons, a cursor that clicks, chat bubbles) use ui.py.
"""
import json
import math
import os

import cv2
import numpy as np
import skia

import engine as E
import story as S_
import ui as U
from story import *  # noqa: F401,F403  (the design gets the story kit through this module)
from engine import (AMBER, CORAL, FPS, H, INK, MINT, OH, OW, SKY, W, WHITE, clamp01, col, draw_text, ease_in_out_sine,
                    ease_out_back, ease_out_cubic, env, fill, font, lerp, nfc, rrect, spring, stroke, text_width)
from gfx import big_text, chip, icon

BT = json.load(open(os.path.join(E.PROJECT, "beats.json")))
BEAT = BT["beat"] / FPS
BAR = 4 * BEAT
DOWN = {c["n"]: c["down"] / FPS for c in BT["chapters"]}       # chapter number -> its downbeat (s)
CARD = {c["beat"]: c["cut"] / FPS for c in BT["cards"]}        # card clip name -> its cut-in (s)
CARD_OF = {c["chapter"]: c["cut"] / FPS for c in BT["cards"] if c.get("chapter")}   # chapter number -> its card (s)
CUT = {c["beat"]: c["cut"] / FPS for c in BT["cuts"]}          # clip name -> its cut (s)
BROLL = [(b["cut"] / FPS, (b["cut"] + b["frames"]) / FPS, b["beat"]) for b in BT.get("broll", [])]
OVERLAYS = [dict(o, t0=o["at"] / FPS, t1=(o["at"] + o["frames"]) / FPS) for o in BT.get("overlays", [])]
_last = BT.get("broll", [])[-1:] if BT.get("broll") else []
T_END = _last[0]["cut"] / FPS if _last and _last[0]["cut"] + _last[0]["frames"] == BT["total"] else BT["total"] / FPS
CREAM = (255, 244, 224)
PAPER = (252, 244, 228)
INKB = (38, 32, 26)                                            # warm ink for text on paper
ARRANGE = {}     # chapter -> [(first bar from 1, style, progression)], read by vlog_music.py (defaults there)
QUIET = []       # extra (t0, t1) where vlog_mix.py mutes the clip's sound (B-roll, holds and the end are automatic)

S_.PIP_T = BEAT / 2            # the speaker shrinks / grows back in half a beat, so both ends of a PiP sit on the grid


# ----------------------------------------------------------------------------
# the grid
# ----------------------------------------------------------------------------
def gb(n):
    """global beat number -> seconds"""
    return n * BEAT


def q(t, div=2):
    """the point of the beat grid nearest to t (div 1: beats, 2: half beats, 4: quarter beats)"""
    step = BEAT / div
    return round(t / step) * step


def qb(t):
    return q(t, 1)


def bar(ch, n, beat=1.0):
    """time of bar n (from 1), beat (from 1.0) of chapter ch"""
    return DOWN[ch] + ((n - 1) * 4 + (beat - 1.0)) * BEAT


def bar_lines(ch, t_end):
    """the downbeats of chapter ch up to t_end"""
    out, t = [], DOWN[ch]
    while t < t_end - 1e-6:
        out.append(t)
        t += BAR
    return out


def w(beat, word, n=1):
    """output time of the n-th `word` in the clip `beat` (as spoken)"""
    return word_in(beat, word, n)


def on(beat, word, n=1, div=2):
    """the same, moved to the nearest half beat (div=1: beat): graphics hit with the music"""
    return q(word_in(beat, word, n), div)


def pulse(t, t0, dur=0.42, amt=1.0):
    """1 -> 0 after a beat at t0: for things that kick with the music"""
    if t0 is None:
        return 0.0
    u = (t - t0) / dur
    return amt * (1 - ease_out_cubic(u)) if 0 <= u < 1 else 0.0


# ----------------------------------------------------------------------------
# B-roll over a speaking clip (overlays in beats.json; build_master.py put their frames in the master)
# ----------------------------------------------------------------------------
_rd = {"rd": None, "next": None}


def master_frame(src_f):
    """one graded frame of master.mkv by source frame number; sequential calls keep one decoder open"""
    if _rd["rd"] is None or _rd["next"] != src_f:
        if _rd["rd"] is not None:
            _rd["rd"].close()
        _rd["rd"] = E.ClipReader(src_f, 600)
    fr = _rd["rd"].next()
    _rd["next"] = src_f + 1
    return fr


def broll_over(ctx, t, t0, t1, src_t0, zoom=(1.0, 1.04), focus=(0.5, 0.5)):
    """source frames from src_t0 on cover the picture from t0 to t1 (the clip's sound plays on), with a slow push-in.
    Drawn on ctx.mid: under the film finish, the titles and the captions. Returns True while it shows. Keep depth
    words off it: the matte belongs to the clip underneath."""
    if not (t0 - 1e-6 <= t < t1 - 1e-6):
        return False
    fr = master_frame(int(round(src_t0 * FPS)) + int(round((t - t0) * FPS)))
    if fr is None:
        return False
    u = (t - t0) / max(1e-6, t1 - t0)
    z = lerp(zoom[0], zoom[1], ease_in_out_sine(u)) * max(OW / E.SRC_W, OH / E.SRC_H)
    cx, cy = focus[0] * E.SRC_W, focus[1] * E.SRC_H
    cx = min(max(cx, OW / z / 2), E.SRC_W - OW / z / 2)
    cy = min(max(cy, OH / z / 2), E.SRC_H - OH / z / 2)
    M = np.array([[z, 0, OW / 2 - z * cx], [0, z, OH / 2 - z * cy]], np.float64)
    img = cv2.warpAffine(fr, M, (OW, OH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    arr = ctx.mid.arr
    arr[..., :3] = img
    arr[..., 3] = 255
    ctx.mid.mark_all()
    return True


def overlay_at(t):
    """the overlay showing at t (a dict with t0, t1, src), else None"""
    for o in OVERLAYS:
        if o["t0"] - 1e-6 <= t < o["t1"] - 1e-6:
            return o
    return None


def _draw_overlays(ctx, t):
    o = overlay_at(t)
    if o is not None:
        broll_over(ctx, t, o["t0"], o["t1"], o["src"], zoom=tuple(o.get("zoom", (1.0, 1.04))),
                   focus=tuple(o.get("focus", (0.5, 0.5))))


# ----------------------------------------------------------------------------
# drawing helpers
# ----------------------------------------------------------------------------
class scaled:
    """with scaled(L, x, y, s): draw in a local frame whose origin is (x, y) and whose unit is s layout px"""

    def __init__(self, L, x, y, s):
        self.L, self.args = L, (x, y, s)

    def __enter__(self):
        x, y, s = self.args
        self.L.c.save()
        self.L.c.translate(x, y)
        self.L.c.scale(s, s)
        return self.L.c

    def __exit__(self, *exc):
        self.L.c.restore()


class tilt:
    """with tilt(L, cx, cy, deg, scale): draw rotated (and scaled) about (cx, cy)"""

    def __init__(self, L, cx, cy, deg=0.0, scale=1.0):
        self.c, self.args = L.c, (cx, cy, deg, scale)

    def __enter__(self):
        cx, cy, deg, sc = self.args
        self.c.save()
        self.c.translate(cx, cy)
        self.c.rotate(deg)
        self.c.scale(sc, sc)
        self.c.translate(-cx, -cy)
        return self.c

    def __exit__(self, *exc):
        self.c.restore()


def k_in(t, t0, dur=0.3):
    return clamp01((t - t0) / dur)


def pop(t, t0, dur=0.38):
    """0..1 with a soft overshoot, starting at t0"""
    return spring(clamp01((t - t0) / dur), 6.5, 1.6) if t >= t0 else 0.0


def fade(t, t0, t1, fin=0.14, fout=0.2):
    return env(t, t0, t1, fin, fout)


def shade(L, y0, y1, a_top, a_bot, rgb=(10, 12, 10)):
    """a soft vertical gradient band (legibility for type over the sky and the trees)"""
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)], [col(rgb, a_top), col(rgb, a_bot)]))
    L.c.drawRect(skia.Rect.MakeLTRB(0, y0, W, y1), p)
    L.mark(0, y0, W, y1, pad=0)


def rule(L, x0, x1, y, k, rgb=AMBER, a=255, width=3.0):
    """a thin rule that draws itself from its centre"""
    if k <= 0:
        return
    cx = (x0 + x1) / 2
    hw = (x1 - x0) / 2 * ease_out_cubic(k)
    L.c.drawLine(cx - hw, y, cx + hw, y, stroke(rgb, a, width=width))
    L.mark(x0, y - 6, x1, y + 6, pad=10)


def underline(L, x0, x1, y, k, rgb=AMBER, a=255, width=7.0):
    """a marker underline drawn left to right with a small wave"""
    if k <= 0:
        return
    path = skia.Path()
    n = 24
    xe = lerp(x0, x1, ease_out_cubic(k))
    for i in range(n + 1):
        x = lerp(x0, xe, i / n)
        yy = y + 3.0 * math.sin((x - x0) / 46.0)
        if i == 0:
            path.moveTo(x, yy)
        else:
            path.lineTo(x, yy)
    L.c.drawPath(path, stroke(rgb, a * 0.35, width=width + 8, blur=7))
    L.c.drawPath(path, stroke(rgb, a, width=width))
    L.mark(x0 - 10, y - 16, x1 + 10, y + 16, pad=14)


def label(L, text, x, y, size=34, rgb=WHITE, a=255, kind="semi", align="left", shadow=8, tracking=0.0):
    return draw_text(L, text, font(kind, size), x, y, rgb=rgb, a=a, align=align, shadow=shadow, shadow_a=170,
                     tracking=tracking)


def plate(L, x0, y0, x1, y1, a, r=26, accent=None, glow=0.0, dark=168):
    """a dark glass-like plate with a hairline (cheap: no blur of the picture)"""
    c = L.c
    c.drawRRect(rrect(x0, y0 + 10, x1, y1 + 10, r), fill((0, 0, 0), 70 * a, blur=18))
    c.drawRRect(rrect(x0, y0, x1, y1, r), fill(INK, dark * a))
    c.drawRRect(rrect(x0, y0, x1, y1, r), stroke(WHITE, 52 * a, width=1.6))
    if accent is not None and glow > 0:
        c.drawRRect(rrect(x0, y0, x1, y1, r), stroke(accent, 200 * a * glow, width=5, blur=9))
        c.drawRRect(rrect(x0, y0, x1, y1, r), stroke(accent, 255 * a * glow, width=2.4))
    L.mark(x0, y0, x1, y1 + 14, pad=30)


def paper(L, x0, y0, x1, y1, a, rot=0.0, r=10, tape=True):
    """a cream paper card (a page of the travel journal) with a strip of tape. Draw it and its content inside one
    `with tilt(L, cx, cy, deg, scale)` so both turn together."""
    c = L.c
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    c.save()
    c.rotate(rot, cx, cy)
    c.drawRRect(rrect(x0 + 4, y0 + 16, x1 - 4, y1 + 18, r), fill((0, 0, 0), 95 * a, blur=22))
    c.drawRRect(rrect(x0, y0, x1, y1, r), fill(PAPER, 250 * a))
    if tape:
        tw, th = 150, 38
        c.drawRect(skia.Rect.MakeLTRB(cx - tw / 2, y0 - th * 0.45, cx + tw / 2, y0 + th * 0.55), fill(AMBER, 150 * a))
    c.restore()
    L.mark(x0, y0 - 30, x1, y1 + 24, pad=40)


def mini(L, cx, cy, w, h, t, t0, t1, title, sub=None, icon_kind=None, accent=AMBER, glow=0.0, dim=0.0, num=None):
    """a titled plate for the top band: a number or an icon, a title, one line under it. Pops in at t0. Two side by
    side at cx 680 / 1250 (or three at 372 / 960 / 1548), cy 212, about 540 x 156: they stay above both heads."""
    v = fade(t, t0, t1)
    if v <= 0:
        return None
    k = 0.6 + 0.4 * pop(t, t0)
    a = v * (1 - 0.55 * dim)
    with tilt(L, cx, cy, 0.0, k):
        x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        plate(L, x0, y0, x1, y1, a, accent=accent, glow=glow)
        tx = x0 + 34
        if num is not None:
            draw_text(L, num, font("black", 72), tx, cy + 25, rgb=accent, a=255 * a, align="left")
            tx += text_width(num, font("black", 72)) + 26
        elif icon_kind:
            icon(L.c, icon_kind, tx + 36, cy, 72, accent, 255 * a, sw=5)
            tx += 72 + 28
        if sub:
            draw_text(L, title, font("bold", 44), tx, cy - 8, rgb=WHITE, a=255 * a, align="left")
            draw_text(L, sub, font("medium", 30), tx, cy + 38, rgb=(222, 222, 212), a=240 * a, align="left")
        else:
            draw_text(L, title, font("bold", 44), tx, cy + 15, rgb=WHITE, a=255 * a, align="left")
    L.mark(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2 + 14, pad=40)
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def chip_row(L, t, items, y, t1, size=44, gap=30, cx=None):
    """chips side by side, the row centred on cx: items = [(text, icon, t0, accent)], each popping at its own t0"""
    ws = []
    for (txt, ic, _t0, _acc) in items:
        ws.append(text_width(txt, font("semi", size)) + (size * 1.05 + size * 0.4 if ic else 0) + size * 1.5)
    total = sum(ws) + gap * (len(ws) - 1)
    x = (cx if cx is not None else W / 2) - total / 2
    for (txt, ic, t0, acc), w_ in zip(items, ws):
        chip(L, t, t0, t1, x, y, txt, ic, style="glow", size=size, accent=acc, anchor="left")
        x += w_ + gap


def side_chip(ctx, t, t0, t1, spk, row, text, icon_kind=None, accent=AMBER, size=38):
    """a chip beside a speaker at shoulder height: at the frame's right edge for the person on the right, at its left
    edge for the person on the left, so a long line never runs off the frame or onto the other person. Keep it to
    three or four words."""
    y = anc(ctx, 0, 0, spk)[1] + 34 + row * 96
    if E.FACE[spk][0] >= E.SRC_W / 2:
        return chip(ctx.front, t, t0, t1, W - MX, y, text, icon_kind, style="glow", size=size, accent=accent, anchor="right")
    return chip(ctx.front, t, t0, t1, MX, y, text, icon_kind, style="glow", size=size, accent=accent, anchor="left")


def step_row(L, x, y, num, text, t, t0, a, accent=AMBER, done_t=None, size=40, hot_t=None):
    """one line of a list of steps: a numbered dot and its text; pops at t0; a tick replaces the number from done_t;
    the dot flashes at hot_t (a replay)."""
    if t < t0:
        return
    k = pop(t, t0)
    aa = a * clamp01((t - t0) / 0.1)
    r = 27 * (0.6 + 0.4 * k)
    hot = pulse(t, hot_t, 0.3) if hot_t is not None else 0.0
    c = L.c
    if hot > 0:
        c.drawCircle(x, y, r + 16 * hot, fill(accent, 120 * hot * a / 255, blur=10))
    if done_t is not None and t >= done_t:
        U.tick(L, x, y, r, aa, k=clamp01((t - done_t) / 0.3), rgb=(36, 196, 118))
    else:
        c.drawCircle(x, y, r, fill(accent, aa))
        draw_text(L, str(num), font("black", 32), x, y + 11, rgb=INK, a=aa, align="center")
    draw_text(L, text, font("semi", size), x + 50 + (1 - ease_out_cubic(k_in(t, t0, 0.35))) * 18, y + size * 0.34, rgb=WHITE,
              a=aa, align="left")
    L.mark(x - 50, y - 44, x + 60 + text_width(text, font("semi", size)), y + 44, pad=10)


def step_slot(L, x, y, num, v, wide=0):
    """the empty place of a step still to come, so the eye knows how many there are"""
    c = L.c
    c.drawCircle(x, y, 24, stroke(WHITE, 80 * v, width=2.5))
    draw_text(L, str(num), font("bold", 26), x, y + 9, rgb=WHITE, a=90 * v, align="center")
    c.drawRRect(rrect(x + 50, y - 10, x + 250 + 40 * wide, y + 10, 10), fill(WHITE, 28 * v))
    L.mark(x - 30, y - 30, x + 300, y + 30)


def arrow_h(L, x0, x1, y, k, rgb=AMBER, a=255, width=5.0, head=16):
    """a horizontal arrow that draws itself"""
    if k <= 0:
        return
    xe = lerp(x0, x1, ease_out_cubic(k))
    c = L.c
    c.drawLine(x0, y, xe, y, stroke(rgb, a, width=width))
    if k >= 0.98:
        d = 1 if x1 >= x0 else -1
        c.drawLine(x1, y, x1 - d * head, y - head * 0.75, stroke(rgb, a, width=width))
        c.drawLine(x1, y, x1 - d * head, y + head * 0.75, stroke(rgb, a, width=width))
    L.mark(min(x0, x1) - 10, y - 24, max(x0, x1) + 10, y + 24, pad=10)


def strike_line(L, x0, x1, y, k, rgb=CORAL, a=255, width=8.0):
    if k <= 0:
        return
    xe = lerp(x0, x1, ease_out_cubic(k))
    L.c.drawLine(x0, y, xe, y, stroke(rgb, a, width=width))
    L.mark(x0 - 10, y - 14, x1 + 10, y + 14, pad=10)


C_TAG, C_ATTR, C_STR, C_TXT, C_DIM = (130, 200, 255), (255, 196, 98), (150, 235, 190), (236, 238, 242), (120, 132, 150)


def code_lines(L, x, y, lines, a, size=30, k=1.0, lh=1.5, hot=None, hot_a=0.0, hot_rgb=AMBER, width=None):
    """monospace code, typed up to k over all characters; line `hot` gets a soft highlight bar.
    lines = [[(text, rgb), ...], ...]; C_TAG, C_ATTR, C_STR, C_TXT, C_DIM are the code colours."""
    f = U.mono(size)
    total = sum(len(s) for ln in lines for s, _ in ln)
    budget = int(round(total * clamp01(k)))
    c = L.c
    yy = y
    for i, ln in enumerate(lines):
        if hot is not None and i == hot and hot_a > 0:
            ww = width or (sum(f.measureText(s) for s, _ in ln) + 24)
            c.drawRRect(rrect(x - 12, yy - size * 0.95, x - 12 + ww, yy + size * 0.42, 8), fill(hot_rgb, 70 * hot_a * a / 255))
            c.drawRRect(rrect(x - 12, yy - size * 0.95, x - 12 + ww, yy + size * 0.42, 8),
                        stroke(hot_rgb, 230 * hot_a * a / 255, width=2.4))
        xx = x
        for s, rgb in ln:
            take = max(0, min(len(s), budget))
            budget -= take
            if take > 0:
                xx += U.text(c, s[:take], f, xx, yy, rgb, a)
        yy += size * lh
    L.mark(x - 20, y - size * 1.2, x + (width or 700), yy, pad=10)


_ipa = {}


def ipa_font(size):
    """Times New Roman from the system fonts, for phonetic symbols (the skill's fonts have none)"""
    key = round(size, 1)
    if key not in _ipa:
        p = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "times.ttf")
        tf = skia.Typeface.MakeFromFile(p) if os.path.exists(p) else None
        if tf is None:
            _ipa[key] = font("medium", size)
        else:
            f = skia.Font(tf, float(size))
            f.setSubpixel(True)
            f.setEdging(skia.Font.Edging.kAntiAlias)
            _ipa[key] = f
    return _ipa[key]


# ----------------------------------------------------------------------------
# chapter card and chapter tag
# ----------------------------------------------------------------------------
def chapter_card(ctx, t, tc, num, title, total="07"):
    """two beats of B-roll: beat 1 the number and a rule, beat 2 the title in serif italic. The chapter starts on the
    downbeat after it."""
    t1 = tc + 2 * BEAT
    if not (tc - 1e-6 <= t < t1 - 1e-6):
        return
    shade(ctx.mid, 0, 600, 150, 0)
    shade(ctx.mid, 700, H, 0, 110)
    L = ctx.front
    k1 = ease_out_cubic(clamp01((t - tc) / 0.30))
    draw_text(L, f"{num} / {total}", font("bold", 40), W / 2, 196 + (1 - k1) * 12, rgb=AMBER, a=255 * k1, align="center",
              tracking=8.0, shadow=10, shadow_a=170)
    rule(L, W / 2 - 150, W / 2 + 150, 226, clamp01((t - tc) / 0.45), rgb=AMBER, a=230, width=3)
    big_text(L, t, tc + BEAT - 0.04, t1, title, W / 2, 372, size=128, kind="serif_ib", rgb=CREAM, max_w=1560,
             tracking=0.0, enter="rise", stagger=0.016, shadow=16, fade_out=0.001)


def chapter_tag(ctx, t, t0, num, title, hold=3.3):
    """a small tag at the top left for the chapter's first seconds (the standard chapter rail's job)"""
    v = fade(t, t0, t0 + hold, 0.2, 0.35)
    if v <= 0:
        return
    L = ctx.ui
    k = ease_out_cubic(clamp01((t - t0) / 0.45))
    x0, y0 = 96 - (1 - k) * 30, 74
    fn, ft = font("black", 36), font("serif_i", 40)
    wn, wt = text_width(num, fn), text_width(title, ft)
    w_, h = 30 + wn + 22 + wt + 34, 70
    L.c.drawRRect(rrect(x0, y0, x0 + w_, y0 + h, h / 2), fill(INK, 160 * v))
    L.c.drawRRect(rrect(x0, y0, x0 + w_, y0 + h, h / 2), stroke(WHITE, 46 * v, width=1.5))
    draw_text(L, num, fn, x0 + 30, y0 + h / 2 + 13, rgb=AMBER, a=255 * v, align="left")
    draw_text(L, title, ft, x0 + 30 + wn + 22, y0 + h / 2 + 13, rgb=CREAM, a=255 * v, align="left")
    L.mark(x0, y0, x0 + w_, y0 + h, pad=20)


# ----------------------------------------------------------------------------
# setup: the style's fixed behaviour
# ----------------------------------------------------------------------------
def _chapter_of(t):
    ns = [n for n in DOWN if DOWN[n] <= t + 1e-6]
    return max(ns) if ns else None


def setup(titles, yt_chapters=None, tag_hold=2.4, tag_holds=None, no_tags=(), pip_view=None, reframe_bars=2,
          punch=0.022):
    """call once, at the top of design.py.

    titles: {chapter: "lowercase title"} for the cards and tags. yt_chapters: {chapter: "Title for the description"}
    (default: the titles, capitalised); chapter 1 starts at 0:00, the others at their cards. tag_hold / tag_holds
    ({chapter: s}): how long the top-left tag stays (shorten it where a card of the design takes the top band);
    no_tags: chapters without a tag. pip_view: {speaker: (card width in source px, x offset)} when two people sit
    close: the picture-in-picture card then shows that speaker alone, head to knees. reframe_bars: wide and medium
    alternate every this many bars. punch: the push on each chapter's downbeat (0 for none)."""
    total = f"{len(DOWN):02d}"
    broll = set(b for (_a, _b, b) in BROLL)
    # shots: wide / medium alternate every `reframe_bars` bars from each chapter's downbeat; B-roll is the two-shot
    for c in CLIPS:
        if c["beat"] in broll:
            SHOT_OVERRIDES.append((c["out_in"], c["out_out"], f"TWO_{c['spk']}"))
            continue
        ch = _chapter_of(c["out_in"])
        t0_ = DOWN[ch] if ch is not None else 0.0
        t = c["out_in"]
        while t < c["out_out"] - 1e-6:
            b = int((t - t0_) / BAR + 1e-6)
            nxt = min(c["out_out"], t0_ + (b + 1) * BAR)
            size = "wide" if (b // reframe_bars) % 2 == 0 else "med"
            SHOT_OVERRIDES.append((t, nxt, f"{c['spk']}_{size}"))
            t = nxt
    SHOT_OVERRIDES.append((DUR, TOTAL, f"TWO_{CLIPS[-1]['spk']}"))
    # no caption lingers over B-roll: the cards and the ending belong to the music
    quiet = [(a, b) for (a, b, _n) in BROLL]
    CAPTION_OFF.append(lambda t: any(a - 1e-6 <= t < b for a, b in quiet))
    for n in sorted(DOWN):
        if n != min(DOWN) and punch:
            PUNCHES.append((DOWN[n], punch, 0.08, 0.15, 0.9))
    for tc in sorted(CARD.values()):
        LEAKS.append(tc - 0.04)
    for o in OVERLAYS:
        LEAKS.append(o["t1"] - 0.04)
    names = yt_chapters or {n: s[:1].upper() + s[1:] for n, s in titles.items()}
    for n in sorted(names):
        YT_CHAPTERS.append((0.0 if n == min(DOWN) else CARD_OF.get(n, DOWN.get(n, 0.0)), names[n]))
    if pip_view:
        def _card_view(spk, cw, ch_):
            fx, fy, _ = E.FACE[spk]
            w_src, dx = pip_view.get(spk, (800.0, 0.0))
            s = cw / w_src
            h_src = ch_ / s
            cx = fx + dx
            cy = fy + 0.10 * h_src
            cx = min(max(cx, w_src / 2), E.SRC_W - w_src / 2)
            cy = min(max(cy, h_src / 2), E.SRC_H - h_src / 2)
            return cx, cy, s
        E.card_view = _card_view

    def _soft_auto_cues():
        """the skill's automatic cues at a vlog's level; clean cuts into and out of B-roll"""
        for (a, b) in PIP:
            cue(a + S_.PIP_T * 0.6, "whoosh", 0.26, length=0.5, direction=1)
            cue(b + S_.PIP_T * 0.6, "whoosh", 0.22, length=0.5, direction=-1)
        for i in range(1, len(CLIPS)):
            if CLIPS[i]["spk"] != CLIPS[i - 1]["spk"] and CLIPS[i]["beat"] not in broll and CLIPS[i - 1]["beat"] not in broll:
                cue(CLIPS[i]["out_in"] + 0.03, "whoosh", 0.3, length=0.42, direction=1)
        # the engine whips the camera at a speaker change and lets a caption linger over a cut; an empty split at a
        # cut time switches both off there (render.near_split, story.build_lines). It has to run here, after story
        # has cleared SPLIT for 16:9.
        for (a, b) in quiet:
            S_.SPLIT.append((a, a, None, None))
            S_.SPLIT.append((b, b, None, None))

    S_._auto_cues = _soft_auto_cues
    if OVERLAYS:
        PRE.append(_draw_overlays)
    # the cards and the tags
    for n in sorted(CARD_OF):
        tc = CARD_OF[n]
        if n in titles:
            ev(tc - 0.02, tc + 2 * BEAT + 0.02)(
                lambda ctx, t, tc=tc, n=n: chapter_card(ctx, t, tc, f"{n:02d}", titles[n], total))
    holds = dict(tag_holds or {})
    for n in sorted(DOWN):
        if n in no_tags or n not in titles:
            continue
        t0 = DOWN[n]
        o = overlay_at(t0)
        if o is not None:
            t0 = o["t1"]
        t0 += 0.05
        hold = holds.get(n, tag_hold)
        ev(t0 - 0.05, t0 + hold + 0.05)(lambda ctx, t, t0=t0, n=n, hold=hold: chapter_tag(ctx, t, t0, f"{n:02d}", titles[n], hold))
