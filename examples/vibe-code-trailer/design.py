"""Vibe code là gì? as a movie trailer for TikTok (9:16, 55 s): the worked example of references/trailer.md.

A hook with a black "RỐT CUỘC" card over her question; the old way as a montage (a step counter, a word and a drum
hit on every cut, the room dimmed, a clock speeding up, a rewind on "quay lại"); a date card; the question; the
old process collapsing; a punchline card; a fast escalation; then the twist (the prompt this trailer started from,
typing itself) and the title. The kit is scripts/trailer.py, the score scripts/trailer_score.py.
"""
import math

from story import *
from trailer import *
from trailer_score import BB_MAJ, D_MAJ, D_MIN

for key, word, near in [
    ("khoe", "khoe", 0.9), ("vibe1", "vibe", 1.66), ("thamchi", "thậm", 3.45), ("crm", "CRM", 4.47),
    ("thi_q", "thì", 5.15), ("rot", "rốt", 5.54), ("vibe_q", "vibe", 6.16), ("gi", "gì", 6.80),
    ("muon", "muốn", 8.72), ("mota", "mô", 10.34), ("y_tuong", "ý", 10.78), ("dac", "đặc", 12.60),
    ("wire", "wireframe", 14.56), ("uiux", "UI", 16.25), ("code5", "code", 18.12), ("frontend", "frontend", 18.76),
    ("backend", "backend", 19.44), ("test7", "Test", 20.21), ("nguoi8", "người", 22.62), ("quay", "quay", 23.98),
    ("sua", "sửa", 24.82), ("rat", "rất", 25.86), ("gian", "gian", 26.86),
    ("thuat", "thuật", 28.77), ("nha", "nhà", 30.76), ("openai", "OpenAI", 31.62),
    ("vay", "Vậy", 33.13), ("vibe_a", "vibe", 34.29), ("sao", "sao", 34.87),
    ("la_r", "Là", 35.86), ("triet", "triệt", 36.16), ("tieu", "tiêu", 36.44), ("giua", "giữa", 37.96),
    ("y2", "ý", 38.96), ("tieng", "tiếng", 40.90), ("voi", "với", 42.00),
    ("ai", "AI", 42.92), ("lam", "làm", 43.32), ("browser", "browser", 45.18), ("chup", "chụp", 46.22),
    ("test_s", "test", 46.84), ("ket", "kết", 47.91),
]:
    A[key] = at(word, near)


def c0(beat):
    return min(c["out_in"] for c in CLIPS if c["beat"] == beat)


def c1(beat):
    return max(c["out_out"] for c in CLIPS if c["beat"] == beat)


KEYS.update({
    "vibe code": ("xbold", MINT, 1.0), "crm": ("xbold", WHITE, 1.0), "rốt cuộc": ("serif_ib", AMBER, 1.15),
    "ý tưởng": ("serif_ib", AMBER, 1.15), "đặc tả": ("xbold", SKY, 1.0), "wireframe": ("xbold", SKY, 1.0),
    "ui/ux": ("xbold", SKY, 1.0), "frontend": ("xbold", SKY, 1.0), "backend": ("xbold", SKY, 1.0),
    "quay lại": ("serif_ib", CORAL, 1.1), "mất thời gian": ("serif_ib", CORAL, 1.1), "openai": ("xbold", WHITE, 1.0),
    "triệt tiêu": ("serif_ib", CORAL, 1.15), "tiếng việt": ("serif_ib", AMBER, 1.15), "ai làm": ("xbold", MINT, 1.0),
    "tự test": ("serif_ib", MINT, 1.15), "kết quả": ("serif_ib", GOLD, 1.15),
})
KEEP_CASE.update({"crm": "CRM", "openai": "OpenAI", "uiux": "UI/UX"})
NO_BREAK.update({"OpenAI", "CRM", "UI/UX", "AI"})
COMPOUNDS.update({"vibe code", "phần mềm", "ý tưởng", "tài liệu", "đặc tả", "yêu cầu", "giao diện", "thiết kế",
                  "người dùng", "kịch bản", "nội bộ", "quay lại", "thời gian", "thuật ngữ", "sáng lập", "triệt tiêu",
                  "công đoạn", "tiếng việt", "nói chuyện", "lập tức", "toàn bộ", "còn lại", "màn hình", "kết quả",
                  "cuối cùng", "rốt cuộc", "thậm chí", "đầu tiên"})

