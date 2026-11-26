"""Caption style after the user's TikTok reference (@raw.to.reel, "Real Estate Video Editing Masterclass", seen
2026-11-24; the request: "phong cách trailer nhưng chữ mầu sắc phải chất như video này"). Used on tập 14-16 and approved
with the motion style (references/motion.md, 2026-11-26).

What the reference does, and what this module copies:
- every spoken phrase is a magazine stack over the speaker: the lead-in words small and white above the left end of
  the key word ("If your" / "thinking"), the key word huge, the words after it small and white under its right end
  ("about", "here");
- the key word takes one of a few treatments: a heavy rounded sans in lowercase (aqua "character", orange
  "completely"), heavy capitals (red "DIFFERENT" with a light edge, white "COMMUNITIES"), or a black-weight
  high-contrast serif (a sky-to-royal blue gradient "Calgary", "THINGS"; teal "Moving");
- the key word stands behind the speaker (the matte), its lower edge tucked behind the head; the small words sit in
  front; a soft shadow under every word keeps it legible over the trees;
- words come in as they are spoken: small words rise and fade in, the key word pops (1.25x -> 1x, ease-out-back).

The reference's navy-black words sit on a bright sky. This footage has dark trees behind the head, so the navy
treatment is kept for the white card scenes only.
"""
import math

import skia

import engine as E
import refstyle as R
import story as S
from engine import clamp01, ease_out_back, ease_out_cubic, font, nfc

E.FONTS.setdefault("serif_k", ("PlayfairDisplay-VF.ttf", 900))     # Playfair Display at its black weight

W, H = 1080, 1920
WHITE = (255, 255, 255)
AQUA = (40, 230, 228)
ORANGE = (255, 110, 32)
RED = (255, 46, 46)
NAVY = (20, 26, 40)
TEAL = (64, 242, 228)
BLUE = ((236, 249, 255), (150, 206, 255), (84, 146, 255))

TREAT = {
    "aqua": dict(kind="black", case="lower", rgb=AQUA),
    "orange": dict(kind="black", case="lower", rgb=ORANGE),
    "red": dict(kind="black", case="upper", rgb=RED, edge=(255, 236, 228)),
    "white": dict(kind="black", case="upper", rgb=WHITE),
    "blue": dict(kind="serif_k", case="title", grad=BLUE, edge=(255, 255, 255), edge_w=0.018),
    "teal": dict(kind="serif_k", case="title", rgb=TEAL, edge=(255, 255, 255), edge_w=0.018),
    "navy": dict(kind="black", case="upper", rgb=NAVY),
}
ROTATION = ["aqua", "blue", "orange", "white", "red", "teal"]
FORCE = {}          # normalised key phrase -> treatment name (set by the design)
TEXT = {}           # normalised key phrase -> text to show instead of the spoken words (spelling, names)


OUTLINE = None      # (rgb, width as a fraction of the size, alpha): set by a design whose background is bright


def c4(rgb, a):
    return skia.Color4f(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, max(0.0, min(1.0, a / 255)))


def argb(rgb, a):
    return skia.ColorSetARGB(int(max(0, min(255, a))), int(rgb[0]), int(rgb[1]), int(rgb[2]))


def cased(text, case):
    text = nfc(text)
    if case == "upper":
        return text.upper()
    if case == "title":
        return text[:1].upper() + text[1:]
    return text


def top_of(text, f):
    """height of the tallest glyph above the baseline (diacritics included), in px"""
    g = f.textToGlyphs(nfc(text))
    if len(g) == 0:
        return f.getSize() * 0.75
    return -min(r.top() for r in f.getBounds(g))


