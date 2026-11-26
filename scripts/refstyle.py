"""Caption helpers after the user's TikTok reference @__dviet ("4 cách cắt video", seen 2026-11-16). rawstyle.py builds the
motion style's captions on its word handling (disp, split_rows, active_line, WEAK); the look described here was the
first reference:

- kinetic captions beside the speaker instead of a caption bar: the spoken line in small white lowercase words on a
  gentle arc, its key phrase (story.KEYS) big in neon green with a glow, each word appearing as it is spoken;
- full-screen scenes on a dark green gradient: a huge blurred word behind, small sharp words in front, thin glowing
  curves, glowing UI frames, sparks.

Our footage is a bright field, not a dark room, so every word carries a soft dark halo for legibility instead of the
picture being darkened (the user rejected darkening).
"""
import math
import random

import skia

import story as S
from engine import clamp01, ease_out_back, ease_out_cubic, font, nfc

W, H = 1080, 1920
NEON = (110, 255, 170)
NEON_GLOW = (40, 255, 130)
WHITE = (255, 255, 255)
PROPER = {"anthropic": "Anthropic", "claude": "Claude", "codex": "Codex", "copilot": "Copilot",
          "skill.md": "SKILL.md", "gpt": "GPT", "chatgpt": "ChatGPT", "github": "GitHub", "telegram": "Telegram",
          "zalo": "Zalo", "iphone": "iPhone", "android": "Android", "pc": "PC", "server": "server", "mobile": "mobile",
          "code": "Code", "codex": "Codex"}


def _c4(rgb, a):
    return skia.Color4f(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, max(0.0, min(1.0, a / 255)))


def disp(word):
    """lowercase like the reference, proper names kept, trailing punctuation dropped except a question mark. An acronym
    the transcript wrote in capitals stays (AI, GPT, MCP); the pronoun "ai" (who, anyone) is lowercase there and stays
    lowercase."""
    w = nfc(word).strip()
    q = w.endswith("?")
    core = w.strip(".,;:!?…\"“”")
    key = S._norm(core)
    if len(core) >= 2 and core.isupper():
        out = core
    else:
        out = PROPER.get(core.lower(), PROPER.get(key, core.lower()))
    return out + ("?" if q else "")


def glow_text(c, text, f, x, y, rgb, a, glow_rgb=None, glow_a=0.0, glow_sigma=14, halo=0.6, align="center",
              rot=0.0):
    """one word at baseline (x, y): dark halo, coloured glow, then the face. Returns its width."""
    text = nfc(text)
    w = f.measureText(text)
    x0 = x - w / 2 if align == "center" else x
    c.save()
    if rot:
        c.translate(x, y)
        c.rotate(rot)
        c.translate(-x, -y)
    if halo > 0:
        hp = skia.Paint(AntiAlias=True, Color=_c4((0, 8, 6), a * halo))
        hp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, f.getSize() * 0.18))
        c.drawString(text, x0, y + f.getSize() * 0.03, f, hp)
    if glow_rgb is not None and glow_a > 0:
        gp = skia.Paint(AntiAlias=True, Color=_c4(glow_rgb, glow_a))
        gp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, glow_sigma))
        c.drawString(text, x0, y, f, gp)
    p = skia.Paint(AntiAlias=True, Color=_c4(rgb, a))
    c.drawString(text, x0, y, f, p)
    c.restore()
    return w


# ----------------------------------------------------------------------------
# kinetic captions
# ----------------------------------------------------------------------------
def active_line(t):
    for ln in S.LINES:
        if ln[0]["line_start"] <= t <= ln[0]["line_end"]:
            return ln
    return None


WEAK = set()    # key words that win a line only when it has no other key phrase (an episode's own topic word)


def split_rows(ln):
    """(before, key, after): the LAST run of key-styled words is the key phrase. In these lines the point tends to
    come last ("cái agent skill này chỉ là MỘT KỸ NĂNG", "khái niệm được ANTHROPIC"); earlier key words stay small.
    A run made only of WEAK words loses to an earlier run with a stronger word ("tự động nạp cái skill đó")."""
    runs, i = [], 0
    while i < len(ln):
        if ln[i]["style"]:
            j = i
            while j + 1 < len(ln) and ln[j + 1]["style"]:
                j += 1
            runs.append((i, j))
            i = j + 1
        else:
            i += 1
    if not runs:
        return ln, [], []
    strong = [r for r in runs if any(S._norm(x["disp"]) not in WEAK for x in ln[r[0]:r[1] + 1])]
    i0, i1 = (strong or runs)[-1]
    return ln[:i0], ln[i0:i1 + 1], ln[i1 + 1:]


