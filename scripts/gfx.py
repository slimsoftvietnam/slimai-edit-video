"""Reusable motion-graphics components (skia 87.9) for the edit.

All components draw into engine.Layer objects. Times are output-timeline seconds.
"""
import math

import skia

from engine import (AMBER, CORAL, GOLD, INK, MINT, SKY, WHITE, clamp01, col, draw_text, ease_in_cubic,
                    ease_in_out_cubic, ease_out_back, ease_out_cubic, ease_out_expo, env, fill, font, lerp,
                    nfc, rrect, spring, stroke, text_width)


# ----------------------------------------------------------------------------
# icons (line style, drawn centred at x, y inside a box of size s)
# ----------------------------------------------------------------------------
def _p(sw, rgb, a):
    return stroke(rgb, a, width=sw)


def icon(c, kind, x, y, s, rgb=WHITE, a=255, sw=None, prog=1.0):
    """prog in [0,1] lets icons draw-on (used sparingly)."""
    sw = sw or max(2.0, s * 0.085)
    p = _p(sw, rgb, a * clamp01(prog * 1.5))
    c.save()
    c.translate(x, y)
    h = s / 2
    if kind == "folder":
        path = skia.Path()
        path.moveTo(-h, -h * 0.55)
        path.lineTo(-h, h * 0.75)
        path.lineTo(h, h * 0.75)
        path.lineTo(h, -h * 0.35)
        path.lineTo(-h * 0.05, -h * 0.35)
        path.lineTo(-h * 0.25, -h * 0.62)
        path.lineTo(-h * 0.85, -h * 0.62)
        path.close()
        c.drawPath(path, p)
    elif kind == "file":
        path = skia.Path()
        path.moveTo(-h * 0.62, -h * 0.85)
        path.lineTo(h * 0.25, -h * 0.85)
        path.lineTo(h * 0.65, -h * 0.45)
        path.lineTo(h * 0.65, h * 0.85)
        path.lineTo(-h * 0.62, h * 0.85)
        path.close()
        c.drawPath(path, p)
        for k in range(3):
            yy = -h * 0.1 + k * h * 0.3
            c.drawLine(-h * 0.35, yy, h * 0.38 - (k == 2) * h * 0.3, yy, _p(sw * 0.8, rgb, a * 0.8))
    elif kind == "box":
        path = skia.Path()
        path.moveTo(0, -h * 0.9)
        path.lineTo(h * 0.85, -h * 0.45)
        path.lineTo(h * 0.85, h * 0.5)
        path.lineTo(0, h * 0.95)
        path.lineTo(-h * 0.85, h * 0.5)
        path.lineTo(-h * 0.85, -h * 0.45)
        path.close()
        path.moveTo(-h * 0.85, -h * 0.45)
        path.lineTo(0, 0)
        path.lineTo(h * 0.85, -h * 0.45)
        path.moveTo(0, 0)
        path.lineTo(0, h * 0.95)
        c.drawPath(path, p)
    elif kind == "clock":
        c.drawCircle(0, 0, h * 0.8, p)
        c.drawLine(0, 0, 0, -h * 0.48, p)
        c.drawLine(0, 0, h * 0.35, h * 0.2, p)
    elif kind == "history":
        oval = skia.Rect(-h * 0.8, -h * 0.8, h * 0.8, h * 0.8)
        path = skia.Path()
        path.addArc(oval, 200, 290)
        c.drawPath(path, p)
        ax, ay = h * 0.8 * math.cos(math.radians(200)), h * 0.8 * math.sin(math.radians(200))
        c.drawLine(ax, ay, ax - h * 0.25, ay - h * 0.28, p)
        c.drawLine(ax, ay, ax + h * 0.3, ay - h * 0.12, p)
        c.drawLine(0, 0, 0, -h * 0.42, p)
        c.drawLine(0, 0, h * 0.3, h * 0.18, p)
    elif kind == "branch":
        r = h * 0.2
        c.drawCircle(-h * 0.45, -h * 0.62, r, p)
        c.drawCircle(-h * 0.45, h * 0.62, r, p)
        c.drawCircle(h * 0.5, -h * 0.3, r, p)
        c.drawLine(-h * 0.45, -h * 0.42, -h * 0.45, h * 0.42, p)
        path = skia.Path()
        path.moveTo(h * 0.5, -h * 0.1)
        path.cubicTo(h * 0.5, h * 0.3, -h * 0.45, h * 0.1, -h * 0.45, h * 0.42)
        c.drawPath(path, p)
    elif kind == "shield":
        path = skia.Path()
        path.moveTo(0, -h * 0.92)
        path.cubicTo(h * 0.45, -h * 0.7, h * 0.65, -h * 0.68, h * 0.8, -h * 0.68)
        path.lineTo(h * 0.8, -h * 0.05)
        path.cubicTo(h * 0.8, h * 0.45, h * 0.4, h * 0.75, 0, h * 0.95)
        path.cubicTo(-h * 0.4, h * 0.75, -h * 0.8, h * 0.45, -h * 0.8, -h * 0.05)
        path.lineTo(-h * 0.8, -h * 0.68)
        path.cubicTo(-h * 0.65, -h * 0.68, -h * 0.45, -h * 0.7, 0, -h * 0.92)
        c.drawPath(path, p)
        path = skia.Path()
        path.moveTo(-h * 0.35, 0.0)
        path.lineTo(-h * 0.08, h * 0.28)
        path.lineTo(h * 0.4, -h * 0.25)
        c.drawPath(path, p)
    elif kind == "robot":
        c.drawRRect(rrect(-h * 0.75, -h * 0.45, h * 0.75, h * 0.7, h * 0.25), p)
        c.drawLine(0, -h * 0.45, 0, -h * 0.75, p)
        c.drawCircle(0, -h * 0.85, h * 0.1, p)
        c.drawCircle(-h * 0.3, h * 0.08, h * 0.1, fill(rgb, a))
        c.drawCircle(h * 0.3, h * 0.08, h * 0.1, fill(rgb, a))
        c.drawLine(-h * 0.25, h * 0.42, h * 0.25, h * 0.42, p)
    elif kind == "user":
        c.drawCircle(0, -h * 0.35, h * 0.38, p)
        path = skia.Path()
        path.moveTo(-h * 0.8, h * 0.9)
        path.cubicTo(-h * 0.75, h * 0.2, h * 0.75, h * 0.2, h * 0.8, h * 0.9)
        c.drawPath(path, p)
    elif kind == "undo":
        # counter-clockwise arrow: arc from 200deg sweeping -250deg, arrowhead at the end
        r0 = h * 0.62
        oval = skia.Rect(-r0, -r0, r0, r0)
        sweep = -250 * clamp01(prog)
        path = skia.Path()
        path.addArc(oval, 200, sweep)
        c.drawPath(path, p)
        ang = math.radians(200 + sweep)
        ex, ey = r0 * math.cos(ang), r0 * math.sin(ang)
        # tangent direction for CCW travel
        tx, ty = math.sin(ang), -math.cos(ang)
        nx, ny = -ty, tx
        L = h * 0.42
        tri = skia.Path()
        tri.moveTo(ex + tx * L * 0.55, ey + ty * L * 0.55)
        tri.lineTo(ex - tx * L * 0.45 + nx * L * 0.5, ey - ty * L * 0.45 + ny * L * 0.5)
        tri.lineTo(ex - tx * L * 0.45 - nx * L * 0.5, ey - ty * L * 0.45 - ny * L * 0.5)
        tri.close()
        if prog > 0.05:
            c.drawPath(tri, fill(rgb, a * clamp01(prog * 1.5)))
    elif kind == "link":
        c.save()
        c.rotate(-45)
        c.drawRRect(rrect(-h * 0.95, -h * 0.3, h * 0.05, h * 0.3, h * 0.3), p)
        c.drawRRect(rrect(-h * 0.05, -h * 0.3, h * 0.95, h * 0.3, h * 0.3), p)
        c.restore()
    elif kind == "code":
        path = skia.Path()
        path.moveTo(-h * 0.35, -h * 0.55)
        path.lineTo(-h * 0.85, 0)
        path.lineTo(-h * 0.35, h * 0.55)
        path.moveTo(h * 0.35, -h * 0.55)
        path.lineTo(h * 0.85, 0)
        path.lineTo(h * 0.35, h * 0.55)
        path.moveTo(h * 0.12, -h * 0.75)
        path.lineTo(-h * 0.12, h * 0.75)
        c.drawPath(path, p)
    elif kind == "calendar":
        c.drawRRect(rrect(-h * 0.8, -h * 0.65, h * 0.8, h * 0.85, h * 0.15), p)
        c.drawLine(-h * 0.8, -h * 0.25, h * 0.8, -h * 0.25, p)
        c.drawLine(-h * 0.4, -h * 0.9, -h * 0.4, -h * 0.45, p)
        c.drawLine(h * 0.4, -h * 0.9, h * 0.4, -h * 0.45, p)
        for i in range(3):
            for j in range(2):
                c.drawCircle(-h * 0.4 + i * h * 0.4, h * 0.12 + j * h * 0.38, sw * 0.6, fill(rgb, a))
    elif kind == "list":
        for k in range(3):
            yy = -h * 0.55 + k * h * 0.55
            path = skia.Path()
            path.moveTo(-h * 0.85, yy)
            path.lineTo(-h * 0.7, yy + h * 0.14)
            path.lineTo(-h * 0.45, yy - h * 0.14)
            c.drawPath(path, p)
            c.drawLine(-h * 0.2, yy, h * 0.85, yy, p)
    elif kind == "check":
        path = skia.Path()
        path.moveTo(-h * 0.6, 0.0)
        path.lineTo(-h * 0.15, h * 0.45)
        path.lineTo(h * 0.65, -h * 0.45)
        c.drawPath(path, p)
    elif kind == "cross":
        c.drawLine(-h * 0.5, -h * 0.5, h * 0.5, h * 0.5, p)
        c.drawLine(-h * 0.5, h * 0.5, h * 0.5, -h * 0.5, p)
    elif kind == "warn":
        path = skia.Path()
        path.moveTo(0, -h * 0.85)
        path.lineTo(h * 0.9, h * 0.75)
        path.lineTo(-h * 0.9, h * 0.75)
        path.close()
        c.drawPath(path, p)
        c.drawLine(0, -h * 0.3, 0, h * 0.2, p)
        c.drawCircle(0, h * 0.48, sw * 0.6, fill(rgb, a))
    elif kind == "star":
        path = skia.Path()
        for k in range(10):
            r = h * (0.9 if k % 2 == 0 else 0.4)
            ang = -math.pi / 2 + k * math.pi / 5
            (path.moveTo if k == 0 else path.lineTo)(r * math.cos(ang), r * math.sin(ang))
        path.close()
        c.drawPath(path, p)
    elif kind == "fork":
        r = h * 0.18
        c.drawCircle(-h * 0.45, -h * 0.65, r, p)
        c.drawCircle(h * 0.45, -h * 0.65, r, p)
        c.drawCircle(0, h * 0.68, r, p)
        path = skia.Path()
        path.moveTo(-h * 0.45, -h * 0.47)
        path.lineTo(-h * 0.45, -h * 0.15)
        path.cubicTo(-h * 0.45, h * 0.1, 0, h * 0.05, 0, h * 0.5)
        path.moveTo(h * 0.45, -h * 0.47)
        path.lineTo(h * 0.45, -h * 0.15)
        path.cubicTo(h * 0.45, h * 0.1, 0, h * 0.05, 0, h * 0.5)
        c.drawPath(path, p)
    elif kind == "camera":
        c.drawRRect(rrect(-h * 0.9, -h * 0.5, h * 0.45, h * 0.55, h * 0.12), p)
        path = skia.Path()
        path.moveTo(h * 0.45, -h * 0.15)
        path.lineTo(h * 0.9, -h * 0.42)
        path.lineTo(h * 0.9, h * 0.45)
        path.lineTo(h * 0.45, h * 0.2)
        c.drawPath(path, p)
    elif kind == "spark":
        for ang in range(0, 360, 45):
            r0, r1 = (h * 0.25, h * 0.9) if ang % 90 == 0 else (h * 0.25, h * 0.55)
            ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            c.drawLine(r0 * ca, r0 * sa, r1 * ca, r1 * sa, p)
    elif kind == "trash":
        c.drawLine(-h * 0.75, -h * 0.55, h * 0.75, -h * 0.55, p)
        path = skia.Path()
        path.moveTo(-h * 0.25, -h * 0.55)
        path.lineTo(-h * 0.18, -h * 0.85)
        path.lineTo(h * 0.18, -h * 0.85)
        path.lineTo(h * 0.25, -h * 0.55)
        path.moveTo(-h * 0.6, -h * 0.55)
        path.lineTo(-h * 0.46, h * 0.88)
        path.lineTo(h * 0.46, h * 0.88)
        path.lineTo(h * 0.6, -h * 0.55)
        path.moveTo(-h * 0.2, -h * 0.2)
        path.lineTo(-h * 0.16, h * 0.55)
        path.moveTo(h * 0.2, -h * 0.2)
        path.lineTo(h * 0.16, h * 0.55)
        c.drawPath(path, p)
    elif kind == "upload":
        path = skia.Path()
        path.moveTo(-h * 0.75, h * 0.3)
        path.lineTo(-h * 0.75, h * 0.8)
        path.lineTo(h * 0.75, h * 0.8)
        path.lineTo(h * 0.75, h * 0.3)
        path.moveTo(0, h * 0.4)
        path.lineTo(0, -h * 0.75)
        path.moveTo(-h * 0.4, -h * 0.35)
        path.lineTo(0, -h * 0.75)
        path.lineTo(h * 0.4, -h * 0.35)
        c.drawPath(path, p)
    elif kind == "brain":
        # simple memory "chip" icon
        c.drawRRect(rrect(-h * 0.55, -h * 0.55, h * 0.55, h * 0.55, h * 0.12), p)
        c.drawRRect(rrect(-h * 0.22, -h * 0.22, h * 0.22, h * 0.22, h * 0.05), p)
        for k in (-0.3, 0.0, 0.3):
            c.drawLine(h * k, -h * 0.55, h * k, -h * 0.85, p)
            c.drawLine(h * k, h * 0.55, h * k, h * 0.85, p)
            c.drawLine(-h * 0.55, h * k, -h * 0.85, h * k, p)
            c.drawLine(h * 0.55, h * k, h * 0.85, h * k, p)
    c.restore()


