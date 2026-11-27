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

This module holds the palette, the treatments (TREAT) and the word drawing; rawgroups.py sets the stacks by hand.
"""
import skia

import engine as E
from engine import c4, nfc
from engine import col as argb  # noqa: F401  (skia.Color(r, g, b, a) is ColorSetARGB(a, r, g, b): the same colour)

E.FONTS.setdefault("serif_k", ("PlayfairDisplay-VF.ttf", 900))     # Playfair Display at its black weight

W, H = E.W, E.H
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


OUTLINE = None      # (rgb, width as a fraction of the size, alpha): set by a design whose background is bright


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


def head_top(ctx, spk="M"):
    """the top of the speaker's head on screen, from find_faces' marker"""
    fx, fy, ht = E.FACE[spk]
    return E.src_to_screen(ctx.cam, fx, ht)
