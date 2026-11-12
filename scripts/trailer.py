"""Movie-trailer kit for a project's design.py. Read references/trailer.md first; examples/ai-agent-trailer/
is the current reference, examples/vibe-code-trailer/ an earlier one that still darkens the room.

    from story import *
    from trailer import *

- Thin cinema bars slide in on the first frame and close like curtains into black title cards: @card(t0, t1) with
  card_text() lines. Put cards on the silences that select.json "gap_after" leaves (story.gap(beat)), or over a
  line for a voice-over-black beat. Captions hide while a card covers the frame.
- flash(t): a white flash frame on a hard cut of the escalation. A few only, never more than three a second.
- pill_text(): tracked caps on a dark pill, for a title or a note over a bright sky. This is how text stays
  legible without touching the picture.
- top_fade() and dim_room(t0, t1): darken the sky or the room. Only when the user asks for a moodier picture: on
  phone footage the darkening reads as haze ("mờ và nhòe"), and the user judges the colour against the original.
- prompt_box() and title_slam(): a typed prompt and a title slam, for a twist and the title on black.
The colour stays as the user chose it: the film feel comes from the bars, the cards and the rhythm, not a grade.
The sound is registered with story.score(); trailer_score.py synthesises it and audio_mix.py mixes it.
"""
import skia

import story as _S
from engine import AMBER, INK, MINT, WHITE, H, W, clamp01, draw_text, ease_in_cubic, ease_out_cubic, ease_out_expo, \
    env, fill, font, lerp, nfc, rrect, stroke, text_width

__all__ = ["BAR", "CARDS", "FLASHES", "card", "curtain", "card_text", "flash", "pill_text", "top_fade", "dim_room",
           "wrap_text", "prompt_box", "title_slam"]

YT = _S.YT
BAR = 132 if YT else 104     # 16:9: a letterbox; 9:16: mostly under the platform UI, felt when the curtains move
K = 0.8 if YT else 1.0       # card sizes and offsets are written in 9:16 px
CARDS = []                   # (t0, t1, fn, close, open)
FLASHES = []


def card(t0, t1, close=0.16, open_=0.24):
    """black title card from t0 to t1: the bars close over `close` s before t0 and open over `open_` s after t1
    (0 = hard cut). fn(ctx, t, t0, t1) draws its text on ctx.ui, usually with card_text()."""
    def deco(fn):
        CARDS.append((t0, t1, fn, close, open_))
        return fn
    return deco


def curtain(t):
    """0 = thin cinema bars, 1 = closed (full black)."""
    k = 0.0
    for (t0, t1, _fn, cl, op) in CARDS:
        if cl > 0 and t0 - cl <= t < t0:
            k = max(k, ease_in_cubic((t - (t0 - cl)) / cl))
        elif t0 <= t <= t1:
            k = 1.0
        elif op > 0 and t1 < t <= t1 + op:
            k = max(k, 1 - ease_out_cubic((t - t1) / op))
    return k


def card_text(L, t, t0, t1, text, dy, kind="semi", size=80, rgb=WHITE, track=0.18, delay=0.0, gradient=None,
              glow=None, push=0.05):
    """one centred line of a title card, its baseline dy px below the frame centre. It fades in from slightly
    large `delay` s after t0, then drifts closer by `push` until t1. Caps with track 0.2-0.34 for statements,
    serif_ib without tracking for the emotional word."""
    a0 = t0 + delay
    if t < a0:
        return None
    v = env(t, a0, t1, 0.12, 0.08)
    k = ease_out_cubic(clamp01((t - a0) / 0.45))
    sc = (1.07 - 0.07 * k) * (1.0 + push * clamp01((t - a0) / max(0.4, t1 - a0)))
    size *= K
    return draw_text(L, text, font(kind, size), W / 2, H / 2 + dy * K, rgb=rgb, a=255 * v, tracking=track * size,
                     scale=sc, gradient=gradient, glow=glow, glow_a=110, glow_blur=26)


def flash(t):
    FLASHES.append(t)