# ----------------------------------------------------------------------------
# chips (pills)
# ----------------------------------------------------------------------------
def chip(layer, t, t0, t1, x, y, text, icon_kind=None, style="glow", size=40, accent=AMBER,
         anchor="center", text_rgb=WHITE, font_kind="semi", pop=True, alpha=1.0):
    """Pill label with optional icon. Pops in with a spring, fades out.
    Returns rect or None."""
    v = env(t, t0, t1, 0.001, 0.22) * alpha
    if v <= 0:
        return None
    k = clamp01((t - t0) / 0.42)
    sc = spring(k, 6.5, 1.6) if pop else ease_out_cubic(k)
    sc = 0.55 + 0.45 * sc if pop else 1.0
    fade = clamp01((t - t0) / 0.12) * v
    fnt = font(font_kind, size)
    tw = text_width(text, fnt)
    ic = size * 1.05 if icon_kind else 0
    gap = size * 0.4 if icon_kind else 0
    padx, h = size * 0.75, size * 1.95
    w = tw + ic + gap + padx * 2
    if anchor == "left":
        cx = x + w / 2
    elif anchor == "right":
        cx = x - w / 2
    else:
        cx = x
    c = layer.c
    c.save()
    c.translate(cx, y)
    c.scale(sc, sc)
    r = h / 2
    if style == "glow":
        c.drawRRect(rrect(-w / 2, -h / 2, w / 2, h / 2, r), fill(INK, 150 * fade))
        c.drawRRect(rrect(-w / 2, -h / 2, w / 2, h / 2, r), stroke(accent, 230 * fade, width=6, blur=9))
        c.drawRRect(rrect(-w / 2, -h / 2, w / 2, h / 2, r), stroke(lerp_rgb(accent, WHITE, 0.45), 255 * fade, width=2.6))
    elif style == "solid":
        c.drawRRect(rrect(-w / 2, -h / 2, w / 2, h / 2, r), fill(accent, 245 * fade))
    elif style == "dark":
        c.drawRRect(rrect(-w / 2, -h / 2, w / 2, h / 2, r), fill(INK, 190 * fade))
        c.drawRRect(rrect(-w / 2, -h / 2, w / 2, h / 2, r), stroke(WHITE, 60 * fade, width=1.5))
    tx = -w / 2 + padx
    if icon_kind:
        icon(c, icon_kind, tx + ic / 2, 0, ic, accent if style != "solid" else INK, 255 * fade)
        tx += ic + gap
    m = fnt.getMetrics()
    base = (-m.fAscent - m.fDescent) / 2 + size * 0.02
    draw_text(layer, text, fnt, tx, base, rgb=(INK if style == "solid" else text_rgb), a=255 * fade,
              align="left")
    c.restore()
    x0, y0, x1, y1 = cx - w / 2 * sc, y - h / 2 * sc, cx + w / 2 * sc, y + h / 2 * sc
    layer.mark(x0, y0, x1, y1, pad=30)
    return (x0, y0, x1, y1)


