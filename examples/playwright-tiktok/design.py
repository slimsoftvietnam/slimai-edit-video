"""Tập 16 · Playwright (IMG_8457): the motion style's worked example (references/motion.md), an 89 s TikTok cut of a
6.6-minute talk between two people (she asks, he answers), with the raw.to.reel captions and the licensed track of
tập 14-15. Approved, then put in the skill as the style "Motion viral (TikTok)" (2026-11-26).

The music is "Trap Banger" by alex-morgan (Pixabay 591329, Pixabay Content License; its page marks it Content ID
registered and AI generated: fine on TikTok, a claim risk on YouTube). It is not in the skill: download it from its
Pixabay page into a folder of its own, decode it to music_work/trapbanger.wav at 48 kHz, and the add_track() line
below finds it.

The user, 2026-11-25: "2s đầu bằng mọi cách phải giữ chân được user… và vượt 5s thì video sẽ viral > hãy dùng hiệu
ứng đẹp, mới lạ và viral nhất bạn biết trong các video motion, giữ chân user đến giây cuối, hãy tự đề xuất những gì bạn
thấy hiệu quả và hay nhất".

What this edit proposes (all new for the series, fx.py and ui.py):
- the motif: a ghost cursor. A mouse pointer moves, clicks and types on its own through the whole video, because the
  topic is an AI that drives a browser. It presses the title on the first frame, opens a browser, fills a login form
  step by step, re-runs it at speed, sends a chat message, types the comment for the viewer;
- the first frame: the speaker cut out like a sticker on a blue sunburst, a 3D title "AI TỰ ĐIỀU KHIỂN MÁY TÍNH", the
  cursor already there; boom, crash and the track's drop on frame 0; her voice says the topic in the first 2.2 s;
- 3-6 s: "tự mở web, tự bấm, tự gõ" happen on screen as she says them (a window opens, a button is pressed, a field
  types itself); the open question at 8 s;
- the reveal: the frame goes black and the letters PLAY WRIGHT are windows onto him; on the word "Playwright" the
  camera flies through a letter and the music drops;
- an early promise ("cuối video: cách nhận skill điều khiển Zalo"), a thin story bar, a dictionary card, the 4-step script
  with a login form, the x-ray (the page turns into HTML as a scan line passes), a chat window, a counter to 20;
- the call to comment where the wish is strongest (right after "gửi tin nhắn cho 20 người… tiết kiệm token"), typed by
  the cursor, then his laugh "cái chữ đó rất khó viết đúng" with typos on screen, and an end card whose last move
  (the cursor presses, the blue comes back) leads into the first frame again for the loop.
"""
import math
import os

import skia

from story import *
from trailer import *

import engine as E
import story as S
from engine import clamp01, ease_in_cubic, ease_out_back, ease_out_cubic, font, spring
import rawstyle as RS
import rawgroups as G
import fx as FX
import ui as UI
import modern_score  # noqa: F401  (registers hit, subdrop, stutter…)
import modern_sfx as MS
import track_music as TM

UI.RIPPLE = RS.AQUA                            # the cursor's click ripple in the captions' aqua
TM.add_track("banger", "music_work/trapbanger.wav", bar0=2.282, bpm=96.69)    # first downbeat (s), tempo: music_analyse.py

PROJ = os.path.dirname(os.path.abspath(__file__))
W2 = W / 2
DURATION = S.DUR
YELLOW = (255, 226, 60)
DEEP = (20, 52, 190)                        # the backdrop blue
NAVY = (10, 22, 90)

for name_, beat_, word_, *n_ in [
        ("c_ai", "cold", "ai"), ("c_dieu", "cold", "điều"), ("c_may", "cold", "máy"),
        ("w_tu", "web", "tự"), ("w_mo", "web", "mở"), ("w_bam", "web", "bấm"), ("w_go", "web", "gõ"),
        ("a_lam", "ask", "làm"),
        ("r_ai", "reveal", "ai"), ("r_pw", "reveal", "playwright"),
        ("h_thao", "human", "thao"), ("h_nguoi", "human", "người"),
        ("m_pw", "mean", "playwright"), ("m_kich", "mean", "kịch"), ("m_nha", "mean", "nhà"),
        ("s_kich", "script", "kịch"), ("s_dang", "script", "đăng"),
        ("s1", "step1", "1"), ("s1_mo", "step1", "mở"), ("s2", "step2", "2"), ("s2_dien", "step2", "điền"),
        ("s3", "step3", "3"), ("s3_nhap", "step3", "nhập"), ("s4", "step4", "4"), ("s4_an", "step4", "ấn"),
        ("s4_login", "step4", "login"),
        ("rr_run", "rerun", "run"), ("rr_xong", "rerun", "xong"),
        ("e_nhin", "see", "nhìn"), ("e_sao", "see", "sao"), ("e_bam", "see", "bấm"),
        ("k_chup", "code", "chụp"), ("k_nut", "code", "nút"), ("k_doc", "code", "đọc"), ("k_ma", "code", "mã"),
        ("n_doc", "nolook", "đọc"), ("n_khong", "nolook", "không"),
        ("z_nhan", "zalo", "nhắn"), ("z_zalo", "zalo", "zalo"), ("z_dang", "zalo", "đăng"), ("z_zalo2", "zalo", "zalo", 2),
        ("z_tim", "zalo", "tìm"), ("z_abc", "zalo", "abc"), ("z_nhan2", "zalo", "nhắn", 2), ("z_pw", "zalo", "playwright"),
        ("f_dau", "first", "đầu"), ("f_ai", "first", "ai"),
        ("b_sau", "brain", "sau"), ("b_tu", "brain", "tự"), ("b_khong", "brain", "không"), ("b_bo", "brain", "bộ"),
        ("b_nghi", "brain", "nghĩ"),
        ("t_20", "twenty", "20"), ("t_20b", "twenty", "20", 2),
        ("v_pw", "save", "playwright"), ("v_tiet", "save", "tiết"),
        ("q_tai", "cta", "tải"), ("q_skill", "cta", "skill"), ("q_pw", "cta", "playwright"), ("q_zalo", "cta", "zalo"),
        ("q_comment", "cta", "comment"), ("q_pw2", "cta", "playwright", 2), ("q_nha", "cta", "nhá"),
        ("g_chu", "sting", "chữ"), ("g_kho", "sting", "khó"), ("g_viet", "sting", "viết")]:
    A[name_] = word_in(beat_, word_, *n_)

S.NO_BREAK.update({"AI", "Playwright", "Zalo", "ABC"})
S.CAPTION_OFF.append(lambda t: True)       # the stacks replace the caption bar
RS.OUTLINE = ((8, 12, 26), 0.055, 0.92)     # pale sky behind the words here: every word gets a dark rim
IN = {"inline": True}
CAP_W, CAP_M = 800.0, 884.0                 # baselines of the compact stacks under a window (her / his head top)
E.SHOTS["W_wide"] = dict(spk="W", z=1.0, cx=float(os.environ.get("W_CX", 700)), cy=540.0)   # his knee stays out of her frame


def cap(rows, base, **kw):
    """a compact stack in front, at a fixed height (under a window); rows as in G.group"""
    out = []
    for r in rows:
        o = dict(r[2]) if len(r) > 2 else {}
        o.setdefault("size", 44 if r[1] == "s" else (84 if r[1] == "k2" else 100))
        out.append((r[0], r[1], o))
    return G.group(out, base=base, scale=1.0, front=True, **kw)


def tp(t, t0, t1):
    return clamp01((t - t0) / max(0.01, t1 - t0))


def kwin(t, t_in, t_out, d_in=0.32, d_out=0.16):
    """(pop progress, alpha) of a window that lives from t_in to t_out"""
    k = clamp01((t - t_in) / d_in)
    return k, 255 * min(1.0, k * 2.5) * clamp01((t_out - t) / d_out)


def chest(ctx):
    hx, hy = RS.head_top(ctx, ctx.spk)
    return W2, hy + 330


# ============================================================================
# 0-2.9 s  THE HOOK: sticker cut-out on a blue sunburst, a 3D title, the cursor presses each word as she says it
# ============================================================================
T_COLD = beat_end("cold")
PUNCHES.append((0.0, 0.06, 0.05, 0.4, 0.8))
TITLE = [("AI", 310, 512, YELLOW), ("TỰ ĐIỀU KHIỂN", 118, 646, RS.WHITE), ("MÁY TÍNH", 176, 806, YELLOW)]
T_CLICK = [A["c_ai"] + 0.16, A["c_dieu"] + 0.02, A["c_may"] + 0.04]
CUR_COLD = UI.Cursor([(0.0, 905, 600), (T_CLICK[0], 640, 430), (T_CLICK[1], 800, 640), (T_CLICK[2], 760, 770),
                      (T_COLD - 0.02, 540, 470)], clicks=T_CLICK, move=0.3, scale=4.6, t_in=-1.0, t_out=T_COLD + 0.5)


