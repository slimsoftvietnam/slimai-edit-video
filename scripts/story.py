"""The design library. A project's design.py does `from story import *`, fills the anchors, registers
events with @ev and cues with cue(), and the same file then renders both formats.

Format differences live here (PROFILES) and in pick(youtube_value, tiktok_value) / place() calls, so a
new video is authored once. See references/design-playbook.md for the layout rules and the worked
example in examples/repo-ai-agent/design.py.
"""
import functools
import json
import math
import os
import re
import sys
import unicodedata

import skia

from engine import (AMBER, BASE, CFG, CORAL, FACE, FMT, FPS, GOLD, HEADBOX, INK, MINT, PROJECT, SHOTS, SKY, WHITE, H, W,
                    clamp01, col, draw_text, ease_in_cubic, ease_in_out_cubic, ease_in_out_sine, ease_out_back,
                    ease_out_cubic, ease_out_expo, env, fill, font, lerp, nfc, rrect, shot_cam, spring,
                    src_to_screen, stroke, text_width)
from gfx import big_text, chip, dot, draw_on_path, glass_panel, icon, kicker, strike

YT, TK = FMT == "youtube", FMT == "tiktok"
PROFILES = {
    "youtube": dict(cap_size=58, cap_y=968, cap_maxw=1500, cap_target=21, cap_max=32, scrim=(800, 100), mx=96,
                    top=50, rail=True, end_hold=8.0, stage_x=(120, 1150), stage_cy=500, stage_hmax=640,
                    card=(1196, 320, 1836, 680), split_cap_y=None),
    "tiktok": dict(cap_size=66, cap_y=1352, cap_maxw=900, cap_target=15, cap_max=24, scrim=(560, 125), mx=70,
                   top=240, rail=False, end_hold=2.8, stage_x=(60, 1020), stage_cy=525, stage_hmax=550,
                   card=(125, 823, 955, 1290), split_cap_y=1000),
}
P = PROFILES[FMT]
MX = P["mx"]
CAP_Y = P["cap_y"]
SCRIM_R = P["scrim"]
PIP_RECT = P["card"]
PIP_T = 0.5

TL = json.load(open(os.path.join(PROJECT, "timeline.json"), encoding="utf-8"))
WORDS, CLIPS, DUR = TL["words"], TL["clips"], TL["duration"]
GAPS = [tuple(g) for g in TL.get("gaps", [])]    # (t0, t1, beat): silences left for trailer title cards
CL = [c["out_in"] for c in CLIPS]
END_HOLD = float(CFG.get("end_hold", {}).get(FMT, P["end_hold"]))
TOTAL = DUR + END_HOLD

# registered by the project's design.py
A = {}                 # named word anchors (output seconds)
SHOT_OVERRIDES = []    # (t0, t1, shot name)
PUNCHES = []           # (time, extra zoom fraction, attack, hold, release)
PIP = []               # (t_in, t_out): speaker shrinks into the card over PIP_T from t_in, grows back from t_out
SPLIT = []             # (t0, t1, top, bottom): split screen, one speaker per half (split_screen(); vertical only)
SPLIT_FRAME = {}       # speaker -> (source centre x, centre y, source height one half shows); unset: from the face
LEAKS = []             # light-leak times
LABELS = []            # (time, "01", "title"): chapter rail, YouTube only
YT_CHAPTERS = []       # (time, title) for the description; YouTube needs >= 10 s per chapter
MUSIC = dict(drop=None, sections=[], stops=[], bpm=96.0, transpose=0, tail=None)
KEYS = {}              # caption keyword -> (font kind, colour, size multiple)
# lower-case word -> displayed form. Never map "ai": in Vietnamese it is also the pronoun ("ai cũng" = everyone),
# and Whisper already writes the technology as "AI".
KEEP_CASE = {"github": "GitHub"}
NO_BREAK = {"AI"}      # capitalised words that are not a sentence start, e.g. "Anh" in "tiếng Anh"
CUES, EVENTS = [], []
SCORE = []             # (time, kind, options): a trailer score instead of the composed music (trailer_score.py)
PRE, POST = [], []     # fn(ctx, t) drawn before every event / after the captions (the trailer kit uses both)
CAPTION_OFF = []       # fn(t) -> True while captions must stay hidden, e.g. under a black title card
CCTV_T = [None, None]