def pill_text(L, t, t0, t1, text, x, y, size=30, rgb=WHITE, track=0.2):
    """tracked caps centred on x, baseline y, on a dark pill that fades with them: legible over a bright sky
    without darkening the picture. Draw it on ctx.front, or on ctx.behind to keep it behind the people."""
    v = env(t, t0, t1, 0.25, 0.2)
    if v <= 0:
        return
    f = font("bold", size)
    tw = text_width(text, f, track * size)
    L.c.drawRRect(rrect(x - tw / 2 - 26, y - size * 1.15, x + tw / 2 + 26, y + size * 0.55, size), fill(INK, 175 * v))
    draw_text(L, text, f, x, y, rgb=rgb, a=255 * v, tracking=track * size)
    L.mark(x - tw / 2 - 30, y - size * 1.3, x + tw / 2 + 30, y + size * 0.7)


def top_fade(t0=0.0, t1=None, strength=0.62):
    """dark fade from the top bar down to about a third of the frame, behind the people. Opt-in: see the top."""
    depth = 330 if YT else 600
    t1 = _S.DUR if t1 is None else t1
    shader = []

    def fn(ctx, t):
        if not (t0 <= t <= t1):
            return
        if not shader:
            shader.append(skia.GradientShader.MakeLinear([skia.Point(0, BAR), skia.Point(0, depth)],
                                                         [skia.Color4f(0, 0, 0, strength), skia.Color4f(0, 0, 0, 0)]))
        p = skia.Paint(AntiAlias=True)
        p.setShader(shader[0])
        ctx.behind.c.drawRect(skia.Rect.MakeLTRB(0, 0, W, depth), p)
        ctx.behind.mark(0, 0, W, depth, pad=0)
    _S.PRE.append(fn)


def dim_room(t0, t1, amount=100, fade_in=0.6, fade_out=0.3):
    """darken the room (not the people) by amount/255 between t0 and t1; depth words still sit on top. Opt-in."""
    def fn(ctx, t):
        v = env(t, t0, t1, fade_in, fade_out)
        if v > 0:
            ctx.behind.c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), fill((0, 0, 0), amount * v))
            ctx.behind.mark(0, 0, W, H, pad=0)
    _S.PRE.append(fn)


def wrap_text(text, f, width):
    lines, cur = [], ""
    for word in text.split(" "):
        test = (cur + " " + word).strip()
        if cur and text_width(test, f) > width:
            lines.append(cur)
            cur = word
        else:
            cur = test
    return lines + ([cur] if cur else [])


def prompt_box(L, t, text, t_in, t_type0, t_type1, t_enter, t_out, label="MÔ TẢ BẰNG LỜI", y0=None):
    """a chat box on black that types `text` between t_type0 and t_type1; its send button lights up at t_enter and
    everything fades out from t_out. Returns the box rectangle (for text placed above it) or None."""
    vb = clamp01((t - t_in) / 0.25) * (1 - clamp01((t - t_out) / 0.12))
    if t < t_in or vb <= 0:
        return None
    c = L.c
    size = 40 if YT else 42
    f = font("medium", size)
    bw = 1200 if YT else W - 168
    bx0, bx1 = (W - bw) / 2, (W + bw) / 2
    lines = wrap_text(text, f, bw - 132)
    lh = round(size * 1.38)
    by0 = y0 if y0 is not None else H / 2 - 55 * K      # leaves room above for card_text lines at dy -240 / -148
    by1 = by0 + 70 + lh * len(lines) + 60
    c.drawRRect(rrect(bx0, by0, bx1, by1, 34), fill((30, 32, 36), 235 * vb))
    c.drawRRect(rrect(bx0, by0, bx1, by1, 34), stroke(WHITE, 46 * vb, width=1.5))
    n = int(len(text) * clamp01((t - t_type0) / max(0.05, t_type1 - t_type0)))
    shown, y = 0, by0 + 78
    last = (bx0 + 44, y)
    for ln in lines:
        part = ln[:max(0, n - shown)]
        shown += len(ln) + 1
        if part:
            draw_text(L, part, f, bx0 + 44, y, rgb=WHITE, a=255 * vb, align="left")
            last = (bx0 + 44 + text_width(part, f), y)
        if n < shown:
            break
        y += lh
    if t < t_enter + 0.2 and int(t * 2.6) % 2 == 0:
        c.drawRect(skia.Rect.MakeLTRB(last[0] + 5, last[1] - 34, last[0] + 8, last[1] + 8), fill(MINT, 255 * vb))
    ke = clamp01((t - t_enter) / 0.3)
    sx, sy = bx1 - 64, by1 - 50
    c.drawCircle(sx, sy, 28 * (1 + 0.18 * (ke * (1 - ke) * 4)), fill(MINT if ke > 0 else (80, 84, 90), 255 * vb))
    c.drawLine(sx, sy + 11, sx, sy - 11, stroke(INK, 255 * vb, width=4))
    c.drawLine(sx, sy - 11, sx - 9, sy - 2, stroke(INK, 255 * vb, width=4))
    c.drawLine(sx, sy - 11, sx + 9, sy - 2, stroke(INK, 255 * vb, width=4))
    if label:
        draw_text(L, label, font("bold", 28), bx0 + 44, by0 - 24, rgb=WHITE, a=160 * vb, align="left", tracking=0.3 * 28)
    L.mark(bx0 - 30, by0 - 70, bx1 + 30, by1 + 30)
    return (bx0, by0, bx1, by1)