@ev(0.0, T_COLD + 0.35)
def cold_open(ctx, t):
    out = ease_in_cubic(tp(t, T_COLD - 0.22, T_COLD + 0.12))          # the backdrop closes like an iris on the cursor
    if out < 1:
        cxp, cyp = CUR_COLD.pos(t)
        FX.backdrop(ctx, t, a=1.0, rgb=DEEP, cx=W2, cy=1010,
                    reveal=None if out <= 0 else (cxp, cyp, 2300 * (1 - out)))
        c = ctx.behind.c
        c.save()
        if out > 0:
            p = skia.Path()
            p.addCircle(cxp, cyp, max(1.0, 2300 * (1 - out)))
            c.clipPath(p, skia.ClipOp.kIntersect, True)
        for i, (txt, size, y, rgb) in enumerate(TITLE):
            f = font("black", size)
            w = f.measureText(txt)
            k_in = ease_out_back(clamp01((t + 0.04) / 0.2))          # all three rows are on the first frame
            pulse = 0.0
            if t >= T_CLICK[i]:
                pulse = 0.13 * math.exp(-(t - T_CLICK[i]) / 0.16)
            sc = (0.86 + 0.14 * k_in) * (1 + pulse)
            c.save()
            c.translate(W2, y - size * 0.36)
            c.scale(sc, sc)
            c.translate(-W2, -(y - size * 0.36))
            on = t >= T_CLICK[i]
            face = rgb if (on or i == 0) else tuple(int(v * 0.86) for v in rgb)
            FX.extrude(c, txt, f, W2 - w / 2, y, 255, face, side=NAVY, depth=size * 0.075)
            c.restore()
        c.restore()
        ctx.behind.mark_all()
        FX.sticker(ctx, t, a=1 - out, r=13)
    # hand-drawn marks as each word is pressed
    L = ctx.front
    a = 255 * (1 - out)
    if a > 0:
        f2 = font("black", TITLE[1][1])
        w2 = f2.measureText(TITLE[1][0])
        FX.underline(L, t, T_CLICK[1] + 0.04, W2 - w2 / 2, W2 + w2 / 2, TITLE[1][2] + 26, rgb=RS.ORANGE, a=a, width=12)
        f3 = font("black", TITLE[2][1])
        w3 = f3.measureText(TITLE[2][0])
        FX.circle(L, t, T_CLICK[2] + 0.04, W2, TITLE[2][2] - 62, w3 / 2 + 46, 112, rgb=RS.WHITE, a=a, width=9, dur=0.32)
    FX.shockwave(ctx, t, 0.0, W2, 1010, rgb=RS.WHITE, dur=0.5, r1=1300)
    if a > 0:                                   # a dark floor: the cut-out fades into it (and the low table with it)
        gp = skia.Paint(AntiAlias=True)
        gp.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 1600), skia.Point(0, 1800)],
                                                    [RS.argb(NAVY, 0), RS.argb(NAVY, int(a))]))
        L.c.drawRect(skia.Rect.MakeLTRB(0, 1600, W, H), gp)
        L.mark(0, 1600, W, H, pad=0)
        kt = clamp01((t - 0.55) / 0.2) * clamp01((T_COLD - 0.35 - t) / 0.15)
        if kt > 0:                              # true: nobody holds this mouse (beside her, clear of the title)
            UI.pill(L, 262, 934, "không ai cầm chuột cả", a * kt, size=32, rgb=(12, 16, 24), k=clamp01((t - 0.55) / 0.25))
    CUR_COLD.draw(ctx.front, t)


for tc_ in T_CLICK:
    cue(tc_, "click", 0.7)
cue(T_COLD - 0.1, "whoosh", 0.5, length=0.45, direction=-1)
FX.beat_pulses(4 * 60.0 / 96.69 / 4, 3, 4 * 60.0 / 96.69 / 4, amt=0.014)

# ============================================================================
# 2.9-6.5 s  "tự mở web… tự bấm… tự gõ": it happens as she says it
# ============================================================================
T_WEB0, T_WEB1 = beat_start("web"), beat_end("web")
WIN_W = (80, 284, 1000, 632)
T_WIN = A["w_tu"] - 0.12
URL1 = "https://bat-ky-web-nao.com"
T_URL = (A["w_mo"] - 0.05, A["w_mo"] + 0.75)
T_BTN = A["w_bam"] + 0.02
T_TYPE = (A["w_go"] - 0.02, T_WEB1 - 0.05)
CUR_WEB = UI.Cursor([(T_COLD - 0.02, 540, 470), (T_WIN, 540, 460), (T_URL[0], 300, 326), (T_BTN, 540, 436),
                     (T_TYPE[0], 300, 560), (T_WEB1 + 0.45, 820, 700)],
                    clicks=[T_WIN, T_URL[0], T_BTN, T_TYPE[0]], move=0.34, t_in=T_COLD - 0.02, t_out=T_WEB1 + 0.75)


@ev(T_WIN, T_WEB1 + 0.4)
def web_scene(ctx, t):
    k, a = kwin(t, T_WIN, T_WEB1 + 0.3)
    if a <= 0:
        return
    L = ctx.front
    c = L.c
    c.save()
    UI.pop_transform(c, 540, 460, k)
    x0, y0, x1, y1 = UI.window(L, WIN_W, a, url=URL1, url_k=tp(t, *T_URL), t=t, typing=True, tab="AI đang lái")
    loaded = clamp01((t - T_URL[1] + 0.25) / 0.2)
    if loaded > 0:
        press = 1.0 if 0 <= t - T_BTN < 0.13 else 0.0
        UI.button(L, 390, 390, 300, 86, "BẤM VÀO ĐÂY", a * loaded, press=press, done=tp(t, T_BTN + 0.1, T_BTN + 0.3), size=30)
        UI.tick(L, 728, 433, 26, a, k=tp(t, T_BTN + 0.12, T_BTN + 0.42))
        UI.field(L, 200, 524, 680, 78, None, "xin chào, tôi là AI", tp(t, *T_TYPE), a * loaded, t=t, focus=t >= T_TYPE[0] - 0.1,
                 size=32)
    c.restore()


@ev(T_COLD - 0.02, T_WEB1 + 0.8)
def web_cursor(ctx, t):
    CUR_WEB.draw(ctx.front, t)


cue(T_WIN, "click", 0.6)
cue(T_WIN + 0.05, "whoosh", 0.4, length=0.35, direction=1)
cue(T_URL[0], "typing", 0.55, until=T_URL[1])
cue(T_BTN, "click", 0.75)
cue(T_BTN + 0.14, "pop", 0.3, f1=MS.note(82))
cue(T_TYPE[0], "typing", 0.55, until=T_TYPE[1])

# ============================================================================
# 6.5-8.9 s  the open question
# ============================================================================
T_ASK0, T_ASK1 = beat_start("ask"), beat_end("ask")
QMARKS = [(165, 430, -14, 0.0), (905, 390, 12, 0.14), (880, 705, -8, 0.28)]


@ev(A["a_lam"] - 0.1, T_ASK1 + 0.05)
def ask_marks(ctx, t):
    L = ctx.front
    for (x, y, rot, dt) in QMARKS:
        k = clamp01((t - (A["a_lam"] + dt)) / 0.22)
        if k <= 0:
            continue
        a = 255 * min(1.0, k * 3) * clamp01((T_ASK1 + 0.05 - t) / 0.1)
        s = 0.5 + 0.5 * ease_out_back(k)
        c = L.c
        c.save()
        c.translate(x, y)
        c.rotate(rot + 4 * math.sin(t * 5 + x))
        c.scale(s, s)
        f = font("black", 190)
        FX.extrude(c, "?", f, -f.measureText("?") / 2, 60, a, YELLOW, side=NAVY, depth=12)
        c.restore()
        L.mark(x - 130, y - 170, x + 150, y + 120)


for (_x, _y, _r, dt_) in QMARKS:
    cue(A["a_lam"] + dt_, "pop", 0.22, f1=MS.note(77 + int(dt_ * 20)))

# ============================================================================
# 8.9-11.1 s  THE REVEAL: black, PLAY WRIGHT as windows onto him, a flight through a letter on the word
# ============================================================================
T_REV0 = beat_start("reveal")
T_PW = A["r_pw"]                              # the word, and the drop
MASK = [("PLAY", 372, 1070), ("WRIGHT", 244, 1300)]
PIVOT = FX.glyph_point(MASK, (566, 1000))
T_FLY = T_PW - 0.04
FLY = 0.34


@ev(T_REV0 - 0.02, T_FLY + FLY + 0.02)
def reveal_mask(ctx, t):
    k_in = clamp01((t - (T_REV0 - 0.02)) / 0.1)
    if t < T_REV0 + 0.1 and k_in < 1:         # the black closes in two frames, like a shutter
        c = ctx.ui.c
        h = H / 2 * k_in
        c.drawRect(skia.Rect.MakeLTRB(0, 0, W, h), skia.Paint(Color=skia.Color4f(0.02, 0.03, 0.05, 1)))
        c.drawRect(skia.Rect.MakeLTRB(0, H - h, W, H), skia.Paint(Color=skia.Color4f(0.02, 0.03, 0.05, 1)))
        ctx.ui.mark_all()
        return
    words = [("AI", A["r_ai"]), ("dùng", A["r_ai"] + 0.38), ("thư viện…", A["r_ai"] + 0.72)]
    line = " ".join(w for w, tw in words if t >= tw - 0.04)
    FX.mask_title(ctx, t, T_REV0, T_FLY, FLY, MASK, PIVOT, small=(line, 62, 640, (255, 255, 255)) if line else None)


@ev(T_PW, T_PW + 0.9)
def reveal_wave(ctx, t):
    cx, cy = chest(ctx)
    FX.shockwave(ctx, t, T_PW + 0.16, cx, cy, rgb=RS.AQUA, dur=0.6, r1=1250)
    FX.speedlines(ctx, t, T_PW + 0.16, cx, cy, rgb=RS.WHITE, dur=0.45, n=22, seed=9)


PUNCHES.append((T_PW + 0.14, 0.05, 0.05, 0.25, 0.6))
cue(T_REV0 - 0.02, "shutter", 0.5)
cue(T_FLY + 0.1, "whoosh", 0.7, length=0.5, direction=1)

# the promise, early: why stay to the end
T_PROM = (T_PW + 0.75, beat_end("human") - 0.1)