PUNCHES.extend([(A["crm"], 0.035, 0.08, 0.3, 0.5), (A["gi"], 0.045, 0.06, 0.4, 0.6), (A["rat"], 0.045, 0.08, 0.5, 0.6),
                (A["openai"], 0.035, 0.1, 0.4, 0.6), (A["vibe_a"], 0.04, 0.12, 0.5, 0.5), (A["tieng"], 0.045, 0.06, 0.4, 0.6),
                (A["ai"], 0.045, 0.06, 0.4, 0.6), (A["ket"], 0.045, 0.06, 0.5, 0.5)])
PIP_IN, PIP_OUT = A["sao"] + 0.12, c1("reveal") - 0.25
PIP.append((PIP_IN, PIP_OUT))

STEEL = (178, 198, 222)
DUSK = (255, 150, 132)
G_Q, G_LOOP, G_ASK, G_IDEA = gap("question"), gap("loop"), gap("ask"), gap("idea")
top_fade()


# ============================================================================
# ACT I: the buzz. Reads as one sentence across the beats: VIBE CODE ... RỐT CUỘC ... LÀ GÌ?
# ============================================================================
@ev(0.0, c1("crm"))
def buzz(ctx, t):
    kicker(ctx.front, t, 0.12, A["vibe1"] - 0.15, "DỰA TRÊN MỘT CUỘC TRÒ CHUYỆN CÓ THẬT", W / 2, 318, size=31,
           rgb=WHITE, kind="bold", tracking=0.2)
    depth_word(ctx, t, A["vibe1"] - 0.08, c1("hook") - 0.03, "VIBE CODE", size=235, gradient=(WHITE, (200, 255, 236)),
               enter="settle", stagger=0.04, fade_out=0.07, sheen=0.55)
    chip(ctx.front, t, A["crm"] - 0.06, c1("crm") - 0.02, W / 2, 330, "cả CRM", "database", style="glow", size=40,
         accent=AMBER)


K1 = (A["rot"] - 0.06, A["vibe_q"] - 0.07)


@card(*K1, close=0.10, open_=0.16)          # over her words: voice over black
def k_rotcuoc(ctx, t, t0, t1):
    card_text(ctx.ui, t, t0, t1, "RỐT CUỘC", 40, kind="black", size=124, track=0.05)


@ev(A["vibe_q"] - 0.2, c1("question"))
def question(ctx, t):
    depth_word(ctx, t, A["vibe_q"] - 0.05, c1("question") - 0.1, "LÀ GÌ?", size=280, kind="serif_ib", rgb=AMBER,
               tracking=0.0, enter="pop", stagger=0.05, fade_out=0.1, glow=(255, 170, 60))


@card(*G_Q)
def k_truocday(ctx, t, t0, t1):
    r = card_text(ctx.ui, t, t0, t1, "TRƯỚC ĐÂY", 30, kind="semi", size=84, track=0.34, delay=0.12)
    if r is not None:
        k = ease_in_out_cubic(clamp01((t - t0 - 0.3) / 0.6))
        ctx.ui.c.drawLine(W / 2 - 150 * k, H / 2 + 80, W / 2 + 150 * k, H / 2 + 80,
                          stroke(AMBER, 200 * env(t, t0, t1, 0.2, 0.08), width=2.5))


# ============================================================================
# ACT II: the old way. Dimmed room, a step counter, a word slammed on every cut, then the loop back.
# ============================================================================
dim_room(c0("s1_idea") - 0.4, c1("loop") + 0.3, 100)

STEPS = [  # (time, step number, word, beat)
    (A["mota"] - 0.05, 1, "Ý TƯỞNG", "s1_idea"), (c0("s2_spec"), 2, "ĐẶC TẢ", "s2_spec"),
    (c0("s3_wire"), 3, "WIREFRAME", "s3_wire"), (c0("s4_ui"), 4, "UI/UX", "s4_ui"),
    (c0("s5_code"), 5, "CODE", "s5_code"), (c0("s6_fb"), 6, "FRONTEND", "s6_fb"),
    (c0("s7_test"), 7, "TEST", "s7_test"), (c0("s8_user"), 8, "NGƯỜI DÙNG", "s8_user"),
]