def pick(youtube, tiktok):
    return youtube if YT else tiktok


def _norm(s):
    return re.sub(r"[^\w]", "", unicodedata.normalize("NFC", s).lower())


def at(word, near, tol=1.6, end=False):
    """Output time of `word` spoken nearest to `near` (seconds)."""
    key = _norm(word)
    c = [w for w in WORDS if _norm(w["w"]).startswith(key)]
    if not c:
        raise KeyError(word)
    best = min(c, key=lambda w: abs(w["s"] - near))
    if abs(best["s"] - near) > tol:
        raise KeyError(f"{word}@{near}: nearest {best['s']}")
    return best["e"] if end else best["s"]


def clip_at(t):
    """the clip playing at t; inside a gap or the end hold, the clip before it."""
    prev = CLIPS[0]
    for c in CLIPS:
        if c["out_in"] <= t < c["out_out"]:
            return c
        if c["out_in"] <= t:
            prev = c
    return prev


def gap(beat):
    """(t0, t1) of the silence select.json left after the clip with this beat ("gap_after")."""
    for (g0, g1, b) in GAPS:
        if b == beat:
            return g0, g1
    raise KeyError(f"no gap after {beat}: add \"gap_after\" to that clip in select.json")


def beat_start(beat):
    """output time where the first clip with this beat starts."""
    return min(c["out_in"] for c in CLIPS if c["beat"] == beat)


def beat_end(beat):
    """output time where the last clip with this beat ends."""
    return max(c["out_out"] for c in CLIPS if c["beat"] == beat)


def word_in(beat, word, n=1):
    """output time of the n-th `word` spoken inside the clips of `beat`. Unlike at(), it needs no guessed time, so
    the anchors survive any change to the cut. An exact match wins over a prefix ("là" must not land on "làm")."""
    a, b = beat_start(beat), beat_end(beat)
    key = _norm(word)
    inside = [w for w in WORDS if a - 1e-3 <= w["s"] < b]
    hits = [w["s"] for w in inside if _norm(w["w"]) == key]
    hits = hits or [w["s"] for w in inside if _norm(w["w"]).startswith(key)]
    if len(hits) < n:
        raise KeyError(f"word_in: '{word}' #{n} not in beat '{beat}' ({len(hits)} found)")
    return hits[n - 1]


def shot_at(t):
    for (a, b, s) in SHOT_OVERRIDES:
        if a <= t < b:
            return s
    return clip_at(t)["shot"]


@functools.lru_cache(maxsize=None)
def z_max(t0, t1):
    """tightest zoom used between t0 and t1 (depth words are sized for it, so a cut to a closer shot
    never blows a scene-locked word past its design size)."""
    n = max(2, int((t1 - t0) / 0.1) + 1)
    return max(SHOTS[shot_at(t0 + (t1 - t0) * i / (n - 1))]["z"] for i in range(n))


def cue(t, kind, gain=1.0, **kw):
    CUES.append((round(float(t), 3), kind, gain, kw))


def score(kind, t, **kw):
    """one event of a trailer score (kinds and options: trailer_score.py). Any event replaces the composed music."""
    SCORE.append((round(float(t), 3), kind, kw))


def ev(t0, t1):
    def deco(fn):
        EVENTS.append((t0, t1, fn))
        return fn
    return deco


# ----------------------------------------------------------------------------
# placement
# ----------------------------------------------------------------------------
def head(ctx, spk=None):
    """screen x of face, screen y of head top, screen y of face centre, layout px per source px."""
    spk = spk or ctx.spk
    fx, fy, ht = FACE[spk]
    x, y = src_to_screen(ctx.cam, fx, ht)
    _, yf = src_to_screen(ctx.cam, fx, fy)
    return x, y, yf, ctx.cam[2] * BASE