@ev(T_PROM[0], T_PROM[1] + 0.2)
def promise(ctx, t):
    k = clamp01((t - T_PROM[0]) / 0.3)
    a = 255 * clamp01((T_PROM[1] + 0.2 - t) / 0.2)
    UI.pill(ctx.front, W2, 330, "cuối video: cách nhận skill điều khiển Zalo", a, size=36, rgb=(255, 226, 60), fg=(16, 20, 30), k=k)


cue(T_PROM[0], "pop", 0.24, f1=MS.note(85))

# ============================================================================
# 11.1-14.0 s  "thao tác trên trình duyệt như là người": the cursor wanders like a hand
# ============================================================================
T_HUM0, T_HUM1 = beat_start("human"), beat_end("human")
CUR_HUM = UI.Cursor([(T_HUM0 + 0.2, 1010, 520), (A["h_thao"], 800, 470), (A["h_thao"] + 0.5, 300, 520),
                     (A["h_thao"] + 1.0, 420, 760), (A["h_nguoi"], 740, 730), (T_HUM1 + 0.3, 560, 420)],
                    clicks=[A["h_thao"] + 0.5, A["h_nguoi"]], move=0.42, t_in=T_HUM0 + 0.2, t_out=T_HUM1 + 0.45)


@ev(T_HUM0 + 0.2, T_HUM1 + 0.5)
def human_cursor(ctx, t):
    CUR_HUM.draw(ctx.front, t)


cue(A["h_thao"] + 0.5, "click", 0.5)
cue(A["h_nguoi"], "click", 0.5)

# ============================================================================
# 14.0-17.1 s  the dictionary card: playwright = nhà biên kịch
# ============================================================================
T_MEAN0, T_MEAN1 = beat_start("mean"), beat_end("mean")
DICT = (110, 300, 970, 720)


@ev(T_MEAN0 + 0.05, T_MEAN1 + 0.1)
def dictionary(ctx, t):
    k, a = kwin(t, T_MEAN0 + 0.05, T_MEAN1 + 0.05)
    if a <= 0:
        return
    L = ctx.front
    c = L.c
    c.save()
    UI.pop_transform(c, 540, 510, k)
    UI.card(L, DICT, a)
    x0, y0, x1, y1 = DICT
    UI.text(c, "play·wright", font("serif_k", 112), x0 + 50, y0 + 130, UI.INK, a)
    UI.text(c, "danh từ · tiếng Anh", font("medium", 30), x0 + 54, y0 + 184, UI.MUTE, a)
    c.drawRect(skia.Rect.MakeLTRB(x0 + 50, y0 + 212, x1 - 50, y0 + 215), skia.Paint(Color=UI.c4(UI.LINE, a)))
    k1 = clamp01((t - (A["m_kich"] - 0.08)) / 0.16)
    if k1 > 0:
        strike = clamp01((t - (A["m_nha"] - 0.1)) / 0.18)
        col = tuple(int(UI.INK[i] + (UI.MUTE[i] - UI.INK[i]) * strike) for i in range(3))
        f1 = font("bold", 54)
        w1 = UI.text(c, "kịch bản?", f1, x0 + 54, y0 + 292 + (1 - ease_out_cubic(k1)) * 12, col, a * k1)
        if strike > 0:
            sp = skia.Paint(AntiAlias=True, Color=UI.c4(UI.MUTE, a))
            sp.setStrokeWidth(5)
            c.drawLine(x0 + 48, y0 + 274, x0 + 48 + (w1 + 12) * strike, y0 + 274, sp)
    k2 = clamp01((t - (A["m_nha"] - 0.06)) / 0.14)
    if k2 > 0:
        f2 = font("black", 104)
        txt = "nhà biên kịch"
        w2 = f2.measureText(txt)
        FX.highlight(L, t, A["m_nha"] - 0.04, x0 + 54, x0 + 54 + w2, y0 + 396, 96, rgb=YELLOW, a=a * 0.95)
        UI.text(c, txt, f2, x0 + 54, y0 + 396 + (1 - ease_out_back(k2)) * 14, UI.INK, a * k2)
    c.restore()
    FX.underline(L, t, A["m_nha"] + 0.5, x0 + 60, x0 + 700, y0 + 420, rgb=RS.RED, a=a, width=9)


cue(T_MEAN0 + 0.06, "whoosh", 0.35, length=0.35, direction=1)
cue(A["m_kich"] - 0.06, "tick", 0.3, f=MS.note(82))
cue(A["m_nha"] - 0.04, "pop", 0.3, f1=MS.note(85))

# ============================================================================
# 17.1-33.8 s  THE SCRIPT: a login form, four steps the cursor performs, then "run" replays them at speed
# ============================================================================
T_SC0 = beat_start("script")
T_RR0, T_RR1 = beat_start("rerun"), beat_end("rerun")
WIN_S = (80, 284, 1000, 676)
URL2 = "app.phanmem.vn/login"
STEPS = [("1", "mở link", A["s1"]), ("2", "username", A["s2"]), ("3", "password", A["s3"]), ("4", "login", A["s4"])]
T_S1 = (A["s1_mo"] - 0.1, A["s1_mo"] + 0.75)          # the URL is typed
T_S2 = (A["s2_dien"] - 0.1, beat_end("step2") - 0.1)  # username
T_S3 = (A["s3_nhap"] - 0.2, beat_end("step3") - 0.15)  # password
T_S4 = A["s4_login"] - 0.12                           # the press
BEAT = 60.0 / 96.69
T_RUN = A["rr_run"]
N_RUN = max(2, int((A["rr_xong"] - 0.15 - (T_RUN + 0.2)) / (BEAT * 0.75)))
CYC = (A["rr_xong"] - 0.15 - (T_RUN + 0.2)) / N_RUN     # one replay
F_USER, F_PASS, B_LOGIN, B_RUN = (200, 442, 680, 66), (200, 522, 680, 66), (200, 602, 680, 60), (806, 376, 164, 52)
CUR_S = UI.Cursor([(T_SC0 + 0.25, 540, 480), (T_S1[0], 320, 326), (T_S2[0], 300, 475), (T_S3[0], 300, 555),
                   (T_S4, 540, 632), (T_RR0 + 0.6, 700, 520), (T_RUN, 890, 402), (T_RR1 + 0.2, 930, 560)],
                  clicks=[T_SC0 + 0.25, T_S1[0], T_S2[0], T_S3[0], T_S4, T_RUN], move=0.36, t_in=T_SC0 + 0.2,
                  t_out=T_RR1 + 0.35)


def script_state(t):
    """(url_k, form, user_k, pass_k, press, done, focus, lap) at t, through the first run and the replays"""
    if t < T_RR0 + 0.25:
        return (tp(t, *T_S1), clamp01((t - T_S1[1]) / 0.2), tp(t, *T_S2), tp(t, *T_S3),
                1.0 if 0 <= t - T_S4 < 0.13 else 0.0, tp(t, T_S4 + 0.1, T_S4 + 0.3),
                1 if T_S2[0] - 0.1 <= t < T_S3[0] - 0.1 else (2 if T_S3[0] - 0.1 <= t < T_S4 - 0.2 else 0), 1)
    if t < T_RUN + 0.2:
        return (1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0, 1)            # reset, waiting for "run"
    u = (t - (T_RUN + 0.2)) / CYC
    lap = min(N_RUN - 1, int(u))
    v = u - lap if u < N_RUN else 1.0
    return (1.0, 1.0, clamp01(v / 0.25), clamp01((v - 0.28) / 0.25), 1.0 if 0.6 <= v < 0.74 else 0.0,
            clamp01((v - 0.7) / 0.12), 1 if v < 0.28 else (2 if v < 0.56 else 0), lap + 2)