@ev(c0("s1_idea") - 0.4, c1("s8_user"))
def steps(ctx, t):
    for (ts, n, word, beat) in STEPS:
        t0 = A["y_tuong"] - 0.08 if n == 1 else ts + 0.02
        t1 = c1(beat) - 0.04
        if n == 6:      # "tách thành frontend và backend": two words on one cut
            depth_word(ctx, t, t0, A["backend"] - 0.06, "FRONTEND", size=225, gradient=(WHITE, STEEL), enter="pop",
                       stagger=0.022, fade_out=0.05)
            depth_word(ctx, t, A["backend"] - 0.04, t1, "BACKEND", size=225, gradient=(WHITE, STEEL), enter="pop",
                       stagger=0.022, fade_out=0.05)
            continue
        depth_word(ctx, t, t0, t1, word, size=pick(250, 235), gradient=(WHITE, GOLD if n == 1 else STEEL), enter="pop",
                   stagger=0.025, fade_out=0.05, sheen=0.35 if n == 1 else None)


LOOP0 = A["quay"] - 0.05
HUD_T0, HUD_T1 = A["mota"] - 0.12, c1("loop") - 0.06


def hud_fill(t):
    """filled segments (float) and whether the loop back has started."""
    if t < LOOP0:
        return float(max([n for (ts, n, _w, _b) in STEPS if t >= ts] or [0])), False
    pts = [(LOOP0, 8.0), (LOOP0 + 0.6, 2.0), (A["sua"] + 0.1, 2.0), (A["sua"] + 1.0, 8.0), (A["sua"] + 1.4, 2.0),
           (A["sua"] + 1.85, 8.0), (A["sua"] + 2.15, 2.0), (A["sua"] + 2.45, 8.0)]
    for (ta, va), (tb, vb) in zip(pts, pts[1:]):
        if t <= tb:
            return lerp(va, vb, ease_in_out_cubic(clamp01((t - ta) / max(1e-3, tb - ta)))), True
    return pts[-1][1], True


def clock_icon(c, x, y, r, t, speed, rgb, a):
    c.drawCircle(x, y, r, stroke(rgb, a, width=3))
    ang = 2 * math.pi * t * speed
    c.drawLine(x, y, x + 0.78 * r * math.sin(ang), y - 0.78 * r * math.cos(ang), stroke(rgb, a, width=3))
    c.drawLine(x, y, x + 0.5 * r * math.sin(ang / 12), y - 0.5 * r * math.cos(ang / 12), stroke(rgb, a, width=3))


@ev(HUD_T0, HUD_T1 + 0.1)
def hud(ctx, t):
    """BƯỚC 01..08 with eight segments (the length of the process); the loop back rewinds it, again and again."""
    v = env(t, HUD_T0, HUD_T1, 0.25, 0.12)
    if v <= 0:
        return
    L = ctx.front
    c = L.c
    fn, looping = hud_fill(t)
    rgb = CORAL if looping else AMBER
    if t >= A["rat"] - 0.1:
        label = "LẠI TỪ ĐẦU"
    elif t >= LOOP0 + 0.6:
        label = "SỬA LẠI"
    else:
        label = f"BƯỚC {max(1, int(math.ceil(fn - 0.02))):02d}"
    ts = max([s[0] for s in STEPS if s[0] <= t] or [HUD_T0])
    pk = 1.0 + 0.16 * (1 - ease_out_cubic(clamp01((t - ts) / 0.22))) if not looping else 1.0
    f = font("bold", 40)
    tw = text_width(label, f, 0.24 * 40)
    draw_text(L, label, f, W / 2 + 28, 320, rgb=rgb, a=255 * v, tracking=0.24 * 40, scale=pk, shadow=8, shadow_a=170)
    clock_icon(c, W / 2 + 28 - tw / 2 - 40, 306, 17, t, 3.5 if looping else 0.8, rgb, 235 * v)
    sw, gp = 86, 12
    x0 = W / 2 - (8 * sw + 7 * gp) / 2
    for i in range(8):
        xa = x0 + i * (sw + gp)
        c.drawRRect(rrect(xa, 350, xa + sw, 362, 6), fill(WHITE, 70 * v))
        part = clamp01(fn - i)
        if part > 0:
            c.drawRRect(rrect(xa, 350, xa + sw * part, 362, 6), fill(rgb, 240 * v))
            c.drawRRect(rrect(xa, 350, xa + sw * part, 362, 6), fill(rgb, 90 * v, blur=6))
    L.mark(x0 - 70, 270, W - x0 + 20, 376)