def anc(ctx, dx, dy, spk=None):
    """screen position of a point (dx, dy) source px from the speaker's face centre: scene-locked, so a
    chip beside the head follows cuts, push-ins, punches and the PiP card."""
    fx, fy, _ = FACE[spk or ctx.spk]
    return src_to_screen(ctx.cam, fx + dx, fy + dy)


def place(ctx, yt, tk, spk=None):
    """chip position per format -> (x, y, anchor). yt = (dx, dy, anchor) in source px from the face
    (space beside the speaker exists on 16:9); tk = (x, y, anchor) in screen px (on 9:16 chips stack in
    the free zone y 250-450 above the head). anchor: left | right | center."""
    if YT:
        x, y = anc(ctx, yt[0], yt[1], spk)
        return x, y, yt[2]
    return tk


def stage(h):
    """card rectangle in the stage area next to / above the PiP speaker card."""
    h = min(h, P["stage_hmax"])
    x0, x1 = P["stage_x"]
    cy = P["stage_cy"]
    return x0, cy - h / 2, x1, cy + h / 2


def panel(ctx, t, t0, t1, h, r=44, accent=None):
    """frosted diagram card in the stage area: (alpha, dy, x0, y0, x1, y1), alpha 0 when hidden."""
    x0, y0, x1, y1 = stage(h)
    v, dy = glass_panel(ctx, ctx.mid, t, t0, t1, x0, y0, x1, y1, r=r, accent=accent)
    return v, dy, x0, y0, x1, y1


def diagram(t_in, t_out):
    """register a PiP window for a diagram that lives in [t_in + 0.3, t_out]."""
    PIP.append((t_in, t_out))


def split_screen(t0, t1, top=None, bottom=None):
    """both speakers at once from t0 to t1 (output s), one per half: `top` above, `bottom` below (default the man
    "M" on top and the woman "W" below, else the first two speakers). Vertical formats only: 16:9 already shows both
    in its two-shot. The captions sit on the seam meanwhile; render.py frames each half (SPLIT_FRAME)."""
    SPLIT.append((t0, t1, top, bottom))


def split_at(t):
    """the split screen running at t, (t0, t1, top, bottom), else None. Edges snap to the nearest frame the way cuts
    do, so a split that starts on a cut starts on the cut's first frame."""
    f = round(t * FPS)
    for sp in SPLIT:
        if round(sp[0] * FPS) <= f < round(sp[1] * FPS):
            return sp
    return None


@functools.lru_cache(maxsize=None)
def glyph_top(text, kind):
    """height above the baseline of the tallest glyph (diacritics included), per 1 px of size."""
    f = font(kind, 100)
    return -min(r.top() for r in f.getBounds(f.textToGlyphs(nfc(text)))) / 100.0


def label_w(num, title):
    return 32 + text_width(num, font("black", 41)) + 21 * 2 + 2 + text_width(title, font("semi", 39), 0.4) + 32


@functools.lru_cache(maxsize=None)
def label_right(t0, t1):
    """right edge of any chapter label visible during [t0, t1], else None."""
    if not P["rail"]:
        return None
    r = [MX + label_w(n, ti) for (tc, n, ti) in LABELS if tc + 0.15 < t1 and t0 < tc + 3.2]
    return max(r) if r else None


