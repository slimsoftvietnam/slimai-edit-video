"""Hand-set caption stacks in the reference's style (rawstyle.py has the treatments and the drawing).

The reference's stacks are designed phrase by phrase, so each phrase of this video is set by hand. A group is a list
of rows (text, role[, opts]): role "s" = small white words, a rawstyle.TREAT name = the key word in that treatment,
"k2" = a second big word in white heavy lowercase under the key ("character" / "homes"). The rows' words are matched
in order to the spoken words (story.WORDS), so each word appears as it is said and a recut keeps the timing. The text
shown is the row's own (spelling, case and dropped fillers are the design's choice).

    import rawgroups as G
    G.group([("đừng tìm cách", "s"), ("tiết kiệm token", "white", {"strike": t}), ("nữa", "s")])
    G.event(hidden=lambda t: ...)

Layout: the stack's last big row tucks behind the top of the head (the matte hides its lower edge where the head
is); a last small row sits just above the hair; small rows before the first big row hang from its left end, small
rows after the last one from its right end, as in the reference. Big rows are drawn behind the speaker, small rows
in front of him.
"""
import skia

import engine as E
import rawstyle as RS
import story as S
from engine import clamp01, ease_out_back, ease_out_cubic, font, nfc

W = RS.W
GROUPS = []
SMALL, BIG = 62, 196


def _tok(s):
    return [x for x in nfc(s).split() if S._norm(x)]


_TOKENS = []


def tokens():
    """the spoken words split into single tokens (a fixed word such as "tại Anthropic." gives two), with times"""
    if not _TOKENS:
        for w in S.WORDS:
            parts = [p for p in nfc(w["w"]).split() if S._norm(p)]
            for k, p in enumerate(parts):
                _TOKENS.append((S._norm(p), w["s"] + 0.08 * k))
    return _TOKENS


def _match_times(rows, cursor):
    """the spoken time of every token of every row, matched exactly and in order from token `cursor`;
    returns (times, cursor)"""
    toks = tokens()
    out = []
    i = cursor
    last = toks[cursor][1] if cursor < len(toks) else 0.0
    for row in rows:
        ts = []
        if len(row) > 2 and row[2].get("free"):        # words that are shown, not spoken: no matching
            ts = [last + 0.12 * (k + 1) for k in range(len(_tok(row[0])))]
            out.append(ts)
            continue
        for tok in _tok(row[0]):
            nt = S._norm(tok)
            found = next((j for j in range(i, min(len(toks), i + 14)) if toks[j][0] == nt), None)
            if found is None:
                last += 0.12
                ts.append(last)
                continue
            last = toks[found][1]
            ts.append(last)
            i = found + 1
        out.append(ts)
    return out, i


def group(rows, t_out=None, near=None, tuck=None, base=None, scale=None, front=False, t_in=None):
    """add one stack. `near` = output time to start matching from (default: after the previous group)."""
    cursor = GROUPS[-1]["cursor"] if GROUPS else 0
    if near is not None:
        cursor = min(range(len(tokens())), key=lambda j: abs(tokens()[j][1] - near))
    times, cur = _match_times(rows, cursor)
    g = dict(rows=[dict(text=r[0], role=r[1], times=ts, opts=(r[2] if len(r) > 2 else {}))
                   for r, ts in zip(rows, times)],
             t_in=(min(ts[0] for ts in times if ts) - 0.06) if t_in is None else t_in, t_out=t_out, cursor=cur,
             tuck=tuck, base=base, scale=scale, front=front)
    if GROUPS and GROUPS[-1]["t_out"] is None:
        GROUPS[-1]["t_out"] = g["t_in"] - 0.02
    GROUPS.append(g)
    return g


def _kind_font(role):
    if role == "s":
        return "semi"
    if role == "k2":
        return "black"
    return RS.TREAT[role]["kind"]


def _row_text(r):
    if r["role"] in ("s", "k2"):
        return nfc(r["text"])
    return RS.cased(r["text"], RS.TREAT[r["role"]]["case"])