@ev(A["quay"] - 0.2, c1("loop"))
def loop_back(ctx, t):
    depth_word(ctx, t, A["quay"] - 0.06, A["rat"] - 0.12, "QUAY LẠI", size=270, kind="serif_ib", rgb=CORAL, tracking=0.0,
               enter="pop", stagger=0.04, fade_out=0.08, glow=(255, 90, 70))
    depth_word(ctx, t, A["rat"] - 0.08, c1("loop") - 0.02, "MẤT THỜI GIAN", size=230, gradient=(WHITE, DUSK), enter="pop",
               stagger=0.03, fade_out=0.05)


@card(*G_LOOP, close=0.18, open_=0.26)
def k_name(ctx, t, t0, t1):
    card_text(ctx.ui, t, t0, t1, "THÁNG 2 · 2025", -82, kind="bold", size=40, rgb=AMBER, track=0.34, delay=0.08)
    card_text(ctx.ui, t, t0, t1, "MỘT CÁI TÊN", 52, kind="black", size=112, track=0.03, delay=0.24)
    card_text(ctx.ui, t, t0, t1, "ra đời.", 180, kind="serif_ib", size=120, rgb=GOLD, track=0.0, delay=0.62,
              glow=(255, 170, 60))


# ============================================================================
# ACT III: the name, the question, the collapse
# ============================================================================
@ev(c0("origin") - 0.05, c1("origin"))
def origin(ctx, t):
    t1 = c1("origin") - 0.08
    depth_word(ctx, t, A["thuat"] - 0.02, t1, "VIBE CODING", size=225, gradient=(WHITE, (200, 255, 236)), enter="settle",
               stagger=0.04, fade_out=0.1, sheen=0.6)
    chip(ctx.front, t, A["nha"] - 0.06, t1, W / 2, 312, "Andrej Karpathy", "user", style="glow", size=40, accent=AMBER)
    chip(ctx.front, t, A["openai"] - 0.06, t1, W / 2, 408, "đồng sáng lập OpenAI", None, style="dark", size=34)


ROWS = [("01", "Ý tưởng"), ("02", "Đặc tả"), ("03", "Wireframe"), ("04", "UI/UX"), ("05", "Code"),
        ("06", "Frontend · Backend"), ("07", "Test"), ("08", "Người dùng")]