def depth_word(ctx, t, t0, t1, text, size=280, rgb=WHITE, kind="black", enter="rise", glow=None,
               gradient=None, overlap=None, max_w=None, xoff=0.0, yoff=0.0, layer="behind", tracking=-0.025,
               stagger=0.035, alpha=1.0, fade_out=0.28, sheen=None, t_ref=None, spk=None):
    """Big word standing behind the speaker. size / max_w / offsets are screen px at the tightest shot of
    the word's life (or the shot live at t_ref); the word is locked to the scene (scales and moves with
    the camera), so cuts, punches and the PiP move it exactly like the background."""
    if not (t0 <= t <= t1):
        return None
    spk = spk or ctx.spk
    z_ref = z_max(round(max(t0, 0), 3), round(t1, 3)) if t_ref is None else SHOTS[shot_at(t_ref)]["z"]
    k = ctx.cam[2] / z_ref
    if overlap is None:
        if TK:
            overlap = 0.45 if z_ref <= 1.03 else 0.36
        else:
            overlap = 0.45 if z_ref <= 1.05 else (0.38 if z_ref <= 1.2 else 0.30)
    max_w = max_w or (W - 2 * MX)
    size_s, mw = size * k, max_w * k
    f = font(kind, size_s)
    m = f.getMetrics()
    cap_full = m.fCapHeight if m.fCapHeight > 0 else size_s * 0.7
    tw = text_width(text, f, tracking * size_s)
    fx, fy, ht = FACE[spk]
    hx, hy = src_to_screen(ctx.cam, fx, ht)
    top_k = glyph_top(text, kind)
    # the view may be shrinking into the PiP card: margins follow the view, not the frame
    rx0, ry0, rx1, ry1 = ctx.pip_rect if ctx.pip > 0 else (0, 0, W, H)
    f_ = (rx1 - rx0) / W
    # never sit on another person's head: limit the horizontal span to the speaker's side
    lo, hi = rx0 + MX * f_, rx1 - MX * f_
    eff = min(1.0, mw / tw)
    base = hy + cap_full * eff * overlap + yoff * k
    for other in FACE:
        if other == spk:
            continue
        ox0, oy0 = src_to_screen(ctx.cam, HEADBOX[other][0], HEADBOX[other][1])
        ox1, oy1 = src_to_screen(ctx.cam, HEADBOX[other][2], HEADBOX[other][3])
        if oy0 < base + size_s * eff * 0.2 and base - size_s * eff * top_k < oy1:
            if ox1 < hx:
                lo = max(lo, ox1 + 40 * k)
            elif ox0 > hx:
                hi = min(hi, ox0 - 40 * k)
    mw = min(mw, hi - lo)
    eff = min(1.0, mw / tw)
    base = hy + cap_full * eff * overlap + yoff * k
    # chapter rail: slide right of it when there is room, otherwise drop below it
    min_top = ry0 + P["top"] * (ry1 - ry0) / H
    lab = label_right(round(t0, 3), round(t1, 3)) if ctx.pip <= 0 else None
    if lab is not None and base - size_s * eff * top_k < 172:
        wv = tw * eff
        if min(max(hx + xoff * k, lo + wv / 2), hi - wv / 2) - wv / 2 < lab + 24:
            lo2 = max(lo, lab + 30)
            if hi - lo2 >= 0.72 * wv:
                lo = lo2
                mw = min(mw, hi - lo)
                eff = min(1.0, mw / tw)
                base = hy + cap_full * eff * overlap + yoff * k
            else:
                min_top = 172
    top = base - size_s * eff * top_k
    if top < min_top:
        base += min_top - top
    wv = tw * eff
    cx = min(max(hx + xoff * k, lo + wv / 2), hi - wv / 2)
    L = ctx.behind if layer == "behind" else ctx.front
    return big_text(L, t, t0, t1, text, cx, base, size=size_s, kind=kind, rgb=rgb, max_w=mw, enter=enter,
                    glow=glow, gradient=gradient, tracking=tracking, stagger=stagger, alpha=alpha,
                    fade_out=fade_out, sheen=sheen)


def badge(ctx, t, t0, t1, x, y, r0, kind, rgb):
    """round icon badge that springs in."""
    v = env(t, t0, t1, 0.001, 0.2)
    if v <= 0:
        return
    k = clamp01((t - t0) / 0.45)
    c = ctx.front.c
    r = r0 * (0.5 + 0.5 * spring(k, 6, 1.6))
    c.drawCircle(x, y, r * 1.28, fill(rgb, 70 * v, blur=24))
    c.drawCircle(x, y, r, fill(INK, 150 * v))
    c.drawCircle(x, y, r, stroke(rgb, 255 * v, width=3))
    icon(c, kind, x, y, r * 1.05, rgb, 255 * v)
    ctx.front.mark(x - 2 * r0, y - 2 * r0, x + 2 * r0, y + 2 * r0)