def lerp_rgb(a, b, x):
    return tuple(int(lerp(a[i], b[i], x)) for i in range(3))


# ----------------------------------------------------------------------------
# big depth text (behind the person)
# ----------------------------------------------------------------------------
def big_text(layer, t, t0, t1, text, cx, base_y, size=210, kind="black", rgb=WHITE, max_w=960,
             tracking=-0.02, enter="rise", glow=None, glow_a=120, gradient=None, exit_="fade",
             stagger=0.035, shadow=0.0, alpha=1.0, fade_out=0.28, sheen=None):
    """Per-glyph animated display text. base_y = baseline (screen px)."""
    v = env(t, t0, t1, 0.001, fade_out) * alpha
    if v <= 0:
        return None
    fnt = font(kind, size)
    tw = text_width(text, fnt, tracking * size)
    if tw > max_w:
        size = size * max_w / tw
        fnt = font(kind, size)
    trk = tracking * size
    n = len(nfc(text))
    lt = t - t0

    def per_char(i, nn):
        if enter == "rise":
            k = clamp01((lt - i * stagger) / 0.5)
            e = ease_out_expo(k)
            return (0, (1 - e) * size * 0.55, 1.0, clamp01(k * 2.2))
        if enter == "type":
            k = clamp01((lt - i * stagger) / 0.06)
            return (0, 0, 1.0, k)
        if enter == "pop":
            k = clamp01((lt - i * stagger) / 0.45)
            return (0, 0, 0.6 + 0.4 * spring(k, 7, 1.5), clamp01(k * 3))
        if enter == "scale":
            k = ease_out_cubic(clamp01(lt / 0.5))
            return (0, 0, 1.0, k)
        return (0, 0, 1.0, 1.0)

    sc = 1.0
    if enter == "scale":
        sc = 1.18 - 0.18 * ease_out_cubic(clamp01(lt / 0.6))
    if enter == "settle":
        sc = 1.07 - 0.07 * ease_out_cubic(clamp01(lt / 0.9))
    # gentle drift while visible
    drift = 1.0 + 0.025 * clamp01(lt / max(0.1, t1 - t0))
    r = draw_text(layer, text, fnt, cx, base_y, rgb=rgb, a=255 * v, align="center", tracking=trk,
                  per_char=per_char, glow=glow, glow_a=glow_a, glow_blur=22, gradient=gradient,
                  scale=sc * drift, shadow=shadow, shadow_a=90)
    if sheen is not None:
        # a soft glint that sweeps across the letters once, `sheen` s after entry
        ks = (lt - sheen) / 0.7
        if 0 <= ks <= 1:
            band = ks * (n + 4) - 2

            def glint(i, nn):
                dx_, dy_, sc_, am = per_char(i, nn)
                d = abs(i - band)
                return (dx_, dy_, sc_, am * max(0.0, 1 - d / 1.6) ** 1.5)
            draw_text(layer, text, fnt, cx, base_y, rgb=WHITE, a=170 * v, align="center", tracking=trk,
                      per_char=glint, scale=sc * drift)
    return r