def draw_word(c, text, f, x, y, a, rgb=WHITE, grad=None, edge=None, shadow=0.55, edge_w=0.04):
    """one run of text at baseline (x, y), left-aligned: soft shadow, optional light edge, then the face"""
    text = nfc(text)
    sz = f.getSize()
    if OUTLINE is not None and shadow > 0:      # a dark rim: this footage has a bright sky behind the words
        orgb, frac, oal = OUTLINE
        op = skia.Paint(AntiAlias=True, Color=c4(orgb, a * oal))
        op.setStyle(skia.Paint.kStroke_Style)
        op.setStrokeWidth(max(5.0, sz * frac * 2))
        op.setStrokeJoin(skia.Paint.kRound_Join)
        c.drawString(text, x, y, f, op)
    if shadow > 0:
        sp = skia.Paint(AntiAlias=True, Color=c4((0, 0, 0), a * shadow))
        sp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, max(3.0, sz * 0.07)))
        c.drawString(text, x, y + sz * 0.04, f, sp)
    if edge is not None:
        ep = skia.Paint(AntiAlias=True, Color=c4(edge, a))
        ep.setStyle(skia.Paint.kStroke_Style)
        ep.setStrokeWidth(max(2.0, sz * edge_w))
        ep.setStrokeJoin(skia.Paint.kRound_Join)
        c.drawString(text, x, y, f, ep)
    p = skia.Paint(AntiAlias=True)
    if grad:
        top = y - top_of(text, f)
        p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, top), skia.Point(0, y + sz * 0.04)],
                                                   [argb(g, a) for g in grad], [0.0, 0.48, 1.0]))
    else:
        p.setColor4f(c4(rgb, a))
    c.drawString(text, x, y, f, p)
    return f.measureText(text)


# ----------------------------------------------------------------------------
# the stack
# ----------------------------------------------------------------------------
_TREAT_OF = {}


def treatment(ln, key):
    """the key's treatment: forced by the design, else the rotation (never the same as the line before)"""
    i = S.LINES.index(ln) if ln in S.LINES else 0
    if i in _TREAT_OF:
        return _TREAT_OF[i]
    ph = S._norm(" ".join(x["disp"] for x in key))
    name = FORCE.get(ph)
    if name is None:
        prev = _TREAT_OF.get(i - 1)
        k = i % len(ROTATION)
        name = ROTATION[k]
        if name == prev:
            name = ROTATION[(k + 1) % len(ROTATION)]
    _TREAT_OF[i] = name
    return name


def key_text(key, tr):
    ph = S._norm(" ".join(x["disp"] for x in key))
    if ph in TEXT:
        return TEXT[ph]
    return cased(" ".join(R.disp(x["disp"]) for x in key).rstrip("?"), TREAT[tr]["case"])


def _k(t, x, d=0.13):
    return clamp01((t - (x["s"] - 0.05)) / d)


def small_row(L, t, words, x, y, size, a, align="left", max_w=900):
    """the small white words, each fading and rising in as it is spoken; x is the left (or centre) edge"""
    if not words:
        return 0.0
    txts = [R.disp(w["disp"]) for w in words]
    f = font("bold", size)
    sp = size * 0.26
    widths = [f.measureText(nfc(s)) for s in txts]
    total = sum(widths) + sp * (len(txts) - 1)
    if total > max_w:
        f = font("bold", size * max_w / total)
        sp *= max_w / total
        widths = [f.measureText(nfc(s)) for s in txts]
        total = sum(widths) + sp * (len(txts) - 1)
    pos = x - total / 2 if align == "center" else (x - total if align == "right" else x)
    for w, s, wd in zip(words, txts, widths):
        k = _k(t, w)
        if k > 0:
            draw_word(L.c, s, f, pos, y + (1 - ease_out_cubic(k)) * 14, a * k, WHITE, shadow=0.6)
        pos += wd + sp
    left = x - total / 2 if align == "center" else (x - total if align == "right" else x)
    L.mark(left - 20, y - size * 1.25, left + total + 20, y + size * 0.45)
    return total