def arrow(c, x0, y, x1, prog, rgb, a, width=6):
    path = skia.Path()
    path.moveTo(x0, y)
    path.lineTo(x1, y)
    draw_on_path(c, path, ease_out_cubic(prog), stroke(rgb, a, width=width))
    if prog >= 1:
        c.drawLine(x1, y, x1 - 24, y - 18, stroke(rgb, a, width=width))
        c.drawLine(x1, y, x1 - 24, y + 18, stroke(rgb, a, width=width))


def takeaway(ctx, t, t0, line1, line2, chip_text=None, kick="TÓM LẠI"):
    """end card: blurs the frame, shows the one line to remember. On YouTube the right half stays calm
    for end-screen elements."""
    v = env(t, t0, TOTAL + 1, 0.35, 0.1)
    if v <= 0:
        return
    ctx.end = clamp01((t - t0) / 0.6)
    k = clamp01((t - t0 - 0.1) / 0.5)
    e = ease_out_cubic(k)
    k2 = clamp01((t - t0 - 0.55) / 0.5)

    def fit(text, kind, size):
        # a long sentence must not run off the frame, or into the free half of the YouTube end screen
        room = 1000 if YT else W - 2 * MX
        return font(kind, min(size, size * room / max(1.0, text_width(text, font(kind, size)))))

    if YT:
        x = 150
        kicker(ctx.front, t, t0 + 0.05, TOTAL + 1, kick, x, 352, size=34, rgb=AMBER, kind="bold", align="left")
        draw_text(ctx.front, line1, fit(line1, "black", 112), x, 492 + (1 - e) * 30, rgb=WHITE, a=255 * v * k, align="left",
                  shadow=14, shadow_a=170)
        draw_text(ctx.front, line2, fit(line2, "serif_ib", 156), x - 6, 662 + (1 - e) * 30, rgb=AMBER, a=255 * v * k,
                  align="left", shadow=14, shadow_a=170, glow=(255, 170, 60), glow_a=120)
        if chip_text:
            chip(ctx.front, t, t0 + 0.55, TOTAL + 1, x, 800, chip_text, "check", style="glow", size=40, accent=MINT,
                 alpha=k2, anchor="left")
    else:
        y = 820
        draw_text(ctx.front, line1, fit(line1, "black", 92), W / 2, y - 60 + (1 - e) * 30, rgb=WHITE, a=255 * v * k,
                  shadow=14, shadow_a=170)
        draw_text(ctx.front, line2, fit(line2, "serif_ib", 120), W / 2, y + 80 + (1 - e) * 30, rgb=AMBER, a=255 * v * k,
                  shadow=14, shadow_a=170, glow=(255, 170, 60), glow_a=120)
        if chip_text:
            chip(ctx.front, t, t0 + 0.55, TOTAL + 1, W / 2, y + 250, chip_text, "check", style="glow", size=40,
                 accent=MINT, alpha=k2)


# ----------------------------------------------------------------------------
# captions: word-by-word, keyword styling, no line break inside a compound word
# ----------------------------------------------------------------------------
COMPOUNDS = set("""
tự làm|tự quyết|tất cả|mọi thứ|đáng sợ|thực ra|an toàn|rất nhiều|nhiều người|chia sẻ|một chút|cái gì|
viết tắt|tiếng anh|biết rồi|nghĩa là|đơn giản|hơn thế|quan trọng|tài liệu|dữ liệu|trí nhớ|tức là|lịch sử|
bình thường|không biết|sửa đổi|những cái|cái lần|thứ hai|khác với|không chỉ|một cái|đối tượng|khách hàng|
thế thì|có thể|rẽ nhánh|nôm na|một cách|vì sao|làm việc|ủy thác|quyết định|ra quyết|đa số|các việc|vậy thì|
giao cho|một người|muốn biết|nhỡ may|làm sai|làm sao|quay về|hiện trạng|vì thế|cho nên|chuyên nghiệp|kết nối|
vẫn thường|quay trở|trở lại|phiên bản|bản trước|thông thường|không có|giám sát|nhân viên|đang làm|làm gì|
hãy nên|kết quả|công việc|hiện nay|phổ biến|rất là|là dễ|lưu trữ|kế hoạch|cũng được|bản thân|nó có|có các|
các cái|làm một|của em|là gì|nó biết|nó là|là một|ở điểm|điểm là|thì rất|rất đáng|nó rất|rất an|khá an|là cái|
thì biết""".replace(chr(10), "").split("|"))
LINES = []