@ev(PIP_IN, PIP_OUT + 0.1)
def collapse(ctx, t):
    """the eight steps again; the six in the middle are struck on "triệt" and thrown out on "tiêu"."""
    t0, t1 = PIP_IN + 0.3, PIP_OUT
    h = 540
    v, dy, x0, y0, x1, y1 = panel(ctx, t, t0, t1, h)
    if v <= 0:
        return
    L = ctx.mid
    c = L.c
    cx = (x0 + x1) / 2
    e = ease_in_out_cubic(clamp01((t - (A["tieu"] + 0.08)) / 0.6))
    hk = clamp01((e - 0.55) / 0.45)
    draw_text(L, "QUY TRÌNH CŨ", font("bold", 32), cx, y0 + 62 + dy, rgb=AMBER, a=255 * v * (1 - hk), tracking=0.3 * 32)
    draw_text(L, "VIBE CODE", font("black", 46), cx, y0 + 66 + dy, rgb=MINT, a=255 * v * hk, tracking=0.12 * 46,
              glow=MINT, glow_a=90 * hk)
    row_h, pw = 54, 300
    top = y0 + 122 + dy
    mid_y = top + 3.5 * row_h
    for i, (num, lab) in enumerate(ROWS):
        ki = clamp01((t - (t0 + 0.04 * i)) / 0.25)
        if ki <= 0:
            continue
        yf = top + i * row_h
        middle = 0 < i < 7
        xo = 0.0
        if middle:      # thrown out sideways, alternating
            y = yf
            ex = ease_in_cubic(clamp01((t - (A["tieu"] + 0.02 * i)) / 0.42))
            xo = (1 if i % 2 else -1) * 760 * ex
            a = 255 * v * ki * (1 - ex)
        else:           # the idea and the user slide together
            y = lerp(yf, mid_y + (-118 if i == 0 else 118), e)
            a = 255 * v * ki
        if a <= 1:
            continue
        struck = middle and t >= A["triet"] + 0.035 * (i - 1)
        acc = CORAL if struck else (AMBER if not middle else WHITE)
        rx0, rx1 = cx - pw + xo, cx + pw + xo
        c.drawRRect(rrect(rx0, y - 23, rx1, y + 23, 23), fill(INK, 0.66 * a))
        c.drawRRect(rrect(rx0, y - 23, rx1, y + 23, 23), stroke(acc, 0.55 * a, width=1.8))
        draw_text(L, num, font("black", 27), rx0 + 30, y + 10, rgb=acc, a=a, align="left")
        draw_text(L, lab, font("semi", 35), rx0 + 92, y + 12, rgb=WHITE, a=a, align="left")
        if struck:
            k = ease_in_out_cubic(clamp01((t - (A["triet"] + 0.035 * (i - 1))) / 0.2))
            c.drawLine(rx0 + 16, y, rx0 + 16 + (2 * pw - 32) * k, y, stroke(CORAL, a, width=4.5))
    if e > 0.35:
        k = clamp01((e - 0.35) / 0.65)
        ya, yb = mid_y - 88, mid_y + 88
        c.drawLine(cx, ya, cx, lerp(ya, yb, k), stroke(MINT, 110 * v * k, width=12, blur=8))
        c.drawLine(cx, ya, cx, lerp(ya, yb, k), stroke(MINT, 255 * v, width=5))
        if k >= 1:
            c.drawLine(cx, yb, cx - 13, yb - 15, stroke(MINT, 255 * v, width=5))
            c.drawLine(cx, yb, cx + 13, yb - 15, stroke(MINT, 255 * v, width=5))
    if t >= A["giua"] - 0.1:
        g = clamp01((t - (A["giua"] - 0.1)) / 0.4)
        draw_text(L, "chỉ còn 2 bước", font("serif_ib", 50), cx + 36, mid_y + 16, rgb=MINT, a=255 * v * g, align="left")
    L.mark(x0, y0 + dy, x1, y1 + dy)


# ============================================================================
# ACT IV: the punchline card and the escalation
# ============================================================================
@ev(c0("idea") - 0.1, c1("idea"))
def idea(ctx, t):
    depth_word(ctx, t, A["y2"] - 0.1, c1("idea") - 0.04, "MỘT Ý TƯỞNG", size=230, gradient=(WHITE, GOLD), enter="pop",
               stagger=0.03, fade_out=0.05)


@card(*G_IDEA, close=0.14, open_=0.2)
def k_lang(ctx, t, t0, t1):
    card_text(ctx.ui, t, t0, t1, "NGÔN NGỮ LẬP TRÌNH", -2, kind="semi", size=58, track=0.2, delay=0.05)
    card_text(ctx.ui, t, t0, t1, "mới nhất là…", 128, kind="serif_ib", size=108, rgb=AMBER, track=0.0, delay=0.34,
              glow=(255, 170, 60))