def _place_x(rows, cx):
    bigs = [i for i, ro in enumerate(rows) if ro["kind"] != "s"]
    for i, ro in enumerate(rows):
        if ro["kind"] != "s" or not bigs:
            ro["x"] = cx - ro["w"] / 2
            continue
        ref = rows[bigs[0]] if i < bigs[0] else (rows[bigs[-1]] if i > bigs[-1] else None)
        if ref is None or ro["w"] > ref["w"] * 0.92:
            ro["x"] = cx - ro["w"] / 2
        elif i < bigs[0]:
            ro["x"] = cx - ref["w"] / 2 + ref["w"] * 0.04
        else:
            ro["x"] = cx + ref["w"] / 2 - ref["w"] * 0.04 - ro["w"]


def layout(g, hy, head_x=None, max_w=940, min_top=175, tuck=0.30, cx=W / 2):
    """rows with font, text, width, x and baseline y (screen px). head_x = (x0, x1) of the head on screen: a short
    last small row that clears it sits beside the top of the head instead of above it."""
    rows = []
    for scale in ((1.0, 0.9, 0.8, 0.7, 0.62) if g.get("scale") is None else (g["scale"],)):
        rows = []
        for r in g["rows"]:
            kind = "s" if r["role"] == "s" else ("k2" if r["role"] == "k2" else "k")
            base = r["opts"].get("size", SMALL if kind == "s" else (BIG * 0.78 if kind == "k2" else BIG))
            fk = _kind_font(r["role"])
            f = font(fk, base * scale)
            txt = _row_text(r)
            if kind == "s":
                wds = _tok(txt)
                w = sum(f.measureText(x) for x in wds) + f.getSize() * 0.26 * (len(wds) - 1)
            else:
                w = f.measureText(txt)
            if w > max_w:
                f = font(fk, f.getSize() * max_w / w)
                if kind == "s":
                    w = sum(f.measureText(x) for x in _tok(txt)) + f.getSize() * 0.26 * (len(_tok(txt)) - 1)
                else:
                    w = f.measureText(txt)
            rows.append(dict(r=r, f=f, kind=kind, txt=txt, w=w, top=RS.top_of(txt, f), size=f.getSize()))
        main = [ro for ro in rows if not ro["r"]["opts"].get("inline")]
        for i, ro in enumerate(main):
            if i == 0:
                ro["y"] = 0.0
                continue
            pr = main[i - 1]
            if pr["kind"] == "s" and ro["kind"] == "s":
                gap = pr["size"] * 0.44 + ro["top"]
            elif pr["kind"] == "s":
                gap = pr["size"] * 0.22 + ro["top"] * 0.96
            elif ro["kind"] == "s":
                gap = pr["size"] * 0.16 + ro["top"] * 1.25
            else:
                gap = ro["top"] * 0.93                    # two big rows nearly touch, as in the reference
            ro["y"] = pr["y"] + gap
        _place_x(main, cx)
        last = main[-1]
        if g.get("base") is not None:
            anchor = g["base"]                             # a compact stack at a fixed height (under a window)
        elif last["kind"] != "s":
            anchor = hy + tuck * last["size"]
        elif head_x is not None and (last["x"] > head_x[1] + 24 or last["x"] + last["w"] < head_x[0] - 24):
            anchor = hy + last["size"] * 0.7               # beside the head, clear of it
        else:
            anchor = hy - 26                               # above the hair
        shift = anchor - last["y"]
        for ro in main:
            ro["y"] += shift
        # an inline row ("about" under the end of "thinking"): small, under the right end of the big row before it
        for i, ro in enumerate(rows):
            if not ro["r"]["opts"].get("inline"):
                continue
            pr = next((rows[j] for j in range(i - 1, -1, -1) if not rows[j]["r"]["opts"].get("inline")), rows[0])
            ro["y"] = pr["y"] + ro["size"] * 0.98
            ro["x"] = (pr["x"] + pr["w"] * 0.985 - ro["w"]) if ro["w"] <= pr["w"] * 0.9 else cx - ro["w"] / 2
        if main[0]["y"] - main[0]["top"] >= min_top:
            break
    return rows