def _clean(w):
    return re.sub(r"[.,!…]+$", "", w).strip()


def _split_chunk(ch):
    """DP split of a run of words into caption lines, sized per format."""
    n = len(ch)
    INF = 1e9
    best = [INF] * (n + 1)
    prev = [0] * (n + 1)
    best[0] = 0.0
    tgt, mx = P["cap_target"], P["cap_max"]
    for j in range(1, n + 1):
        for i in range(max(0, j - 7), j):
            words = ch[i:j]
            chars = sum(len(x["t"]) for x in words) + (len(words) - 1)
            if chars > mx and len(words) > 1:
                continue
            c = (0.012 if YT else 0.02) * (chars - tgt) ** 2
            if len(words) == 1:
                c += 2.5 if len(words[0]["t"]) < 6 else 1.0
            if j < n:
                a, b = ch[j - 1]["t"].lower().strip("?,."), ch[j]["t"].lower().strip("?,.")
                if f"{a} {b}" in COMPOUNDS:
                    c += 9.0
                if ch[j]["s"] - ch[j - 1]["e"] > 0.22:
                    c -= 2.0
                if ch[j - 1]["comma"]:
                    c -= 3.0
            if best[i] + c < best[j]:
                best[j] = best[i] + c
                prev[j] = i
    cuts = []
    j = n
    while j > 0:
        cuts.append((prev[j], j))
        j = prev[j]
    return [ch[a:b] for a, b in reversed(cuts)]


def build_lines():
    words = []
    for w in WORDS:
        txt = _clean(w["w"])
        if not txt:
            continue
        raw = w["w"].strip()
        words.append({"t": txt, "s": w["s"], "e": w["e"], "spk": w["spk"],
                      "end_punct": bool(re.search(r"[.?!]$", raw)), "comma": raw.endswith(",")})
    keep = set(KEEP_CASE.values()) | NO_BREAK
    chunks, cur = [], []
    for w in words:
        cap_start = w["t"][:1].isupper() and w["t"] not in keep
        if cur and (cur[-1]["end_punct"] or w["s"] - cur[-1]["e"] > 0.6 or w["spk"] != cur[-1]["spk"] or cap_start
                    or split_at(w["s"]) != split_at(cur[-1]["s"])):
            chunks.append(cur)
            cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    out = []
    for ch in chunks:
        out.extend(_split_chunk(ch))
    for ln in out:
        low = [_norm(x["t"]) for x in ln]
        raw = [x["t"].lower() for x in ln]
        style = [None] * len(ln)
        for n in (3, 2, 1):
            for i in range(len(ln) - n + 1):
                ph = " ".join(raw[i:i + n]).strip("?")
                if ph in KEYS and all(s is None for s in style[i:i + n]):
                    for j in range(i, i + n):
                        style[j] = KEYS[ph]
        for x, st, lw in zip(ln, style, low):
            x["style"] = st
            disp = x["t"]
            if lw in KEEP_CASE:
                disp = KEEP_CASE[lw] + ("?" if disp.endswith("?") else "")
            x["disp"] = disp
    # a split screen moves the captions to the seam, so no line is shown across a split's edge: it would jump.
    # Each edge sits half a frame before the frame where split_at() changes.
    edges = sorted({(round(e * FPS) - 0.5) / FPS for sp in SPLIT for e in sp[:2]})
    for i, ln in enumerate(out):
        s0 = ln[0]["s"]
        nxt = out[i + 1][0]["s"] if i + 1 < len(out) else 1e9
        ln_start, ln_end, cut = s0 - 0.06, min(nxt - 0.02, ln[-1]["e"] + 0.7), False
        for e in edges:
            if ln_start < e <= s0:
                ln_start = e
            if s0 < e <= ln_end:
                ln_end, cut = e, True       # leaves with the picture's cut instead of fading out before it
        for x in ln:
            x["line_start"], x["line_end"], x["line_cut"] = ln_start, ln_end, cut
    return out