@ev(T_SC0 + 0.2, T_RR1 + 0.35)
def script_scene(ctx, t):
    k, a = kwin(t, T_SC0 + 0.25, T_RR1 + 0.25)
    if a <= 0:
        return
    L = ctx.front
    c = L.c
    url_k, form, user_k, pass_k, press, done, focus, lap = script_state(t)
    c.save()
    UI.pop_transform(c, 540, 480, k)
    UI.window(L, WIN_S, a, url=URL2, url_k=url_k, t=t, typing=t < T_S1[1], tab="kịch bản")
    if form > 0:
        af = a * form
        UI.text(c, "Đăng nhập", font("black", 40), 200, 418, UI.INK, af)
        UI.field(L, *F_USER, None, "admin", user_k, af, t=t, focus=focus == 1, size=30)
        UI.field(L, *F_PASS, None, "matkhau123", pass_k, af, t=t, focus=focus == 2, password=True, size=30)
        UI.button(L, *B_LOGIN, "Đăng nhập" if done < 0.5 else "Đã đăng nhập", af, press=press, done=done, size=28)
        UI.tick(L, 838, 632, 22, af, k=done)
    if t >= T_RR0 + 0.3:                                            # the "run" button and the lap counter
        kr = clamp01((t - (T_RR0 + 0.3)) / 0.25)
        pr = 1.0 if 0 <= t - T_RUN < 0.13 else 0.0
        UI.button(L, *B_RUN, "   RUN", a * kr, press=pr, rgb=(255, 110, 32), size=28)
        tri = skia.Path()                                           # a play triangle (the font has no such glyph)
        tri.moveTo(B_RUN[0] + 34, B_RUN[1] + 14)
        tri.lineTo(B_RUN[0] + 34, B_RUN[1] + B_RUN[3] - 14)
        tri.lineTo(B_RUN[0] + 58, B_RUN[1] + B_RUN[3] / 2)
        tri.close()
        c.drawPath(tri, skia.Paint(AntiAlias=True, Color=UI.c4((255, 255, 255), a * kr)))
        if lap >= 2:
            UI.pill(L, 300, 408, f"lần {lap}", a, size=30, rgb=(16, 20, 30))
    c.restore()
    # the four steps under the window
    kc = clamp01((t - (A["s_kich"] - 0.1)) / 0.3)
    if kc > 0:
        x, wchip, h, gp, y = 80.0, 221.0, 58.0, 12.0, 694.0
        if t < T_RR0 + 0.25:
            cur_i = max([i for i, s_ in enumerate(STEPS) if t >= s_[2] - 0.06] or [-1])
            done_n = cur_i
        elif t < T_RUN + 0.2:
            cur_i, done_n = -1, -1
        else:
            v = ((t - (T_RUN + 0.2)) / CYC) % 1.0 if t < T_RUN + 0.2 + N_RUN * CYC else 0.99
            cur_i = min(3, int(v / 0.25))
            done_n = cur_i
        for i, (num, lab, _t) in enumerate(STEPS):
            xs = x + i * (wchip + gp)
            is_cur = i == cur_i
            is_done = i < done_n or (t >= T_S4 + 0.2 and t < T_RR0 + 0.25) or (t >= T_RUN + 0.2 + N_RUN * CYC)
            col = RS.AQUA if is_cur else ((36, 196, 118) if is_done else (12, 16, 24))
            fg = (12, 16, 24) if (is_cur or is_done) else (236, 240, 246)
            yy = y + (1 - ease_out_cubic(clamp01(kc * 1.4 - i * 0.12))) * 24
            aa = a * clamp01(kc * 1.4 - i * 0.12) * (1.0 if (is_cur or is_done) else 0.78)
            c.drawRRect(UI.rr(xs, yy, xs + wchip, yy + h, h / 2), skia.Paint(AntiAlias=True, Color=UI.c4(col, aa)))
            UI.text(c, num, font("black", 30), xs + 26, yy + 40, fg, aa)
            UI.text(c, lab, font("bold", 28), xs + 58, yy + 39, fg, aa)
        L.mark(60, y - 30, 1020, y + h + 20)
    # "XONG": a stamp
    ks = clamp01((t - (A["rr_xong"] - 0.05)) / 0.16)
    if ks > 0:
        f = font("black", 190)
        txt = "XONG"
        w = f.measureText(txt)
        c.save()
        c.translate(540, 500)
        c.rotate(-9)
        s = 1.0 + 0.9 * (1 - ease_out_cubic(ks))
        c.scale(s, s)
        FX.extrude(c, txt, f, -w / 2, 66, a * min(1.0, ks * 2), (36, 196, 118), side=(8, 60, 36), depth=14, edge=RS.WHITE)
        c.restore()
        L.mark(60, 300, 1020, 720)
    CUR_S.draw(L, t)


cue(T_SC0 + 0.25, "click", 0.6)
cue(T_SC0 + 0.3, "whoosh", 0.4, length=0.35, direction=1)
for (_n, _l, ts_) in STEPS:
    cue(ts_ - 0.05, "pop", 0.26, f1=MS.note(77 + 2 * int(_n)))
cue(T_S1[0], "click", 0.5)
cue(T_S1[0] + 0.05, "typing", 0.5, until=T_S1[1])
cue(T_S2[0], "click", 0.5)
cue(T_S2[0] + 0.05, "typing", 0.5, until=T_S2[1])
cue(T_S3[0], "click", 0.5)
cue(T_S3[0] + 0.05, "typing", 0.5, until=T_S3[1])
cue(T_S4, "click", 0.8)
cue(T_S4 + 0.14, "ding", 0.4, f=MS.note(89))
cue(T_RUN, "click", 0.8)
for i_ in range(N_RUN):
    for j_, fr_ in enumerate((0.02, 0.28, 0.6)):
        cue(T_RUN + 0.2 + (i_ + fr_) * CYC, "tick", 0.28, f=MS.note(82 + 2 * j_))
    cue(T_RUN + 0.2 + (i_ + 0.72) * CYC, "pop", 0.22, f1=MS.note(89))
cue(A["rr_xong"] - 0.05, "impact", 0.35, length=1.0)

# ============================================================================
# 33.8-37.1 s  her second question: it cannot see, so how does it click?
# ============================================================================
T_SEE0, T_SEE1 = beat_start("see"), beat_end("see")
G_SEE = gap("see")


def eye(L, t, t0, x, y, a, slash_t=None, s=1.0):
    FX.circle(L, t, t0, x, y, 118 * s, 62 * s, rgb=RS.WHITE, a=a, width=10, dur=0.3, turns=1.04, start=3.3)
    kp = clamp01((t - (t0 + 0.2)) / 0.12)
    if kp > 0:
        L.c.drawCircle(x, y, 34 * s * ease_out_back(kp), skia.Paint(AntiAlias=True, Color=UI.c4(RS.WHITE, a)))
        L.c.drawCircle(x + 9 * s, y - 9 * s, 10 * s * kp, skia.Paint(AntiAlias=True, Color=UI.c4((16, 20, 30), a)))
    if slash_t is not None:
        FX._draw_poly(L.c, [(x - 130 * s + 260 * s * u, y + 86 * s - 172 * s * u) for u in [i / 20 for i in range(21)]],
                      clamp01((t - slash_t) / 0.16), RS.RED, a, 15 * s, seed=6)
    L.mark(x - 170 * s, y - 120 * s, x + 170 * s, y + 120 * s)


@ev(A["e_nhin"] - 0.2, G_SEE[1])
def see_eye(ctx, t):
    a = 255 * clamp01((G_SEE[1] - t) / 0.1)
    eye(ctx.front, t, A["e_nhin"] - 0.15, W2, 400, a, slash_t=A["e_nhin"] + 0.28)


cue(A["e_nhin"] - 0.12, "swipe", 0.3)
cue(A["e_nhin"] + 0.28, "glitch", 0.25)

# ============================================================================
# 37.1-44.1 s  THE X-RAY: no screenshot; a scan line turns the page into its HTML
# ============================================================================
T_CODE0 = beat_start("code")
T_NL1 = beat_end("nolook")
T_SHOT = A["k_chup"] + 0.05
T_SCAN = (A["k_doc"] - 0.05, A["k_ma"] + 0.2)
HTML = [[("<form ", (130, 170, 255)), ("action", (140, 220, 200)), ("=", (200, 205, 215)), ('"/login"', (255, 190, 120)), (">", (130, 170, 255))],
        [("  <input ", (130, 170, 255)), ("name", (140, 220, 200)), ("=", (200, 205, 215)), ('"username"', (255, 190, 120)), (">", (130, 170, 255))],
        [("  <input ", (130, 170, 255)), ("type", (140, 220, 200)), ("=", (200, 205, 215)), ('"password"', (255, 190, 120)), (">", (130, 170, 255))],
        [("  <button ", (130, 170, 255)), ("id", (140, 220, 200)), ("=", (200, 205, 215)), ('"login"', (255, 190, 120)), (">", (130, 170, 255))],
        [("    Login", (235, 238, 245))],
        [("  </button>", (130, 170, 255))],
        [("</form>", (130, 170, 255))]]
CUR_K = UI.Cursor([(T_CODE0 + 0.3, 880, 760), (A["k_nut"] - 0.1, 600, 640), (T_SCAN[1] + 0.3, 400, 558),
                   (T_NL1, 400, 558)], clicks=[A["k_nut"] - 0.1, T_SCAN[1] + 0.3], move=0.4, t_in=T_CODE0 + 0.3,
                  t_out=T_NL1 + 0.1)