def draw(ctx, t, g, hy, head_x=None, a=255.0):
    t_out = g["t_out"] if g["t_out"] is not None else S.DUR + 0.25
    if t < g["t_in"] or t > t_out:
        return
    v = clamp01((t_out - t) / 0.1)
    if v <= 0:
        return
    a *= v
    for ro in layout(g, hy, head_x, **({"tuck": g["tuck"]} if g.get("tuck") is not None else {})):
        r = ro["r"]
        if ro["kind"] == "s":
            L = ctx.front
            f = ro["f"]
            sp = f.getSize() * 0.26
            x = ro["x"]
            times = r["times"] or [g["t_in"]]
            for n, tok in enumerate(_tok(ro["txt"])):
                ts = times[min(n, len(times) - 1)]
                k = clamp01((t - (ts - 0.05)) / 0.13)
                if k > 0:
                    RS.draw_word(L.c, tok, f, x, ro["y"] + (1 - ease_out_cubic(k)) * 14, a * k, RS.WHITE, shadow=0.75)
                x += f.measureText(tok) + sp
            L.mark(ro["x"] - 20, ro["y"] - ro["top"] - 30, ro["x"] + ro["w"] + 20, ro["y"] + ro["size"] * 0.4)
            continue
        t0 = r["opts"].get("t", r["times"][0] if r["times"] else g["t_in"])
        k0 = clamp01((t - (t0 - 0.07)) / 0.09)
        if k0 <= 0:
            continue
        L = ctx.front if (r["opts"].get("front") or g.get("front")) else ctx.behind
        c = L.c
        spec = RS.TREAT.get(r["role"], dict(rgb=RS.WHITE))
        cxr, cyr = ro["x"] + ro["w"] / 2, ro["y"] - ro["top"] * 0.45
        pop = 1.0 + 0.25 * (1 - ease_out_back(clamp01((t - (t0 - 0.07)) / 0.24)))
        c.save()
        c.translate(cxr, cyr)
        c.scale(pop, pop)
        c.translate(-cxr, -cyr)
        txt, x_ = ro["txt"], ro["x"]
        cnt = r["opts"].get("count")
        if cnt:                                     # a number counting up, centred where the final one stands
            n_end, c0, c1, suffix = cnt
            kc = ease_out_cubic(clamp01((t - c0) / max(0.05, c1 - c0)))
            n = int(round(n_end * kc / 100.0) * 100) if kc < 1 else n_end
            txt = f"{n:,}".replace(",", ".") + (suffix if kc >= 1 else "")
            x_ = ro["x"] + (ro["w"] - ro["f"].measureText(txt)) / 2
        RS.draw_word(c, txt, ro["f"], x_, ro["y"], a * k0, spec.get("rgb", RS.WHITE), spec.get("grad"),
                     spec.get("edge"), shadow=0.62, edge_w=spec.get("edge_w", 0.04))
        st = r["opts"].get("strike")
        if st is not None and t >= st:
            ks = ease_out_cubic(clamp01((t - st) / 0.2))
            ym = ro["y"] - ro["top"] * 0.40
            x0s, x1s = ro["x"] - 20, ro["x"] + ro["w"] + 20
            p = skia.Paint(AntiAlias=True, Color=RS.c4(r["opts"].get("strike_rgb", RS.RED), a * k0))
            p.setStrokeWidth(max(9.0, ro["size"] * 0.08))
            p.setStrokeCap(skia.Paint.kRound_Cap)
            c.drawLine(x0s, ym + 8, x0s + (x1s - x0s) * ks, ym + 8 - 16 * ks, p)
        c.restore()
        L.mark(ro["x"] - 70, ro["y"] - ro["top"] * 1.35 - 30, ro["x"] + ro["w"] + 70, ro["y"] + ro["size"] * 0.4)


def event(hidden=lambda t: False, end=None):
    """one event that draws the active group"""
    @S.ev(0.0, end if end is not None else S.DUR + 0.3)
    def _groups(ctx, t):
        if hidden(t):
            return
        for g in GROUPS:
            t_out = g["t_out"] if g["t_out"] is not None else S.DUR + 0.25
            if g["t_in"] <= t <= t_out:
                spk = ctx.spk
                hx, hy = RS.head_top(ctx, spk)
                hb = E.HEADBOX[spk]
                bx0, _y0 = E.src_to_screen(ctx.cam, hb[0] - 12, 0)
                bx1, _y1 = E.src_to_screen(ctx.cam, hb[2] + 12, 0)
                draw(ctx, t, g, hy, (bx0, bx1))


# (img8457: the head's edges come from engine.HEADBOX of the current speaker)