def draw_captions(ctx, t):
    if t > DUR + 0.2:
        return
    ln = None
    for L in LINES:
        if L[0]["line_start"] <= t <= L[0]["line_end"]:
            ln = L
    if ln is None:
        return
    layer = ctx.ui
    y = ctx.cap_y
    size = P["cap_size"]
    items = []
    total = 0
    for x in ln:
        kind, rgb, mult = x["style"] if x["style"] else ("bold", WHITE, 1.0)
        f = font(kind, size * mult)
        w = text_width(x["disp"], f)
        items.append((x, f, rgb, w))
        total += w
    sp = size * 0.27
    total += sp * (len(items) - 1)
    sc = min(1.0, P["cap_maxw"] / total) if total > 0 else 1.0
    xx = W / 2 - total * sc / 2
    end_v = 1.0 if ln[0]["line_cut"] else clamp01((ln[0]["line_end"] - t) / 0.1)
    for (x, f, rgb, w) in items:
        k = clamp01((t - (x["s"] - 0.05)) / 0.16)
        if k <= 0:
            xx += (w + sp) * sc
            continue
        e = ease_out_cubic(k)
        active = x["s"] - 0.05 <= t <= x["e"] + 0.05
        lift = 1.0 + (0.04 if active and x["style"] is None else 0.0)
        draw_text(layer, x["disp"], f, xx + w * sc / 2, y + (1 - e) * pick(18, 22), rgb=rgb, a=255 * e * end_v,
                  align="center", shadow=pick(8, 9), shadow_a=200, scale=sc * lift)
        xx += (w + sp) * sc
    ctx.caption_box = True


# ----------------------------------------------------------------------------
# chapter rail (YouTube, top-left) — mirrors the description chapters
# ----------------------------------------------------------------------------
def chapter_rail(ctx, t):
    for (tc, num, title) in LABELS:
        t0, t1 = tc + 0.25, tc + 3.1
        v = env(t, t0, t1, 0.001, 0.3)
        if v <= 0:
            continue
        L = ctx.ui
        c = L.c
        k = ease_out_cubic(clamp01((t - t0) / 0.5))
        fn, ft = font("black", 41), font("semi", 39)
        wn = text_width(num, fn)
        h, padx, gap = 78, 32, 21
        w = label_w(num, title)
        x0, y0 = MX - (1 - k) * 34, 70
        a = 255 * v * clamp01((t - t0) / 0.15)
        c.drawRRect(rrect(x0, y0, x0 + w, y0 + h, h / 2), fill(INK, 165 * v))
        c.drawRRect(rrect(x0, y0, x0 + w, y0 + h, h / 2), stroke(WHITE, 46 * v, width=1.5))
        draw_text(L, num, fn, x0 + padx, y0 + h / 2 + 14, rgb=AMBER, a=a, align="left")
        bx = x0 + padx + wn + gap
        c.drawLine(bx, y0 + 20, bx, y0 + h - 20, stroke(WHITE, 90 * v, width=2))
        draw_text(L, title, ft, bx + 2 + gap, y0 + h / 2 + 13, rgb=WHITE, a=a, align="left", tracking=0.4)
        p = ease_in_out_cubic(clamp01((t - t0 - 0.2) / (t1 - t0 - 0.5)))
        c.drawLine(x0 + h / 2, y0 + h + 12, x0 + h / 2 + (w - h) * p, y0 + h + 12, stroke(AMBER, 210 * v, width=3))
        L.mark(x0, y0, x0 + w, y0 + h + 24)


# ----------------------------------------------------------------------------
# frame
# ----------------------------------------------------------------------------
def draw(ctx, t):
    ctx.cap_y = P["split_cap_y"] if split_at(t) else CAP_Y
    for fn in PRE:
        fn(ctx, t)
    for (t0, t1, fn) in EVENTS:
        if t0 - 0.05 <= t <= t1 + 0.05:
            fn(ctx, t)
    if ctx.pip > 0.02:
        x0, y0, x1, y1 = ctx.pip_rect
        ctx.front.c.drawRRect(rrect(x0, y0, x1, y1, 28 * ctx.pip), stroke(WHITE, 64 * ctx.pip, width=2))
        ctx.front.mark(x0, y0, x1, y1, pad=6)
    if P["rail"]:
        chapter_rail(ctx, t)
    if not any(off(t) for off in CAPTION_OFF):
        draw_captions(ctx, t)
    for tl in LEAKS:
        if tl - 0.05 <= t <= tl + 0.75:
            ctx.leak = (clamp01((t - tl) / 0.7), 0.42)
    for fn in POST:
        fn(ctx, t)