def title_slam(L, t, t0, text, sub=None, y=None, size=200, max_w=None):
    """the title on black: slams in from 1.22x with a glint across it; `sub` fades in under it."""
    if t < t0:
        return
    y = y if y is not None else H / 2 + 40 * K
    k = clamp01((t - t0) / 0.32)
    sc = 1.22 - 0.22 * ease_out_expo(k)
    mw = max_w or (1300 if YT else 930)
    f = font("black", size)
    f = font("black", size * min(1.0, mw / text_width(text, f, 0.02 * size)))
    trk = 0.02 * f.getSize()
    draw_text(L, text, f, W / 2, y, a=255 * clamp01(k * 3), tracking=trk, scale=sc, gradient=(WHITE, (186, 198, 214)),
              glow=(255, 236, 200), glow_a=60, glow_blur=30)
    ks = (t - t0 - 0.5) / 0.75
    if 0 <= ks <= 1:
        band = ks * (len(text) + 4) - 2

        def glint(i, nn):
            return (0, 0, 1.0, max(0.0, 1 - abs(i - band) / 1.6) ** 1.5)
        draw_text(L, text, f, W / 2, y, a=170, tracking=trk, scale=sc, per_char=glint)
    # the accent line clears the tallest glyph, Vietnamese marks included. It used to sit at a fixed 120 px, which cut
    # through the top of a large title (by 13 px on 9:16 and 52 px on 16:9)
    tops = [r.top() for r in f.getBounds(f.textToGlyphs(nfc(text)))]
    ly = y - (-min(tops) if tops else f.getMetrics().fCapHeight) - 22 * K
    L.c.drawLine(W / 2 - 170 * k, ly, W / 2 + 170 * k, ly, stroke(AMBER, 180 * k, width=2))
    if sub and t >= t0 + 0.45:
        v = clamp01((t - t0 - 0.45) / 0.12)
        e = ease_out_cubic(clamp01((t - t0 - 0.45) / 0.45))
        draw_text(L, sub, font("serif_i", 50 * K), W / 2, y + 98 * K, rgb=AMBER, a=255 * v, scale=1.07 - 0.07 * e)


def _bars(ctx, t):
    # drawn before everything else on the top layer, so captions and the YouTube rail stay readable on the bars
    hb = lerp(BAR * ease_out_cubic(clamp01(t / 0.32)), H / 2 + 4, curtain(t))
    if hb > 0.5:
        c = ctx.ui.c
        c.drawRect(skia.Rect.MakeLTRB(0, 0, W, hb), fill((0, 0, 0), 255))
        c.drawRect(skia.Rect.MakeLTRB(0, H - hb, W, H), fill((0, 0, 0), 255))
        ctx.ui.mark(0, 0, W, H, pad=0)


def _cards(ctx, t):
    for (t0, t1, fn, _cl, _op) in CARDS:
        if t0 <= t <= t1:
            fn(ctx, t, t0, t1)
    for tf in FLASHES:
        u = (t - tf) / 0.07
        if 0 <= u <= 1:     # one pure white frame, one fading: a longer or weaker flash only greys the picture
            ctx.ui.c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), fill((255, 255, 255), 255 * (1 - u) ** 1.3))
            ctx.ui.mark(0, 0, W, H, pad=0)


_S.PRE.append(_bars)
_S.POST.append(_cards)
_S.CAPTION_OFF.append(lambda t: curtain(t) >= 0.35)