def _word_k(t, x):
    return clamp01((t - (x["s"] - 0.05)) / 0.14)


def kinetic(L, t, cx, y_top, max_w=900, small=50, big=118, arc_r=1300.0, line=None, after_y=None):
    """draws the active caption line around (cx, y_top): small words on an arc at y_top, the key phrase big below it,
    the words after it small under the key. Returns the bottom y used, or None when no line is active."""
    ln = line or active_line(t)
    if not ln:
        return None
    end_v = 1.0 if ln[0]["line_cut"] else clamp01((ln[0]["line_end"] - t) / 0.12)
    if end_v <= 0:
        return None
    before, key, after = split_rows(ln)
    c = L.c
    fs = font("semi", small)
    rows_bottom = y_top

    def arc_row(words, y, f, rgb, glow=None):
        if not words:
            return y
        txts = [disp(x["disp"]) for x in words]
        sp = f.getSize() * 0.28
        widths = [f.measureText(nfc(s)) for s in txts]
        total = sum(widths) + sp * (len(words) - 1)
        sc = min(1.0, max_w / total) if total > 0 else 1.0
        ff = font("semi", f.getSize() * sc) if sc < 1 else f
        widths = [ff.measureText(nfc(s)) for s in txts]
        total = sum(widths) + sp * sc * (len(words) - 1)
        pos = cx - total / 2
        for x, s, w in zip(words, txts, widths):
            k = _word_k(t, x)
            mid = pos + w / 2
            pos += w + sp * sc
            if k <= 0:
                continue
            ang = (mid - cx) / arc_r                      # radians along the arc
            px = cx + arc_r * math.sin(ang)
            py = y + arc_r * (1 - math.cos(ang)) + (1 - ease_out_cubic(k)) * 16
            glow_text(c, s, ff, px, py, rgb, 255 * k * end_v, glow_rgb=glow or (255, 255, 255),
                      glow_a=70 * k * end_v, glow_sigma=10, rot=math.degrees(ang))
        return y + ff.getSize() * 0.35

    y = y_top
    if before:
        y = arc_row(before, y, fs, WHITE)
    if key:
        txt = " ".join(disp(x["disp"]) for x in key)
        k0 = _word_k(t, key[0])
        if k0 > 0:
            fb = font("black", big)
            w = fb.measureText(nfc(txt))
            if w > max_w:
                fb = font("black", big * max_w / w)
            yk = y + fb.getSize() * 0.92
            pop = 1.0 + 0.3 * (1 - ease_out_back(min(1.0, k0)))
            pulse = math.exp(-max(0.0, t - key[0]["s"]) / 0.5)
            c.save()
            c.translate(cx, yk - fb.getSize() * 0.35)
            c.scale(pop, pop)
            c.translate(-cx, -(yk - fb.getSize() * 0.35))
            glow_text(c, txt, fb, cx, yk, NEON, 255 * k0 * end_v, glow_rgb=NEON_GLOW,
                      glow_a=(150 + 105 * pulse) * k0 * end_v, glow_sigma=fb.getSize() * 0.16, halo=0.55)
            c.restore()
            y = yk + fb.getSize() * 0.12
    if after:
        y = arc_row(after, (after_y if after_y is not None else y + small * 0.95), font("semi", small * 0.9), WHITE)
    rows_bottom = y
    L.mark(0, y_top - 160, W, rows_bottom + 120, pad=0)
    return rows_bottom