# ----------------------------------------------------------------------------
# music plan: bars follow the edit, the first downbeat lands on MUSIC["drop"]
# ----------------------------------------------------------------------------
def music_plan():
    """MUSIC["sections"]: [(t_start, style, progression), ...] in order. Styles: intro build light groove
    lift break outro; progressions: main calm tense."""
    bpm = float(MUSIC.get("bpm", 96.0))
    bar = 4 * 60.0 / bpm
    drop = MUSIC["drop"] if MUSIC["drop"] is not None else 0.0
    secs = MUSIC["sections"] or [(0.0, "light", "main")]
    intro_bars = 2 if MUSIC["drop"] is not None else 0
    bar0 = drop - intro_bars * bar

    def bar_of(t):
        return int(round((t - bar0) / bar))

    b_end = bar_of(TOTAL) + 2
    sections = [[0, intro_bars, "intro", "tense"]] if intro_bars else []
    starts = [max(intro_bars, bar_of(t)) for (t, _s, _p) in secs]
    for i, (_t, style, prog) in enumerate(secs):
        a = starts[i]
        b = starts[i + 1] if i + 1 < len(secs) else b_end
        if b > a:
            sections.append([a, b, style, prog])
    return {"duration": round(TOTAL, 3), "bar0": round(bar0, 4), "tail": MUSIC.get("tail") or (3.2 if YT else 2.4),
            "sections": sections, "stops": list(MUSIC["stops"]), "bpm": bpm, "transpose": int(MUSIC.get("transpose", 0))}


def fmt_ts(t):
    t = int(t)
    return f"{t // 60}:{t % 60:02d}"


def _auto_cues():
    for (tc, _n, _t) in (LABELS if P["rail"] else []):
        cue(tc + 0.25, "pop", 0.35, f0=440, f1=820)
    for (a, b) in PIP:
        cue(a + 0.22, "whoosh", 0.42, length=0.5, direction=1)
        cue(b + 0.22, "whoosh", 0.36, length=0.5, direction=-1)
    names = list(FACE)
    for i in range(1, len(CLIPS)):
        if CLIPS[i]["spk"] != CLIPS[i - 1]["spk"]:
            cue(CLIPS[i]["out_in"] + 0.03, "whoosh", 0.6, length=0.42,
                direction=-1 if names.index(CLIPS[i]["spk"]) % 2 else 1)


def _resolve_splits():
    """name each split's top and bottom speaker; 16:9 keeps its two-shot, so it drops the splits."""
    if not TK:
        SPLIT.clear()
        return
    names = list(FACE)
    if SPLIT and len(names) < 2:
        raise SystemExit("split_screen() needs two speakers in project.json")
    default = ("M", "W") if {"M", "W"} <= set(names) else tuple(names[:2])
    for i, sp in enumerate(SPLIT):
        t0, t1, *rest = sp
        top, bottom = (list(rest) + [None, None])[:2]
        # with one name given, the other half gets the other speaker
        top = top or next(n for n in default if n != bottom)
        bottom = bottom or next(n for n in default + tuple(names) if n != top)
        if top not in names or bottom not in names or top == bottom:
            raise SystemExit(f"split_screen({t0}, {t1}): top {top!r} and bottom {bottom!r} must be two of {names}")
        SPLIT[i] = (t0, t1, top, bottom)
    SPLIT.sort()


def load_design():
    """import the project's design.py (it registers everything above), then build what depends on it."""
    global LINES
    sys.path.insert(0, PROJECT)
    import design  # noqa: F401  (project file)
    PIP.sort()
    _resolve_splits()
    _auto_cues()
    LINES = build_lines()