@ev(T_CODE0 + 0.02, T_NL1 + 0.15)
def xray(ctx, t):
    k, a = kwin(t, T_CODE0 + 0.05, T_NL1 + 0.08)
    if a <= 0:
        return
    L = ctx.front
    c = L.c
    c.save()
    UI.pop_transform(c, 540, 480, k)
    px0, py0, px1, py1 = UI.window(L, WIN_S, a, url=URL2, url_k=1.0, t=t, tab="trang web")
    UI.text(c, "Đăng nhập", font("black", 40), 200, 418, UI.INK, a)
    UI.field(L, *F_USER, None, "admin", 1.0, a, t=t, size=30)
    UI.field(L, *F_PASS, None, "matkhau123", 1.0, a, t=t, password=True, size=30)
    UI.button(L, *B_LOGIN, "Đăng nhập", a, size=28)
    # the scan: above the line the page is its code
    ks = tp(t, *T_SCAN)
    if ks > 0:
        ys = py0 + (py1 - py0 + 6) * ease_out_cubic(ks)
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(px0, py0, px1, min(py1, ys)))
        c.drawRect(skia.Rect.MakeLTRB(px0, py0, px1, py1), skia.Paint(Color=UI.c4(UI.CODE_BG, a)))
        fm = UI.mono(31)
        yy = py0 + 50
        for i, ln in enumerate(HTML):
            xx = px0 + 34
            if i == 3:
                hk = clamp01((t - (T_SCAN[1] + 0.25)) / 0.2)
                if hk > 0:
                    c.drawRRect(UI.rr(px0 + 20, yy - 30, px0 + 20 + (px1 - px0 - 40) * hk, yy + 12, 8),
                                skia.Paint(AntiAlias=True, Color=UI.c4(RS.AQUA, a * 0.28)))
            for s_, rgb in ln:
                xx += UI.text(c, s_, fm, xx, yy, rgb, a)
            yy += 41
        c.restore()
        if ks < 1:
            gl = skia.Paint(AntiAlias=True, Color=UI.c4(RS.AQUA, a))
            gl.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10))
            c.drawRect(skia.Rect.MakeLTRB(px0, ys - 7, px1, ys + 7), gl)
            c.drawRect(skia.Rect.MakeLTRB(px0, ys - 2, px1, ys + 2), skia.Paint(Color=UI.c4(RS.WHITE, a)))
    c.restore()
    # "không chụp ảnh màn hình": the shutter brackets, a blink, then a red cross
    u = t - T_SHOT
    if 0 <= u < T_SCAN[0] - T_SHOT:
        aa = a * clamp01((T_SCAN[0] - 0.05 - t) / 0.15)
        bp = skia.Paint(AntiAlias=True, Color=UI.c4(RS.WHITE, aa))
        bp.setStyle(skia.Paint.kStroke_Style)
        bp.setStrokeWidth(9)
        bp.setStrokeCap(skia.Paint.kSquare_Cap)
        x0, y0, x1, y1 = WIN_S[0] - 22, WIN_S[1] - 22, WIN_S[2] + 22, WIN_S[3] + 22
        g = 60 + 30 * (1 - ease_out_cubic(clamp01(u / 0.2)))
        for (cx_, cy_, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            c.drawLine(cx_, cy_, cx_ + dx * g, cy_, bp)
            c.drawLine(cx_, cy_, cx_, cy_ + dy * g, bp)
        if u < 0.12:
            c.drawRect(skia.Rect.MakeLTRB(WIN_S[0], WIN_S[1], WIN_S[2], WIN_S[3]),
                       skia.Paint(Color=UI.c4(RS.WHITE, a * 0.8 * (1 - u / 0.12))))
        UI.cross(L, 540, 480, 120, aa, k=tp(t, T_SHOT + 0.3, T_SHOT + 0.6), width=30)
        L.mark(40, 240, 1040, 720)
    if T_CODE0 + 0.3 <= t < T_SCAN[0]:
        FX.circle(L, t, A["k_nut"] - 0.05, 540, 632, 380, 56, rgb=RS.ORANGE, a=a * clamp01((T_SCAN[0] - t) / 0.15), width=9)
    CUR_K.draw(L, t)


@ev(T_SCAN[0], T_SCAN[0] + 1.0)
def xray_wave(ctx, t):
    cx, cy = chest(ctx)
    FX.shockwave(ctx, t, T_SCAN[0], cx, cy, rgb=RS.AQUA, dur=0.55, r1=1200)


cue(T_CODE0 + 0.08, "whoosh", 0.35, length=0.35, direction=1)
cue(T_SHOT, "shutter", 0.7)
cue(T_SHOT + 0.3, "glitch", 0.3)
cue(T_SCAN[0], "swell", 0.4, length=0.5)
cue(T_SCAN[1] + 0.3, "click", 0.6)

# ============================================================================
# 44.1-56.6 s  ZALO: log in to the web chat, find ABC, send a message
# ============================================================================
T_Z0, T_Z1 = beat_start("zalo"), beat_end("zalo")
WIN_Z = (80, 284, 1000, 700)
T_ZWIN = A["z_dang"] - 0.35
T_ZURL = (A["z_dang"], A["z_zalo2"] + 0.45)
T_ZSEARCH = A["z_tim"]
T_ZABC = (A["z_abc"] - 0.25, A["z_abc"] + 0.35)
T_ZPICK = A["z_abc"] + 0.52
T_ZMSG = (A["z_nhan2"] - 0.1, A["z_nhan2"] + 0.5)
T_ZSEND = A["z_nhan2"] + 0.62
MSG = "Tối nay cà phê nhé?"
CUR_Z = UI.Cursor([(T_ZWIN, 540, 500), (T_ZURL[0], 330, 326), (T_ZSEARCH, 210, 410), (T_ZPICK, 230, 498),
                   (T_ZMSG[0], 600, 650), (T_ZSEND, 944, 650), (T_Z1 + 0.2, 900, 780)],
                  clicks=[T_ZWIN, T_ZURL[0], T_ZSEARCH, T_ZPICK, T_ZMSG[0], T_ZSEND], move=0.38, t_in=T_ZWIN - 0.1,
                  t_out=T_Z1 + 0.3)


@ev(T_ZWIN - 0.1, T_Z1 + 0.35)
def zalo_scene(ctx, t):
    k, a = kwin(t, T_ZWIN, T_Z1 + 0.25)
    L = ctx.front
    c = L.c
    if a > 0:
        c.save()
        UI.pop_transform(c, 540, 500, k)
        px0, py0, px1, py1 = UI.window(L, WIN_Z, a, url="chat.zalo.me", url_k=tp(t, *T_ZURL), t=t, typing=True,
                                       tab="Zalo web")
        ld = clamp01((t - T_ZURL[1]) / 0.25)
        if ld > 0:
            al = a * ld
            xm = px0 + 300                                      # the list | the conversation
            c.drawRect(skia.Rect.MakeLTRB(xm, py0, xm + 2, py1), skia.Paint(Color=UI.c4(UI.LINE, al)))
            UI.field(L, px0 + 20, py0 + 18, 262, 56, None, "ABC", tp(t, *T_ZABC), al, t=t,
                     focus=T_ZSEARCH - 0.05 <= t < T_ZPICK, size=28)
            if t < T_ZABC[0]:
                UI.text(c, "Tìm kiếm", font("medium", 26), px0 + 42, py0 + 55, UI.MUTE, al)
            picked = t >= T_ZPICK
            names = [("ABC", True)] if t >= T_ZABC[1] else [("Mẹ", False), ("Nhóm công ty", False), ("ABC", False)]
            for i, (nm, hit) in enumerate(names):
                yy = py0 + 92 + i * 70
                if hit:
                    c.drawRRect(UI.rr(px0 + 12, yy - 4, xm - 12, yy + 62, 14),
                                skia.Paint(AntiAlias=True, Color=UI.c4(UI.BLUE if picked else (228, 236, 255), al)))
                c.drawCircle(px0 + 50, yy + 29, 24, skia.Paint(AntiAlias=True, Color=UI.c4((200, 208, 222), al)))
                UI.text(c, nm[:1], font("bold", 26), px0 + 50, yy + 38, (255, 255, 255), al, align="center")
                UI.text(c, nm, font("semi", 27), px0 + 88, yy + 38, (255, 255, 255) if (hit and picked) else UI.INK, al)
            # the conversation
            if picked:
                kp = clamp01((t - T_ZPICK) / 0.2)
                UI.text(c, "ABC", font("black", 34), xm + 30, py0 + 50, UI.INK, al * kp)
                UI.text(c, "đang hoạt động", font("medium", 22), xm + 112, py0 + 48, (36, 196, 118), al * kp)
                c.drawRect(skia.Rect.MakeLTRB(xm + 2, py0 + 72, px1, py0 + 74), skia.Paint(Color=UI.c4(UI.LINE, al * kp)))
                sent = clamp01((t - T_ZSEND - 0.05) / 0.22)
                UI.field(L, xm + 22, py1 - 78, px1 - xm - 122, 58, None, MSG if sent <= 0 else "", tp(t, *T_ZMSG), al * kp,
                         t=t, focus=T_ZMSG[0] - 0.05 <= t < T_ZSEND, size=27)
                pr = 1.0 if 0 <= t - T_ZSEND < 0.13 else 0.0
                c.drawCircle(px1 - 56, py1 - 49, 29 * (1 - 0.1 * pr), skia.Paint(AntiAlias=True, Color=UI.c4(UI.BLUE, al * kp)))
                UI.text(c, ">", font("black", 34), px1 - 56, py1 - 37, (255, 255, 255), al * kp, align="center")
                if sent > 0:
                    UI.bubble(L, px1 - 24, py0 + 110, px1 - xm - 60, MSG, al, mine=True, size=29, k=sent)
                    UI.text(c, "đã gửi", font("medium", 22), px1 - 28, py0 + 196, UI.MUTE,
                            al * clamp01((t - T_ZSEND - 0.3) / 0.2), align="right")
                    UI.tick(L, px1 - 122, py0 + 189, 13, al, k=clamp01((t - T_ZSEND - 0.3) / 0.3))
        c.restore()
    CUR_Z.draw(L, t)


cue(T_ZWIN, "click", 0.6)
cue(T_ZWIN + 0.05, "whoosh", 0.4, length=0.35, direction=1)
cue(T_ZURL[0], "typing", 0.5, until=T_ZURL[1])
cue(T_ZSEARCH, "click", 0.5)
cue(T_ZABC[0], "typing", 0.5, until=T_ZABC[1])
cue(T_ZPICK, "click", 0.6)
cue(T_ZMSG[0] + 0.02, "typing", 0.5, until=T_ZMSG[1])
cue(T_ZSEND, "click", 0.8)
cue(T_ZSEND + 0.1, "swipe", 0.4)
cue(T_ZSEND + 0.32, "ding", 0.35, f=MS.note(89))

# ============================================================================
# 56.6-66.7 s  the first time the AI writes the script; after that its brain rests
# ============================================================================
T_F0, T_B1 = beat_start("first"), beat_end("brain")


@ev(A["f_ai"] - 0.5, T_B1 + 0.1)
def ai_node(ctx, t):
    k = clamp01((t - (A["f_ai"] - 0.5)) / 0.3)
    a = 255 * min(1.0, k * 2) * clamp01((T_B1 + 0.1 - t) / 0.15)
    if a <= 0:
        return
    L = ctx.front
    c = L.c
    off = clamp01((t - (A["b_khong"] - 0.05)) / 0.4)                 # "không dùng đến bộ não của AI nữa": it powers down
    x, y, r = W2, 372, 74
    s = 0.6 + 0.4 * ease_out_back(k)
    col = tuple(int(RS.AQUA[i] + ((92, 100, 114)[i] - RS.AQUA[i]) * off) for i in range(3))
    if off < 1:
        for i in range(3):
            ph = (t * 1.1 + i / 3) % 1.0
            rp = skia.Paint(AntiAlias=True, Color=UI.c4(RS.AQUA, a * 0.55 * (1 - ph) * (1 - off)))
            rp.setStyle(skia.Paint.kStroke_Style)
            rp.setStrokeWidth(5)
            c.drawCircle(x, y, r * s + 70 * ph, rp)
    c.drawCircle(x, y, r * s, skia.Paint(AntiAlias=True, Color=UI.c4((12, 16, 24), a * 0.92)))
    rp = skia.Paint(AntiAlias=True, Color=UI.c4(col, a))
    rp.setStyle(skia.Paint.kStroke_Style)
    rp.setStrokeWidth(8)
    c.drawCircle(x, y, r * s, rp)
    f = font("black", 62 * s)
    UI.text(c, "AI", f, x, y + 22 * s, col, a, align="center")
    lab = "đang nghĩ…" if off < 0.5 else "nghỉ ngơi  z z z"
    UI.pill(L, x, y + 150, lab, a, size=30, rgb=(12, 16, 24), fg=col)
    L.mark(x - 230, y - 170, x + 230, y + 200)


cue(A["f_ai"] - 0.5, "connect", 0.4)
cue(A["b_khong"] - 0.05, "rewind", 0.3)

# ============================================================================
# 66.7-73.5 s  20 people = the script 20 times; far fewer tokens
# ============================================================================
T_T0, T_T1 = beat_start("twenty"), beat_end("twenty")
T_V0, T_V1 = beat_start("save"), beat_end("save")
T_CNT = (A["t_20"] - 0.1, A["t_20b"] - 0.25)


@ev(T_T0 + 0.1, T_T1 + 0.12)
def twenty_scene(ctx, t):
    k = clamp01((t - (T_T0 + 0.1)) / 0.3)
    a = 255 * min(1.0, k * 2) * clamp01((T_T1 + 0.12 - t) / 0.12)
    if a <= 0:
        return
    L = ctx.front
    c = L.c
    n = int(round(1 + 19 * ease_out_cubic(tp(t, *T_CNT)))) if t >= T_CNT[0] else 1
    flash_all = clamp01((t - (A["t_20b"] - 0.05)) / 0.2)
    f = font("black", 250)
    txt = f"×{n}"
    w = f.measureText(txt)
    bump = 1 + 0.08 * math.exp(-((t - T_CNT[0]) * 19 / max(0.1, T_CNT[1] - T_CNT[0]) % 1.0) * 3) if T_CNT[0] <= t < T_CNT[1] else 1.0
    c.save()
    c.translate(W2, 450)
    c.scale(bump * (0.7 + 0.3 * ease_out_back(k)), bump * (0.7 + 0.3 * ease_out_back(k)))
    FX.extrude(c, txt, f, -w / 2, 60, a, RS.ORANGE if flash_all < 1 else (36, 196, 118), side=(60, 26, 8), depth=16, edge=RS.WHITE)
    c.restore()
    # twenty small bubbles, two rows of ten
    for i in range(20):
        on = i < n and t >= T_CNT[0]
        cx_ = 126 + (i % 10) * 92
        cy_ = 590 + (i // 10) * 76
        col = (36, 196, 118) if (on and flash_all > 0) else (UI.BLUE if on else (12, 16, 24))
        c.drawRRect(UI.rr(cx_ - 36, cy_ - 26, cx_ + 36, cy_ + 26, 18),
                    skia.Paint(AntiAlias=True, Color=UI.c4(col, a * (1.0 if on else 0.45))))
        if on:
            for d in (-14, 0, 14):
                c.drawCircle(cx_ + d, cy_, 4.5, skia.Paint(AntiAlias=True, Color=UI.c4(RS.WHITE, a)))
    L.mark(60, 250, 1020, 700)


for i_ in range(10):
    cue(T_CNT[0] + i_ * (T_CNT[1] - T_CNT[0]) / 10, "tick", 0.2, f=MS.note(77 + (i_ % 4) * 3))
cue(A["t_20b"] - 0.05, "ding", 0.4, f=MS.note(89))


@ev(T_V0 + 0.05, T_V1 + 0.12)
def token_meter(ctx, t):
    k = clamp01((t - (T_V0 + 0.05)) / 0.3)
    a = 255 * min(1.0, k * 2) * clamp01((T_V1 + 0.12 - t) / 0.12)
    if a <= 0:
        return
    L = ctx.front
    c = L.c
    UI.card(L, (90, 290, 990, 600), a, rgb=(12, 16, 24), shadow=0.3)
    UI.text(c, "token cho 20 tin nhắn", font("bold", 32), 130, 350, (150, 160, 178), a)
    g1 = ease_out_cubic(tp(t, T_V0 + 0.25, T_V0 + 0.95))
    g2 = ease_out_cubic(tp(t, A["v_tiet"] - 0.05, A["v_tiet"] + 0.4))
    UI.text(c, "AI nghĩ lại mỗi lần", font("semi", 30), 130, 412, (236, 240, 246), a)
    c.drawRRect(UI.rr(130, 428, 130 + 820 * g1, 468, 12), skia.Paint(AntiAlias=True, Color=UI.c4(RS.RED, a)))
    UI.text(c, "chạy kịch bản Playwright", font("semi", 30), 130, 522, (236, 240, 246), a)
    c.drawRRect(UI.rr(130, 538, 130 + max(14, 96 * g2), 578, 12), skia.Paint(AntiAlias=True, Color=UI.c4(RS.AQUA, a)))
    L.mark(60, 270, 1020, 640)


cue(T_V0 + 0.08, "whoosh", 0.3, length=0.3, direction=1)
cue(A["v_tiet"] - 0.05, "pop", 0.3, f1=MS.note(85))

# ============================================================================
# 73.5-84.2 s  THE CALL: the skill as a download, the comment typed by the cursor, then his laugh and the typos
# ============================================================================
T_Q0, T_Q1 = beat_start("cta"), beat_end("cta")
T_G0, T_G1 = beat_start("sting"), beat_end("sting")
TILE = (130, 296, 950, 590)
BOX = (100, 372, 980, 500)
T_TILE = (A["q_tai"] - 0.12, A["q_comment"] - 0.25)
T_BOX = A["q_comment"] - 0.2
T_TYPEC = (A["q_pw2"] - 0.05, A["q_pw2"] + 0.75)
T_SENDC = A["q_nha"] - 0.12
TYPOS = [("Playright", T_G0 + 0.18), ("Plawright", T_G0 + 0.75), ("Playwright", T_G0 + 1.32)]
CUR_Q = UI.Cursor([(T_TILE[0] + 0.1, 960, 760), (A["q_skill"], 760, 540), (T_BOX + 0.25, 330, 438),
                   (T_SENDC, 918, 436), (T_G0 + 0.1, 760, 560), (T_G1 + 0.2, 760, 560)],
                  clicks=[A["q_skill"], T_BOX + 0.25, T_SENDC], move=0.4, t_in=T_TILE[0] + 0.1, t_out=T_G1 + 0.2)


def comment_box(L, t, a, value, vk, focus, sent=0.0, wrong=None):
    c = L.c
    x0, y0, x1, y1 = BOX
    UI.card(L, BOX, a, r=40)
    c.drawCircle(x0 + 62, (y0 + y1) / 2, 34, skia.Paint(AntiAlias=True, Color=UI.c4((200, 208, 222), a)))
    UI.text(c, "bạn", font("bold", 24), x0 + 62, (y0 + y1) / 2 + 8, (255, 255, 255), a, align="center")
    f = font("semi", 44)
    s = UI.typed(value, vk)
    if not s and not focus:
        UI.text(c, "Thêm bình luận…", font("medium", 38), x0 + 118, (y0 + y1) / 2 + 14, UI.MUTE, a)
    col = UI.INK if wrong is None else ((220, 50, 50) if wrong else (24, 150, 90))
    tw = UI.text(c, s, f, x0 + 118, (y0 + y1) / 2 + 16, col, a)
    if focus:
        UI.caret(c, x0 + 118 + tw, (y0 + y1) / 2 + 16, 46, t, a)
    pr = 1.0 if 0 <= t - T_SENDC < 0.13 else 0.0
    c.drawCircle(x1 - 64, (y0 + y1) / 2, 40 * (1 - 0.1 * pr), skia.Paint(AntiAlias=True, Color=UI.c4(RS.ORANGE, a)))
    ar = skia.Path()
    ar.moveTo(x1 - 78, (y0 + y1) / 2 + 16)
    ar.lineTo(x1 - 64, (y0 + y1) / 2 - 18)
    ar.lineTo(x1 - 50, (y0 + y1) / 2 + 16)
    ap = skia.Paint(AntiAlias=True, Color=UI.c4((255, 255, 255), a))
    ap.setStyle(skia.Paint.kStroke_Style)
    ap.setStrokeWidth(8)
    ap.setStrokeCap(skia.Paint.kRound_Cap)
    ap.setStrokeJoin(skia.Paint.kRound_Join)
    c.drawPath(ar, ap)
    return tw


@ev(T_TILE[0], T_G1 + 0.1)
def call_scene(ctx, t):
    L = ctx.front
    c = L.c
    # the skill, as something to download
    k1, a1 = kwin(t, T_TILE[0], T_TILE[1], d_out=0.2)
    if a1 > 0:
        c.save()
        UI.pop_transform(c, 540, 440, k1)
        UI.card(L, TILE, a1)
        x0, y0, x1, y1 = TILE
        c.drawRRect(UI.rr(x0 + 36, y0 + 40, x0 + 196, y0 + 200, 34), skia.Paint(AntiAlias=True, Color=UI.c4(RS.AQUA, a1)))
        UI.text(c, "SKILL", font("black", 40), x0 + 116, y0 + 134, (12, 16, 24), a1, align="center")
        UI.text(c, "Playwright × Zalo", font("black", 54), x0 + 226, y0 + 104, UI.INK, a1)
        UI.text(c, "AI tự đăng nhập · tìm người", font("medium", 30), x0 + 228, y0 + 152, UI.MUTE, a1)
        UI.text(c, "· tự nhắn tin", font("medium", 30), x0 + 228, y0 + 192, UI.MUTE, a1)
        pr = 1.0 if 0 <= t - A["q_skill"] < 0.13 else 0.0
        UI.button(L, x0 + 500, y0 + 216, 280, 58, "TẢI VỀ", a1, press=pr, rgb=RS.ORANGE, size=28)
        c.restore()
    # the comment box
    k2, a2 = kwin(t, T_BOX, T_G1 + 0.1, d_out=0.1)
    if a2 > 0:
        c.save()
        UI.pop_transform(c, 540, 436, k2)
        sent = clamp01((t - T_SENDC - 0.05) / 0.25)
        if t < T_G0:
            comment_box(L, t, a2, "Playwright" if sent <= 0 else "", tp(t, *T_TYPEC), T_BOX + 0.2 <= t < T_SENDC, sent)
        else:
            cur = max([i for i, (_w, tw) in enumerate(TYPOS) if t >= tw] or [-1])
            if cur < 0:
                comment_box(L, t, a2, "", 0.0, True)
            else:
                word, tw = TYPOS[cur]
                shake = 0.0
                if cur < 2 and t - tw > 0.32:
                    shake = 9 * math.sin((t - tw) * 60) * math.exp(-(t - tw - 0.32) / 0.08)
                c.save()
                c.translate(shake, 0)
                comment_box(L, t, a2, word, tp(t, tw, tw + 0.3), True,
                            wrong=None if t - tw < 0.32 else (cur < 2))
                c.restore()
                if t - tw > 0.32:
                    if cur < 2:
                        UI.cross(L, BOX[2] - 170, (BOX[1] + BOX[3]) / 2, 22, a2, k=tp(t, tw + 0.32, tw + 0.5), width=9)
                    else:
                        UI.tick(L, BOX[2] - 170, (BOX[1] + BOX[3]) / 2, 30, a2, k=tp(t, tw + 0.32, tw + 0.6))
        c.restore()
        if 0 < sent and t < T_G0:                                    # the comment flies to the comment button
            fl = ease_in_cubic(tp(t, T_SENDC + 0.05, T_SENDC + 0.5))
            bx, by = 540 + (990 - 540) * fl, 436 + (1180 - 436) * fl
            UI.pill(L, bx, by, "Playwright", a2 * (1 - fl * 0.6), size=44 * (1 - 0.45 * fl), rgb=RS.ORANGE, fg=(255, 255, 255))
        if T_G0 + 0.1 <= t:
            UI.pill(L, W2, 566, "viết sai cũng được, bên mình hiểu", a2, size=32, rgb=(12, 16, 24),
                    k=clamp01((t - (T_G0 + 0.9)) / 0.25))
    CUR_Q.draw(L, t)


cue(T_TILE[0], "whoosh", 0.4, length=0.35, direction=1)
cue(A["q_skill"], "click", 0.7)
cue(T_BOX, "pop", 0.3, f1=MS.note(82))
cue(T_BOX + 0.25, "click", 0.5)
cue(T_TYPEC[0], "typing", 0.6, until=T_TYPEC[1])
cue(T_SENDC, "click", 0.8)
cue(T_SENDC + 0.08, "swipe", 0.45)
for (w_, tw_) in TYPOS:
    cue(tw_, "typing", 0.5, until=tw_ + 0.3)
cue(TYPOS[0][1] + 0.34, "beep", 0.3)
cue(TYPOS[1][1] + 0.34, "beep", 0.3)
cue(TYPOS[2][1] + 0.34, "ding", 0.45, f=MS.note(89))

# ============================================================================
# the stacks: full (tucked behind the head) where the top is free, compact under a window
# ============================================================================
cap([("kiểu nó", "s"), ("tự mở web", "aqua")], CAP_W, near=T_WEB0)
cap([("xong rồi", "s"), ("tự bấm", "orange")], CAP_W)
cap([("tự gõ", "white"), ("được nha", "s", IN)], CAP_W, t_out=T_WEB1 + 0.02)
G.group([("thì đấy là", "s"), ("làm sao", "red", {"size": 250}), ("mà nó làm được như thế?", "s", {"free": True})],
        near=T_ASK0, t_out=T_ASK1 - 0.02)
G.group([("Playwright", "blue", {"size": 215, "t": T_FLY + FLY - 0.04, "free": True}),
         ("thư viện của Microsoft", "s", {"free": True, "inline": True})],
        near=T_PW, t_in=T_FLY + FLY - 0.06)
G.group([("là nó thao tác", "s"), ("trên trình duyệt", "s"), ("như người", "orange", {"size": 230})], near=T_HUM0,
        t_out=T_HUM1 + 0.02)
cap([("ví dụ em muốn tạo ra", "s"), ("một kịch bản", "aqua")], CAP_M, near=T_SC0)
cap([("để đăng nhập vào", "s"), ("một phần mềm", "white")], CAP_M)
cap([("bước 1", "s"), ("mở đường link", "orange")], CAP_M, near=beat_start("step1") + 0.4)
cap([("bước 2", "s"), ("điền username", "aqua")], CAP_M)
cap([("bước 3", "s"), ("nhập password", "orange")], CAP_M)
cap([("bước 4", "s"), ("ấn nút login", "aqua")], CAP_M)
cap([("mỗi lần cần đăng nhập lại", "s"), ("chỉ run lại", "red")], CAP_M, near=T_RR0)
cap([("kịch bản đấy thôi", "s"), ("là xong", "white")], CAP_M, t_out=T_RR1 + 0.02)
G.group([("nhưng mà AI nó có", "s"), ("nhìn được đâu?", "red")], near=T_SEE0)
G.group([("sao nó lại", "s"), ("bấm vào được?", "orange")], t_out=G_SEE[1] - 0.02)
cap([("nó không", "s"), ("chụp ảnh màn hình", "red")], CAP_M, near=T_CODE0)
cap([("để nó tìm", "s"), ("cái nút này", "white")], CAP_M)
cap([("nó", "s"), ("đọc cái mã", "aqua")], CAP_M)
cap([("của cái", "s"), ("trang web", "white")], CAP_M)
cap([("về cơ bản là nó", "s"), ("đọc mã", "aqua")], CAP_M, near=beat_start("nolook"))
cap([("nhưng", "s"), ("không nhìn", "red")], CAP_M, t_out=T_NL1 + 0.02)
G.group([("em muốn nhắn tin", "s"), ("cho bạn em", "s"), ("từ Zalo", "blue", {"size": 230})], near=T_Z0,
        t_out=T_ZWIN - 0.05)
cap([("em có thể đăng nhập", "s"), ("Zalo web", "aqua")], CAP_M, near=T_ZWIN)
cap([("ở trên", "s"), ("trình duyệt", "white")], CAP_M)
cap([("sau đó em cũng", "s"), ("tìm người", "orange")], CAP_M)
cap([("có tên là", "s"), ("ABC", "aqua")], CAP_M)
cap([("và em", "s"), ("nhắn tin", "orange")], CAP_M)
cap([("Playwright nó", "s"), ("làm được", "white")], CAP_M, t_out=T_Z1 + 0.02)
G.group([("tất nhiên", "s"), ("lần đầu", "white")], near=T_F0)
G.group([("em phải dùng AI", "s"), ("để tạo", "s"), ("kịch bản", "aqua")])
G.group([("từ lần sau", "orange")], near=beat_start("brain"))
G.group([("kịch bản chạy", "s"), ("tự động", "aqua")])
G.group([("có thể sẽ không dùng đến", "s"), ("bộ não AI", "red")])
G.group([("vì nó đã có kịch bản rồi", "s"), ("đâu cần nghĩ", "white"), ("nữa", "s", IN)], t_out=T_B1 + 0.02)
cap([("em muốn gửi tin nhắn cho", "s"), ("20 người", "orange")], CAP_M, near=T_T0)
cap([("đơn giản nó chạy kịch bản", "s"), ("20 lần", "aqua")], CAP_M, t_out=T_T1 + 0.02)
G.group([("em dùng Playwright thì", "s"), ("tiết kiệm", "aqua"), ("token", "k2")], near=T_V0, t_out=T_V1 + 0.02)
cap([("các bạn muốn tải về", "s"), ("cái skill", "aqua")], CAP_W, near=T_Q0)
cap([("để sử dụng Playwright", "s"), ("điều khiển Zalo", "orange")], CAP_W)
cap([("thì có thể", "s"), ("comment", "white")], CAP_W, near=A["q_comment"] - 0.6)
cap([("Playwright", "orange"), ("ở phần comment nhá", "s", IN)], CAP_W, near=A["q_pw2"] - 0.1, t_out=T_Q1 + 0.02)
G.group([("cái chữ đó", "s"), ("rất khó viết", "red"), ("đúng", "s", IN)], near=T_G0, t_out=S.DUR + 0.04)
G.event(hidden=lambda t: curtain(t) >= 0.9 or (T_REV0 <= t < T_FLY + FLY - 0.08) or t < T_COLD)

# ============================================================================
# the story bar: how much is left
# ============================================================================
PARTS = [(0.0, T_REV0), (T_REV0, T_SC0), (T_SC0, T_SEE0), (T_SEE0, T_Z0), (T_Z0, T_Q0), (T_Q0, S.DUR)]


@ev(T_COLD, S.DUR + 0.05)
def bar(ctx, t):
    if T_REV0 - 0.05 <= t < T_FLY + FLY:
        return
    FX.story_bar(ctx, t, PARTS, T_COLD + 0.1, S.DUR + 0.05, y=256, fill=RS.AQUA)


# ============================================================================
# the end card: the title, the call, the joke, and the cursor that starts the loop again
# ============================================================================
T_END = S.DUR + 0.06
T_LOOP = TOTAL - 0.75
CUR_E = UI.Cursor([(T_END + 0.2, 900, 1500), (T_END + 3.3, 700, 1345), (T_LOOP, 540, 960)], clicks=[T_END + 3.3, T_LOOP],
                  move=0.5, t_in=T_END + 0.2, t_out=TOTAL + 1.0)


def _fade(t, t0, d=0.22):
    return ease_out_cubic(clamp01((t - t0) / d))


@card(T_END, TOTAL + 1.0, close=0.12, open_=0.0)
def end_card(ctx, t, t0, t1):
    L = ctx.ui
    c = L.c
    card_text(L, t, t0 + 0.08, t1, "Playwright", -420, kind="serif_k", size=170, gradient=(RS.BLUE[0], RS.BLUE[2]),
              track=0.0, push=0.02)
    card_text(L, t, t0 + 0.3, t1, "AI tự mở web · tự bấm · tự gõ", -340, kind="semi", size=40, rgb=(200, 208, 216),
              track=0.0)
    k = _fade(t, t0 + 0.7)
    if k > 0:
        f1, f2 = font("semi", 50), font("black", 96)
        s1 = "comment"
        RS.draw_word(c, s1, f1, W2 - f1.measureText(s1) / 2, 800 + (1 - k) * 14, 255 * k, RS.WHITE, shadow=0.0)
        kp = clamp01((t - (t0 + 0.9)) / 0.1)
        if kp > 0:
            s2 = "“Playwright”"
            pop = 1.0 + 0.25 * (1 - ease_out_back(clamp01((t - (t0 + 0.9)) / 0.24)))
            c.save()
            c.translate(W2, 880)
            c.scale(pop, pop)
            c.translate(-W2, -880)
            RS.draw_word(c, s2, f2, W2 - f2.measureText(s2) / 2, 912, 255 * kp, RS.ORANGE, shadow=0.0)
            c.restore()
        k3 = _fade(t, t0 + 1.25)
        if k3 > 0:
            s3 = "nhận skill Playwright điều khiển Zalo"
            RS.draw_word(c, s3, f1, W2 - f1.measureText(s3) / 2, 1000 + (1 - k3) * 14, 255 * k3, RS.WHITE, shadow=0.0)
            s4 = "(viết sai chính tả cũng được)"
            f4 = font("medium", 34)
            RS.draw_word(c, s4, f4, W2 - f4.measureText(s4) / 2, 1056, 200 * _fade(t, t0 + 1.6), (170, 180, 195), shadow=0.0)
    k5 = _fade(t, t0 + 2.2)
    if k5 > 0:
        f5 = font("semi", 46)
        s5 = "AI bấm giúp bạn mọi nút…"
        RS.draw_word(c, s5, f5, W2 - f5.measureText(s5) / 2, 1250 + (1 - k5) * 14, 235 * k5, (220, 228, 236), shadow=0.0)
    k6 = clamp01((t - (t0 + 2.9)) / 0.1)
    if k6 > 0:
        f6 = font("black", 84)
        s6 = "trừ nút follow"
        w6 = f6.measureText(s6)
        pr = 1.0 if 0 <= t - (T_END + 3.3) < 0.13 else 0.0
        pop = (1.0 + 0.2 * (1 - ease_out_back(clamp01((t - (t0 + 2.9)) / 0.24)))) * (1 - 0.05 * pr)
        c.save()
        c.translate(W2, 1340)
        c.scale(pop, pop)
        c.translate(-W2, -1340)
        c.drawRRect(UI.rr(W2 - w6 / 2 - 44, 1282, W2 + w6 / 2 + 44, 1400, 59), skia.Paint(AntiAlias=True, Color=UI.c4(RS.AQUA, 255 * k6)))
        RS.draw_word(c, s6, f6, W2 - w6 / 2, 1370, 255 * k6, (10, 14, 22), shadow=0.0)
        c.restore()
    # the loop: the cursor presses the middle of the frame and the blue of the first frame comes back
    if t >= T_LOOP:
        kl = ease_in_cubic(tp(t, T_LOOP + 0.05, TOTAL - 0.02))
        c.drawCircle(540, 960, 2300 * kl, skia.Paint(AntiAlias=True, Color=UI.c4(DEEP, 255)))
    L.mark(0, 200, W, 1700)
    CUR_E.draw(L, t)


cue(T_END + 0.05, "whoosh", 0.3, length=0.45, direction=-1)
cue(T_END + 0.9, "pop", 0.3, f1=MS.note(82))
cue(T_END + 2.9, "pop", 0.32, f1=MS.note(85))
cue(T_END + 3.3, "click", 0.7)
cue(T_LOOP, "click", 0.8)
cue(T_LOOP + 0.3, "whoosh", 0.5, length=0.6, direction=1)

# ============================================================================
# music: the Trap Banger, cut on its bars (as in tập 14-15). First hits: bar 36 +0.02, bar 12 +0.017, bar 44 +0.04 s
# ============================================================================


def BB(n):
    return TM.bar_of("banger", n)


DROP36 = BB(36) + 0.02
BARL = TM.TRACKS["banger"][2]
T_BUILD = T_ASK0
T_MSTOP = T_PW - 0.07
T_ZMUS = T_Z0

score("hit", 0.0, gain=0.42, length=2.0)                    # boom 1 of 2: the first frame (soft: she speaks at 0.14 s)
score("subdrop", 0.0, gain=0.4, length=1.0)
score("crash", 0.0, gain=0.25)
# the hook on the track's drop, through "tự mở web… tự gõ"
score("track", 0.0, track="banger", src_t=DROP36, dur=T_BUILD + 0.02, fade_in=0.004, fade_out=0.03)   # full duck: her words first
# the question: the same bars on with the bass draining away; under "AI dùng thư viện…" a roll, a stutter, a riser
score("track", T_BUILD, track="banger", src_t=DROP36 + T_BUILD, dur=T_MSTOP - T_BUILD, fade_in=0.02, fade_out=0.015,
      hp=(20, 900, 1.6), light=True)
score("roll", T_MSTOP, length=min(1.5, T_MSTOP - T_REV0 + 0.2), gain=0.7, bpm=96.69)
score("stutter", T_MSTOP - 0.3, length=0.28, gain=0.4)
score("riser", T_MSTOP, length=1.7, gain=0.38)
# "Playwright": the brightest part of the track (bar 44) with the second boom, through "như người"
score("track", T_PW, track="banger", src_t=BB(44) + 0.04, dur=T_MEAN0 - T_PW + 0.02, fade_in=0.004, fade_out=0.04,
      light=True)
score("hit", T_PW, gain=0.72, length=2.0)                   # boom 2 of 2
score("crash", T_PW, gain=0.42)
# the dictionary card over the melody alone (bar 32)
score("track", T_MEAN0, track="banger", src_t=BB(32), dur=T_SC0 - T_MEAN0 + 0.02, fade_in=0.05, fade_out=0.03, light=True)
# the script: the beat from a phrase start (bar 4), through the four steps and the replays
score("track", T_SC0, track="banger", src_t=BB(4), dur=T_SEE0 - T_SC0 + 0.02, fade_in=0.004, fade_out=0.05, light=True)
# her question over the nearly empty bar 35, then nothing in the gap
score("track", T_SEE0, track="banger", src_t=BB(33), dur=G_SEE[0] - T_SEE0, fade_in=0.05, fade_out=0.02, light=True)
score("riser", G_SEE[1], length=1.2, gain=0.3)
# "nó không chụp ảnh màn hình": the melody; the drop (bar 36) lands with the scan on "đọc cái mã"
score("track", T_CODE0, track="banger", src_t=DROP36 - (T_SCAN[0] - T_CODE0), dur=T_SCAN[0] - T_CODE0 + 0.01, fade_in=0.05,
      fade_out=0.01, light=True)
score("track", T_SCAN[0], track="banger", src_t=DROP36, dur=T_F0 - T_SCAN[0] + 0.02, fade_in=0.004, fade_out=0.06,
      light=True)
score("crash", T_SCAN[0], gain=0.4)
# "lần đầu… từ lần sau…": the break again, placed so that its drop lands on "20 người"
T_D20 = A["t_20"] - 0.04
score("track", T_F0, track="banger", src_t=DROP36 - (T_D20 - T_F0), dur=T_D20 - T_F0 + 0.01, fade_in=0.3, fade_out=0.01,
      light=True)
score("track", T_D20, track="banger", src_t=DROP36, dur=T_Q0 - T_D20 + 0.02, fade_in=0.004, fade_out=0.08, light=True)
score("crash", T_D20, gain=0.4)
# her call over the melody alone, so the typing and the clicks are heard; a stop for his laugh
score("track", T_Q0, track="banger", src_t=BB(32), dur=T_G0 - T_Q0 - 0.05, fade_in=0.08, fade_out=0.12, light=True)
# the end card: the beat (bar 12), fading out
score("track", T_END, track="banger", src_t=BB(12) + 0.017, dur=TOTAL - T_END, fade_in=0.004, fade_out=1.2, light=True)
score("crash", T_END, gain=0.36)
FX.beat_pulses(T_PW + BEAT, 3, BEAT, amt=0.014)
FX.beat_pulses(T_D20 + BEAT, 3, BEAT, amt=0.014)