def kicker(layer, t, t0, t1, text, x, y, size=34, rgb=AMBER, tracking=0.24, kind="bold", align="center"):
    v = env(t, t0, t1, 0.25, 0.2)
    if v <= 0:
        return None
    k = ease_out_cubic(clamp01((t - t0) / 0.5))
    return draw_text(layer, text, font(kind, size), x, y + (1 - k) * 16, rgb=rgb, a=255 * v, align=align,
                     tracking=tracking * size * (1.0 + 0.6 * (1 - k)), shadow=6, shadow_a=140)


def strike(layer, t, t0, x0, x1, y, rgb=CORAL, width=10, t1=None, dur=0.32):
    """Animated strike-through line (draws left->right)."""
    if t < t0 or (t1 is not None and t > t1):
        return
    k = ease_in_out_cubic(clamp01((t - t0) / dur))
    v = 1.0 if t1 is None else env(t, t0, t1, 0.001, 0.2)
    xe = lerp(x0, x1, k)
    c = layer.c
    c.drawLine(x0, y, xe, y, stroke(rgb, 120 * v, width=width * 2.2, blur=10))
    c.drawLine(x0, y, xe, y, stroke(rgb, 255 * v, width=width))
    layer.mark(x0, y - 30, x1, y + 30)


def glass_panel(ctx, layer, t, t0, t1, x0, y0, x1, y1, r=34, accent=None, enter_dy=40, alpha=1.0):
    """Register a frosted glass panel + draw its rim. Returns (v, dy) for content."""
    v = env(t, t0, t1, 0.001, 0.25) * alpha
    if v <= 0:
        return 0.0, 0.0
    k = ease_out_cubic(clamp01((t - t0) / 0.45))
    dy = (1 - k) * enter_dy
    sc = 0.94 + 0.06 * k
    a = v * clamp01((t - t0) / 0.2)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 + dy
    w, h = (x1 - x0) * sc, (y1 - y0) * sc
    gx0, gy0, gx1, gy1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    ctx.glass.append((gx0, gy0, gx1, gy1, r, a))
    c = layer.c
    c.drawRRect(rrect(gx0, gy0, gx1, gy1, r), stroke(WHITE, 70 * a, width=1.6))
    if accent is not None:
        c.drawRRect(rrect(gx0, gy0, gx1, gy1, r), stroke(accent, 70 * a, width=5, blur=10))
    # top sheen
    sh = skia.Paint(AntiAlias=True)
    sh.setShader(skia.GradientShader.MakeLinear([skia.Point(0, gy0), skia.Point(0, gy0 + h * 0.5)],
                                                [col(WHITE, 26 * a), col(WHITE, 0)]))
    c.drawRRect(rrect(gx0, gy0, gx1, gy1, r), sh)
    layer.mark(gx0, gy0, gx1, gy1, pad=30)
    return a, dy


def dot(c, x, y, r, rgb, a=255, glow=True):
    if glow:
        c.drawCircle(x, y, r * 2.2, fill(rgb, 90 * a / 255, blur=r * 1.2))
    c.drawCircle(x, y, r, fill(rgb, a))


def draw_on_path(c, path, prog, paint):
    """Draw first `prog` fraction of a path using a dash effect."""
    if prog <= 0:
        return
    pm = skia.PathMeasure(path, False)
    L = pm.getLength()
    if prog >= 1:
        c.drawPath(path, paint)
        return
    p = skia.Paint(paint)
    p.setPathEffect(skia.DashPathEffect.Make([L * prog, L * 2 + 10], 0))
    c.drawPath(path, p)