# ----------------------------------------------------------------------------
# scenes
# ----------------------------------------------------------------------------
def scene_bg(L, t, t0, t1, top=0, bottom=H, seed=1, enter=0.14, exit_=0.1):
    """dark green gradient, drifting glowing curves and sparks; returns its alpha 0..1 (0 = not shown)."""
    if t < t0 or t > t1:
        return 0.0
    v = clamp01((t - t0) / enter) * clamp01((t1 - t) / exit_)
    c = L.c
    a = 255 * v
    sh = skia.GradientShader.MakeRadial(skia.Point(W * 0.5, (top + bottom) * 0.46), H * 0.62,
                                        [_c4((22, 84, 62), a), _c4((8, 34, 27), a), _c4((2, 10, 8), a)],
                                        [0.0, 0.55, 1.0])
    p = skia.Paint(AntiAlias=True)
    p.setShader(sh)
    c.drawRect(skia.Rect.MakeLTRB(0, top, W, bottom), p)
    rnd = random.Random(seed)
    u = t - t0
    for i in range(3):                                  # thin glowing curves drifting across
        y0 = top + (bottom - top) * rnd.uniform(0.25, 0.8)
        amp = rnd.uniform(120, 260)
        ph = rnd.uniform(0, 6.28) + u * rnd.uniform(0.3, 0.7)
        path = skia.Path()
        path.moveTo(-60, y0 + amp * math.sin(ph))
        path.cubicTo(W * 0.3, y0 - amp, W * 0.7, y0 + amp * math.cos(ph), W + 60, y0 - amp * 0.5 * math.sin(ph))
        sp = skia.Paint(AntiAlias=True, Color=_c4(NEON, a * 0.22))
        sp.setStyle(skia.Paint.kStroke_Style)
        sp.setStrokeWidth(2.0)
        sp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 1.5))
        c.drawPath(path, sp)
    for i in range(36):                                 # sparks
        px, py = rnd.uniform(0, W), rnd.uniform(top, bottom)
        r = rnd.uniform(1.0, 3.0)
        py = top + ((py - top) - u * rnd.uniform(10, 40)) % (bottom - top)
        tw = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(rnd.uniform(0, 6.28) + t * 3.0))
        dp = skia.Paint(AntiAlias=True, Color=_c4((170, 255, 210), a * 0.6 * tw))
        dp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r))
        c.drawCircle(px, py, r, dp)
    L.mark(0, top, W, bottom, pad=0)
    return v


def depth_word(L, text, x, y, size, a, blur=26, rgb=(70, 150, 112), kind="black"):
    """a huge out-of-focus word behind the scene."""
    f = font(kind, size)
    p = skia.Paint(AntiAlias=True, Color=_c4(rgb, a * 0.45))
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    tw = f.measureText(nfc(text))
    L.c.drawString(nfc(text), x - tw / 2, y, f, p)
    L.mark(x - tw / 2 - 60, y - size, x + tw / 2 + 60, y + size * 0.3)


def small_word(L, text, x, y, size, a, rgb=WHITE, align="center", kind="semi"):
    return glow_text(L.c, text, font(kind, size), x, y, rgb, a, glow_rgb=(255, 255, 255), glow_a=60 * a / 255,
                     glow_sigma=10, halo=0.0, align=align)


def neon_word(L, text, x, y, size, a, align="center", pop_k=1.0, kind="black"):
    f = font(kind, size * pop_k)
    return glow_text(L.c, text, f, x, y, NEON, a, glow_rgb=NEON_GLOW, glow_a=230 * a / 255, glow_sigma=size * 0.16,
                     halo=0.0, align=align)


def ui_frame(L, x0, y0, x1, y1, a, r=34, fill_a=0.55):
    """a glowing rounded frame, like the reference's video-player and timeline windows."""
    c = L.c
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, y0, x1, y1), r, r),
                skia.Paint(AntiAlias=True, Color=_c4((6, 22, 18), a * fill_a)))
    gp = skia.Paint(AntiAlias=True, Color=_c4(NEON_GLOW, a * 0.55))
    gp.setStyle(skia.Paint.kStroke_Style)
    gp.setStrokeWidth(8)
    gp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 9))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, y0, x1, y1), r, r), gp)
    sp = skia.Paint(AntiAlias=True, Color=_c4((190, 255, 220), a * 0.9))
    sp.setStyle(skia.Paint.kStroke_Style)
    sp.setStrokeWidth(2.4)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, y0, x1, y1), r, r), sp)
    L.mark(x0 - 30, y0 - 30, x1 + 30, y1 + 30)