@ev(c0("viet") - 0.05, DUR)
def escalate(ctx, t):
    depth_word(ctx, t, A["tieng"] - 0.07, c1("viet") - 0.04, "TIẾNG VIỆT", size=250, gradient=(WHITE, AMBER), enter="scale",
               fade_out=0.05, sheen=0.35)
    depth_word(ctx, t, A["ai"] - 0.08, c1("ai") - 0.04, "AI", size=330, gradient=(WHITE, MINT), enter="pop", fade_out=0.05,
               sheen=0.4)
    kicker(ctx.front, t, A["lam"] - 0.05, c1("ai") - 0.06, "LÀM TOÀN BỘ PHẦN CÒN LẠI", W / 2, 322, size=32, rgb=MINT, kind="bold")
    t1 = c1("selftest") - 0.04
    for j, (tt, lab, ic, acc) in enumerate(((A["browser"], "mở browser", "browser", SKY), (A["chup"], "chụp màn hình", "camera", SKY),
                                            (A["test_s"], "tự test", "check", MINT))):
        chip(ctx.front, t, tt - 0.1, t1, W / 2, 300 + j * 102, lab, ic, style="glow", size=42, accent=acc)
    depth_word(ctx, t, A["ket"] - 0.1, DUR - 0.01, "KẾT QUẢ", size=255, gradient=(WHITE, GOLD), enter="scale", fade_out=0.02,
               sheen=0.3)


for beat_ in ("viet", "ai", "selftest", "result"):
    flash(c0(beat_))


# ============================================================================
# EPILOGUE: the twist (the request this trailer started from, typing itself), then the title
# ============================================================================
PROMPT = ("Làm thêm 1 video dọc để đăng TikTok cho video vibe code là gì, nhưng đổi phong cách giống trailer phim, "
          "có nhịp điệu thu hút và twist.")
BOX_T, TYPE_T0, TYPE_T1, ENTER_T = DUR + 0.40, DUR + 0.58, DUR + 2.35, DUR + 2.48
LINE_T, TITLE_T = DUR + 2.66, DUR + 4.30


@card(DUR, TOTAL + 1, close=0.0, open_=0.0)     # a hard cut to black on the last word
def k_end(ctx, t, t0, t1):
    L = ctx.ui
    if t < TITLE_T:
        prompt_box(L, t, PROMPT, BOX_T, TYPE_T0, TYPE_T1, ENTER_T, TITLE_T - 0.14)
        card_text(L, t, LINE_T, TITLE_T - 0.13, "Trailer bạn vừa xem", -240, kind="semi", size=50, track=0.04, push=0.0)
        card_text(L, t, LINE_T, TITLE_T - 0.13, "bắt đầu từ đúng câu này.", -148, kind="serif_ib", size=70, rgb=AMBER,
                  track=0.0, delay=0.3, push=0.0, glow=(255, 170, 60))
    title_slam(L, t, TITLE_T, "VIBE CODE", sub="Mô tả bằng lời. AI làm phần còn lại.")


flash(TITLE_T)


# ============================================================================
# sound: small cues on top, and the trailer score
# ============================================================================
cue(A["crm"] - 0.06, "pop", 0.45, f0=600, f1=1150)
cue(A["vibe1"] - 0.08, "whoosh", 0.45, length=0.5, direction=1)
cue(A["quay"] - 0.05, "rewind", 0.55)
for i_ in range(len(ROWS)):
    cue(PIP_IN + 0.3 + 0.04 * i_, "tick", 0.3, f=1700 + 110 * i_)
cue(A["triet"], "swipe", 0.6)
cue(A["tieu"] + 0.08, "whoosh", 0.5, length=0.6, direction=1)
cue(A["giua"] - 0.1, "shimmer", 0.45)
cue(A["nha"] - 0.06, "pop", 0.4, f0=520, f1=1000)
cue(A["openai"] - 0.06, "pop", 0.35, f0=600, f1=1150)
cue(A["browser"] - 0.1, "click", 0.5)
cue(A["chup"] - 0.1, "shutter", 0.45)
cue(A["test_s"] - 0.1, "ding", 0.35, f=1567.98)
cue(TYPE_T0, "typing", 1.0, until=TYPE_T1)
cue(ENTER_T, "click", 0.5)