def stack(ctx, t, ln, cx, base_y, big=178, small=54, max_w=930, behind=True, lift=0.0):
    """draws one caption line as the reference's stack. base_y = the key word's baseline (screen px). Returns the
    (top, bottom) it used."""
    before, key, after = R.split_rows(ln)
    end_v = 1.0 if ln[0]["line_cut"] else clamp01((ln[0]["line_end"] - t) / 0.12)
    if end_v <= 0:
        return None
    a = 255 * end_v
    front = ctx.front
    if not key:                                       # no key phrase: one medium white row
        small_row(front, t, ln, cx, base_y, small * 1.3, a, align="center", max_w=max_w)
        return (base_y - small * 1.6, base_y + small * 0.5)
    tr = treatment(ln, key)
    spec = TREAT[tr]
    txt = key_text(key, tr)
    f = font(spec["kind"], big)
    kw = f.measureText(nfc(txt))
    if kw > max_w:
        f = font(spec["kind"], big * max_w / kw)
        kw = f.measureText(nfc(txt))
    sz = f.getSize()
    if after:
        base_y -= lift
    top = top_of(txt, f)
    x0 = cx - kw / 2
    # the lead-in: small, above the left part of the key word (centred when it is wider than the key)
    if before:
        fb = font("bold", small)
        bw = sum(fb.measureText(nfc(R.disp(w["disp"]))) for w in before) + small * 0.26 * (len(before) - 1)
        yb = base_y - top - small * 0.30
        if bw <= kw * 0.92:
            small_row(front, t, before, x0 + kw * 0.04, yb, small, a)
        else:
            small_row(front, t, before, cx, yb, small, a, align="center", max_w=max_w)
    # the key word: pops in on its first word, behind the speaker
    k0 = _k(t, key[0], 0.09)
    if k0 > 0:
        L = ctx.behind if behind else ctx.front
        c = L.c
        pop = 1.0 + 0.25 * (1 - ease_out_back(clamp01((t - (key[0]["s"] - 0.06)) / 0.24)))
        c.save()
        c.translate(cx, base_y - top * 0.45)
        c.scale(pop, pop)
        c.translate(-cx, -(base_y - top * 0.45))
        draw_word(c, txt, f, x0, base_y, a * k0, spec.get("rgb", WHITE), spec.get("grad"), spec.get("edge"),
                  shadow=0.5)
        c.restore()
        L.mark(x0 - 40, base_y - top * 1.3 - 20, x0 + kw + 40, base_y + sz * 0.35)
    # the words after it: small, under the right end of the key word
    bottom = base_y + sz * 0.12
    if after:
        fa = font("bold", small)
        aw = sum(fa.measureText(nfc(R.disp(w["disp"]))) for w in after) + small * 0.26 * (len(after) - 1)
        ya = base_y + small * 1.05
        if aw <= kw * 0.92:
            small_row(front, t, after, x0 + kw * 0.96, ya, small, a, align="right")
        else:
            small_row(front, t, after, cx, ya, small, a, align="center", max_w=max_w)
        bottom = ya + small * 0.3
    return (base_y - top - (small * 1.4 if before else 0), bottom)


def head_top(ctx, spk="M"):
    """the top of the speaker's head on screen, from find_faces' marker"""
    fx, fy, ht = E.FACE[spk]
    return E.src_to_screen(ctx.cam, fx, ht)


def kinetic(hidden=lambda t: False, tuck=0.16, big=178, small=54, lift=70, min_top=250):
    """the reference's stacks everywhere a line is spoken and nothing covers the frame. The key word's baseline sits
    `tuck` x its size below the top of the head, so the head hides the lower edge of its middle letters."""
    @S.ev(0.0, S.DUR)
    def _raw(ctx, t):
        if hidden(t):
            return
        ln = R.active_line(t)
        if not ln:
            return
        hx, hy = head_top(ctx)
        base = hy + tuck * big
        top_needed = base - big * 0.95 - small * 1.4
        if top_needed < min_top:
            base += min_top - top_needed
        stack(ctx, t, ln, W / 2, base, big=big, small=small, lift=lift)


def setup(keys=(), weak=()):
    """the key phrases of the episode (each line shows its last key run big); the caption bar stays off"""
    style = ("black", WHITE, 1.0)
    S.KEYS.update({k: style for k in keys})
    R.WEAK.update(S._norm(w) for w in weak)
    S.CAPTION_OFF.append(lambda t: True)