CUTS2 = [c0(b) for b in ("s2_spec", "s3_wire", "s4_ui", "s5_code", "s6_fb", "s7_test", "s8_user")]
# act I: a boom as the bars slide in, a drone and a heartbeat under her question, a braam on "gì"
score("boom", 0.0)
score("pad", 0.0, notes=[38, 45, 50], dur=G_Q[0] + 0.2, gain=0.9, bright=0.12, att=0.25, rel=0.6)
score("heartbeat", 0.35, until=K1[0] - 0.2, bpm=72)
score("taiko", K1[0], gain=0.9, f0=140, f1=60)
score("boom", K1[0], gain=0.35, length=1.2)
score("braam", A["gi"] - 0.02, chord=D_MIN, length=3.2)
score("boom", A["gi"] - 0.02, gain=0.6)
# act II: a clock that doubles its speed, the i-VI-iv-V ostinato, a low drum hit on every step, a dissonant swell
# and a riser into a hard stop
score("clock", G_Q[0] + 0.25, until=c1("loop") - 0.02, bpm=100, fast_from=CUTS2[3], loud_from=A["quay"])
score("ostinato", c0("s1_idea"), until=A["quay"] - 0.05, bpm=100, fast_from=CUTS2[3])
score("taiko", A["y_tuong"] - 0.08, gain=0.5)
for k_, tc_ in enumerate(CUTS2):
    score("taiko", tc_, gain=0.45 + 0.03 * k_, f0=120 + 6 * k_, f1=55)
score("taiko", A["backend"] - 0.04, gain=0.45, f0=160, f1=80)
score("pad", A["quay"], notes=[38, 39, 45, 51], dur=c1("loop") - A["quay"] + 0.05, bright=0.35, att=1.6, rel=0.05, trem=0.35)
score("riser", c1("loop"), length=2.6, gain=0.9)
# act III: a braam on the date card, wonder under the name, tension under the question, a low braam on the collapse
score("braam", G_LOOP[0] + 0.14, chord=BB_MAJ, length=3.4)
score("boom", G_LOOP[0] + 0.14, gain=0.75)
o0, o1 = c0("origin"), c1("origin")
score("pad", o0 - 0.1, notes=[46, 50, 53, 58], dur=(o1 - o0) / 2 + 0.5, gain=0.8, bright=0.25, att=0.9, rel=1.2)
score("pad", o0 + (o1 - o0) / 2, notes=[41, 45, 48, 53], dur=(o1 - o0) / 2, gain=0.8, bright=0.25, att=0.8, rel=1.0)
score("pad", c0("ask"), notes=[57, 64, 69, 76], dur=G_ASK[1] - c0("ask") + 0.3, gain=0.9, bright=0.4, att=1.2, rel=0.35,
      trem=0.45)
score("swell", A["triet"], length=0.5)
score("braam", A["triet"] - 0.01, chord=D_MAJ, length=3.0, gain=0.38)    # under his key line: keep it low
score("boom", A["triet"] - 0.01, gain=0.65)
score("pad", A["triet"], notes=[50, 54, 57, 62], dur=G_IDEA[0] - A["triet"], gain=0.85, bright=0.3, att=0.2, rel=0.4)
score("bells", c0("idea") + 0.45, notes=[74, 78, 81, 86])
# act IV: a riser through the punchline card into "tiếng Việt", then the drive, a hit on every cut, a riser into black
score("riser", A["tieng"] - 0.02, length=A["tieng"] - G_IDEA[0], gain=0.9)
score("taiko", A["tieng"] - 0.03, gain=0.75, f0=150, f1=55)
score("boom", A["tieng"] - 0.03, gain=0.5, length=1.6)
score("drive", c0("viet") + 0.12, until=DUR, bpm=120)
for tc_ in (c0("ai"), c0("selftest"), c0("result")):
    score("taiko", tc_, gain=0.65, f0=135, f1=55)
score("riser", DUR, length=2.2)
# epilogue: silence on the cut, a quiet piano under the typing, then the title
score("piano", DUR, notes=[(0.35, 62), (0.85, 69), (1.35, 76), (1.85, 78), (2.75, 74), (3.25, 81)])
score("pad", DUR + 0.4, notes=[50, 57, 62, 66], dur=TITLE_T - DUR - 0.4, gain=0.5, bright=0.15, att=1.2, rel=0.2)
score("swell", TITLE_T, length=0.35, gain=0.8)
score("braam", TITLE_T - 0.01, chord=D_MIN + [50], length=3.4, gain=1.15)
score("boom", TITLE_T - 0.01, length=3.0)
score("crash", TITLE_T - 0.01, gain=0.9)
