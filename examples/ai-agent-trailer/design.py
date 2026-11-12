"""AI agent là gì? as a movie trailer for TikTok (9:16, 88 s), from a 3-minute talk between two people, shot on an
iPhone in HLG in direct sun and kept in the camera's own colour (the "iphone" look).

Her hook ("đại lý AI ạ?"); the Latin root spoken over black, word by word; "làm thay bạn"; "thời này vẫn chỉ dùng AI
để hỏi đáp"; a card into her question about ChatGPT and Claude; an ordinary day as a montage (hỏi, copy, sửa, gửi)
with a counter and a clock speeding up, ending on her face for "người thực tế đang làm là em"; AI telling you what
to write; something is off; the twist: the delegation arrow EM -> AI turns round to AI -> EM; her question; the
real agent in a fast drive (Excel and email go to AI, connected through MCP); the warm part (quét nhà, nấu cơm);
"đa số mới dừng ở hỏi đáp"; the title and a call to follow.

What it adds to examples/vibe-code-trailer, all from the user's notes on the first cut:
- no darkening anywhere (no top_fade, no dim_room): titles over the sky sit on pill_text() instead;
- every shot wide, no punch-ins; the cutaway to her face is a wide shot too;
- the good lines stay even past 60 s: the sweeping-and-cooking analogy is the part people remember;
- anchors come from word_in(beat, word), so a recut does not move them;
- the call to follow is a joke that lands the twist: "giao việc cho AI… trước khi AI giao thêm việc cho bạn";
- one design for both formats: on 16:9 the chips ride in the sky band (CHIP_Y), the step counter sits in the top
  letterbox bar, and the end card says "Đăng ký" and keeps its lower part free for YouTube's end-screen elements.
"""
import math

from story import *
from trailer import *
from trailer_score import BB_MAJ, D_MAJ, D_MIN

# word anchors in output seconds: (name, beat, word[, n-th]), looked up inside that beat's own clips
for name_, beat_, word_, *n_ in [
        ("dai", "hook", "đại"), ("latinh", "latin", "latinh"), ("no_l", "latin", "nó"), ("lam_l", "latin", "làm"),
        ("thuc_l", "latin", "thực"), ("day_l", "latin", "đẩy"), ("hanh_m", "meaning", "hành"),
        ("lam_m", "meaning", "làm"), ("hoi_p", "power", "hỏi"), ("chua_p", "power", "chưa"), ("suc_p", "power", "sức"),
        ("lam_p", "power", "làm"), ("chatgpt_q", "q_daily", "chatgpt"), ("claude_q", "q_daily", "claude"),
        ("agent_q", "q_daily", "agent"), ("hoi_a", "m_ask", "hỏi"), ("tra_a", "m_ask", "trả"),
        ("copy", "m_copy", "copy"), ("sua", "m_send", "sửa"), ("gui", "m_send", "gửi"), ("la_y", "you", "là"),
        ("edit", "edit", "edit"), ("ai_ed", "edit", "ai"), ("ban_ed", "edit", "bạn"), ("sai", "off", "sai"),
        ("em_t", "think", "em"), ("giao_t", "think", "giao"), ("ai_t", "think", "ai"), ("nhung", "twist", "nhưng"),
        ("ai_w", "twist", "ai"), ("giao_w", "twist", "giao"), ("em_w", "twist", "em"), ("the_nao", "q_real", "như"),
        ("hanh_a", "act", "hành"), ("lam_a", "act", "làm"), ("excel", "excel", "excel"), ("no_x", "excel", "nó"),
        ("khong_x", "excel", "không"), ("email", "email", "email"), ("ai_e", "email", "ai", 2),
        ("khong_e", "email", "không"), ("email_m", "mcp", "email"), ("excel_m", "mcp", "excel"),
        ("mcp", "mcp", "mcp"), ("quet", "analogy", "quét"), ("quet2", "analogy", "quét", 2), ("com", "analogy", "nấu"),
        ("com2", "analogy", "nấu", 2), ("thay_c", "analogy", "thay"), ("hoi_e", "end", "hỏi"),
        ("agent_e", "end", "agent")]:
    A[name_] = word_in(beat_, word_, *n_)


KEYS.update({
    "ai agent": ("xbold", MINT, 1.0), "agent": ("xbold", MINT, 1.0), "đại lý": ("serif_ib", AMBER, 1.15),
    "latinh": ("serif_ib", AMBER, 1.15), "làm thay": ("serif_ib", GOLD, 1.15), "hành động": ("xbold", MINT, 1.0),
    "chatgpt": ("xbold", WHITE, 1.0), "claude": ("xbold", WHITE, 1.0), "copy": ("xbold", SKY, 1.0),
    "word": ("xbold", SKY, 1.0), "google docs": ("xbold", SKY, 1.0), "excel": ("xbold", SKY, 1.0), "email": ("xbold", SKY, 1.0),
    "là em": ("serif_ib", AMBER, 1.15), "sai sai": ("serif_ib", CORAL, 1.15), "giao việc": ("serif_ib", AMBER, 1.1),
    "thực ra": ("serif_ib", CORAL, 1.1), "không phải em": ("serif_ib", CORAL, 1.1), "hỏi đáp": ("serif_ib", CORAL, 1.1),
    "sức mạnh": ("serif_ib", GOLD, 1.15), "mcp": ("xbold", MINT, 1.0), "quét nhà": ("serif_ib", AMBER, 1.1),
    "nấu cơm": ("serif_ib", AMBER, 1.1), "hướng dẫn": ("serif_ib", MINT, 1.1),
})
KEEP_CASE.update({"chatgpt": "ChatGPT", "claude": "Claude", "excel": "Excel", "email": "email", "word": "Word",
                  "google": "Google", "docs": "Docs", "latinh": "Latinh", "mcp": "MCP"})
NO_BREAK.update({"AI", "ChatGPT", "Claude", "Excel", "Email", "Word", "Google", "Docs", "Latinh", "MCP"})
COMPOUNDS.update({"ai agent", "nghĩa đen", "đại lý", "tiếng gốc", "thực hiện", "đẩy việc", "hành động", "làm thay",
                  "hàng ngày", "trả lời", "google docs", "khách hàng", "thực tế", "giao việc", "thực ra", "mọi người",
                  "dừng lại", "hỏi đáp", "không phải", "đang làm", "cái gì", "sức mạnh", "khai thác", "kết nối", "công cụ",
                  "quét nhà", "nấu cơm", "đương nhiên", "hướng dẫn", "chúng ta"})

# her face while he says "the one actually doing the work is you"
SHOT_OVERRIDES.append((beat_start("you"), beat_end("you"), "W_wide"))
# no punch-ins: every shot stays at the widest framing that still fills the vertical frame ("k cần zoom quá cận mặt")
PIP_IN, PIP_OUT = beat_start("think") - 0.05, beat_end("twist") - 0.22
PIP.append((PIP_IN, PIP_OUT))

STEEL = (178, 198, 222)
DUSK = (255, 150, 132)
G1, G2, G3 = gap("power"), gap("q_daily"), gap("think")
# 16:9: chips and the kicker ride in the sky band above the depth words, the step counter in the top letterbox bar,
# and the 9:16 layouts that start at the left edge are centred on the wide frame. 9:16 keeps the values it shipped with.
CHIP_Y = pick(215, 330)
DX = pick(W / 2 - 540, 0)


# ============================================================================
# ACT I: her hook. AI AGENT ... ĐẠI LÝ AI?
# ============================================================================
@ev(0.0, beat_end("hook"))
def hook(ctx, t):
    pill_text(ctx.front, t, 0.12, A["dai"] - 0.3, "DỰA TRÊN MỘT CUỘC TRÒ CHUYỆN CÓ THẬT", W / 2, pick(212, 322), size=28)
    depth_word(ctx, t, 0.02, A["dai"] - 0.1, "AI AGENT", size=245, gradient=(WHITE, (200, 255, 236)), enter="settle",
               stagger=0.04, fade_out=0.07, sheen=0.6)
    depth_word(ctx, t, A["dai"] - 0.06, beat_end("hook") - 0.04, "ĐẠI LÝ AI?", size=260, kind="serif_ib", rgb=AMBER, tracking=0.0,
               enter="pop", stagger=0.05, fade_out=0.06, glow=(255, 170, 60))


# ============================================================================
# ACT II: the real meaning, then "only asking questions"
# ============================================================================
@ev(beat_start("latin"), A["no_l"])
def latin(ctx, t):
    chip(ctx.front, t, A["latinh"] - 0.08, A["no_l"] - 0.12, W / 2, CHIP_Y, "gốc Latinh: agere", "spark", style="glow", size=40,
         accent=AMBER)


K_LATIN = (A["no_l"] - 0.04, beat_end("latin"))


@card(*K_LATIN, close=0.12, open_=0.2)          # voice over black: each word lands as he says it
def k_latin(ctx, t, t0, t1):
    card_text(ctx.ui, t, t0, t1, "NGHĨA GỐC", -260, kind="bold", size=38, rgb=AMBER, track=0.34)
    card_text(ctx.ui, t, t0, t1, "LÀM.", -110, kind="black", size=124, track=0.03, delay=A["lam_l"] - 0.05 - t0)
    card_text(ctx.ui, t, t0, t1, "THỰC HIỆN.", 30, kind="black", size=104, track=0.03, delay=A["thuc_l"] - 0.05 - t0)
    card_text(ctx.ui, t, t0, t1, "đẩy việc đi.", 170, kind="serif_ib", size=112, rgb=GOLD, delay=A["day_l"] - 0.05 - t0,
              glow=(255, 170, 60))


@ev(beat_start("meaning") - 0.05, beat_end("power"))
def meaning(ctx, t):
    depth_word(ctx, t, A["hanh_m"] + 0.02, A["lam_m"] - 0.08, "HÀNH ĐỘNG", size=235, gradient=(WHITE, (200, 255, 236)),
               enter="pop", stagger=0.03, fade_out=0.05)
    depth_word(ctx, t, A["lam_m"] - 0.06, beat_end("meaning") - 0.03, "LÀM THAY BẠN", size=235, gradient=(WHITE, GOLD), enter="pop",
               stagger=0.03, fade_out=0.05, sheen=0.3)
    # "thời này vẫn chỉ dùng AI để hỏi đáp ... chưa khai thác được sức mạnh ... nó làm thay"
    t1 = beat_end("power") - 0.05
    r = chip(ctx.front, t, A["hoi_p"] - 0.08, t1, W / 2 - 170, CHIP_Y, "chỉ hỏi đáp", "chat", style="glow", size=40, accent=CORAL)
    if r is not None and t >= A["chua_p"]:
        strike(ctx.front, t, A["chua_p"], r[0] + 10, r[2] - 10, (r[1] + r[3]) / 2, rgb=CORAL, width=6, t1=t1, dur=0.25)
    chip(ctx.front, t, A["lam_p"] - 0.08, t1, W / 2 + 170, CHIP_Y, "làm thay", "robot", style="glow", size=40, accent=MINT)
    depth_word(ctx, t, A["suc_p"] - 0.08, A["lam_p"] - 0.05, "SỨC MẠNH", size=240, gradient=(WHITE, GOLD), enter="scale",
               fade_out=0.05, sheen=0.25)


@card(*G1, close=0.16, open_=0.24)
def k_daily(ctx, t, t0, t1):
    card_text(ctx.ui, t, t0, t1, "BẠN DÙNG AI", 20, kind="black", size=112, track=0.03, delay=0.1)
    card_text(ctx.ui, t, t0, t1, "mỗi ngày.", 150, kind="serif_ib", size=120, rgb=GOLD, delay=0.42, glow=(255, 170, 60))


# ============================================================================
# ACT III: the trap. Her question, an ordinary day, "là em", AI telling you what to write, something is off
# ============================================================================
@ev(beat_start("q_daily") - 0.05, beat_end("q_daily"))
def q_daily(ctx, t):
    t1 = beat_end("q_daily") - 0.06
    chip(ctx.front, t, A["chatgpt_q"] - 0.08, t1, W / 2 - 150, CHIP_Y, "ChatGPT", "chat", style="glow", size=40, accent=MINT)
    chip(ctx.front, t, A["claude_q"] - 0.08, t1, W / 2 + 150, CHIP_Y, "Claude", "spark", style="glow", size=40, accent=AMBER)
    depth_word(ctx, t, A["agent_q"] - 0.1, t1, "AGENT?", size=270, kind="serif_ib", rgb=AMBER, tracking=0.0, enter="pop",
               stagger=0.05, fade_out=0.06, glow=(255, 170, 60))


@card(*G2)
def k_day(ctx, t, t0, t1):
    card_text(ctx.ui, t, t0, t1, "MỘT NGÀY", -10, kind="semi", size=84, track=0.34, delay=0.08)
    card_text(ctx.ui, t, t0, t1, "bình thường.", 110, kind="serif_ib", size=100, rgb=AMBER, delay=0.32, glow=(255, 170, 60))


STEPS = [(beat_start("m_ask") + 0.02, 1), (beat_start("m_copy") + 0.02, 2), (A["sua"] - 0.06, 3), (A["gui"] - 0.06, 4)]
HUD_T0, HUD_T1 = beat_start("m_ask") - 0.05, beat_end("you") - 0.05


def clock_icon(c, x, y, r, t, speed, rgb, a):
    c.drawCircle(x, y, r, stroke(rgb, a, width=3))
    ang = 2 * math.pi * t * speed
    c.drawLine(x, y, x + 0.78 * r * math.sin(ang), y - 0.78 * r * math.cos(ang), stroke(rgb, a, width=3))
    c.drawLine(x, y, x + 0.5 * r * math.sin(ang / 12), y - 0.5 * r * math.cos(ang / 12), stroke(rgb, a, width=3))


@ev(HUD_T0, HUD_T1 + 0.1)
def hud(ctx, t):
    """BƯỚC 01..04 over four segments; on "là em" every segment turns coral: you did all of it. 9:16: on a dark plate
    above the heads. 16:9: inside the top letterbox bar, where it never meets a depth word."""
    v = env(t, HUD_T0, HUD_T1, 0.25, 0.15)
    if v <= 0:
        return
    L = pick(ctx.ui, ctx.front)
    c = L.c
    n = max([k for (ts, k) in STEPS if t >= ts] or [1])
    you = t >= beat_start("you")
    rgb = CORAL if you else AMBER
    label = "EM LÀM HẾT" if you else f"BƯỚC {n:02d}"
    ts = max([s[0] for s in STEPS if s[0] <= t] or [HUD_T0])
    pk = 1.0 + 0.16 * (1 - ease_out_cubic(clamp01((t - (beat_start("you") if you else ts)) / 0.22)))
    sw, gp, fs, yl, ys = pick((150, 14, 32, 68, 92), (180, 16, 40, 320, 350))    # segment, gap, type, label, segments
    k = fs / 40
    x0 = W / 2 - (4 * sw + 3 * gp) / 2
    if not YT:
        c.drawRRect(rrect(x0 - 34, 262, W - x0 + 34, 384, 30), fill(INK, 165 * v))
    f = font("bold", fs)
    tw = text_width(label, f, 0.24 * fs)
    draw_text(L, label, f, W / 2 + 28, yl, rgb=rgb, a=255 * v, tracking=0.24 * fs, scale=pk)
    clock_icon(c, W / 2 + 28 - tw / 2 - 40, yl - 14 * k, 17 * k, t, 2.5 if n >= 3 else 0.8, rgb, 235 * v)
    for i in range(4):
        xa = x0 + i * (sw + gp)
        c.drawRRect(rrect(xa, ys, xa + sw, ys + 12 * k, 6), fill(WHITE, 70 * v))
        if i < n:
            c.drawRRect(rrect(xa, ys, xa + sw, ys + 12 * k, 6), fill(rgb, 240 * v))
    L.mark(x0 - 40, yl - 65, W - x0 + 40, ys + 42)


@ev(beat_start("m_ask") - 0.05, beat_end("off"))
def day(ctx, t):
    kw = dict(size=pick(250, 240), gradient=(WHITE, STEEL), enter="pop", stagger=0.025, fade_out=0.05)
    depth_word(ctx, t, A["hoi_a"] - 0.06, A["tra_a"] - 0.08, "HỎI", **kw)
    depth_word(ctx, t, A["tra_a"] - 0.06, beat_end("m_ask") - 0.04, "TRẢ LỜI", **kw)
    depth_word(ctx, t, A["copy"] - 0.06, beat_end("m_copy") - 0.04, "COPY", **kw)
    depth_word(ctx, t, A["sua"] - 0.06, A["gui"] - 0.08, "SỬA", **kw)
    depth_word(ctx, t, A["gui"] - 0.06, beat_end("m_send") - 0.04, "GỬI", **kw)
    depth_word(ctx, t, A["la_y"] - 0.08, beat_end("you") - 0.03, "LÀ EM", size=280, kind="serif_ib", rgb=AMBER, tracking=0.0,
               enter="pop", stagger=0.05, fade_out=0.06, glow=(255, 170, 60))
    # "em là người edit file, AI nó lại hướng dẫn em: bạn nên viết thế này, viết thế kia"
    depth_word(ctx, t, A["edit"] - 0.08, A["ai_ed"] - 0.1, "EDIT FILE", size=240, gradient=(WHITE, STEEL), enter="pop",
               stagger=0.03, fade_out=0.05)
    t1 = beat_end("edit") - 0.05
    chip(ctx.front, t, A["ai_ed"] - 0.08, t1, W / 2, CHIP_Y, "AI: “Bạn nên viết thế này…”", "robot", style="glow", size=38,
         accent=MINT)
    depth_word(ctx, t, A["ban_ed"] - 0.08, t1, "HƯỚNG DẪN EM", size=225, gradient=(WHITE, (200, 255, 236)), enter="scale",
               fade_out=0.05)
    depth_word(ctx, t, A["sai"] - 0.08, beat_end("off") - 0.03, "SAI SAI", size=280, kind="serif_ib", rgb=CORAL, tracking=0.0,
               enter="pop", stagger=0.05, fade_out=0.06, glow=(255, 90, 70))


# ============================================================================
# ACT IV: the twist. The delegation arrow turns round
# ============================================================================
def node(L, x, y, kind, label, rgb, a, scale=1.0):
    c = L.c
    r = 90 * scale
    c.drawCircle(x, y, r * 1.3, fill(rgb, 0.25 * a, blur=22))
    c.drawCircle(x, y, r, fill(INK, 0.7 * a))
    c.drawCircle(x, y, r, stroke(rgb, a, width=4))
    icon(c, kind, x, y, r * 1.05, rgb, a, sw=5)
    draw_text(L, label, font("black", 46), x, y + r + 62, rgb=WHITE, a=a)


@ev(PIP_IN, PIP_OUT + 0.1)
def delegate(ctx, t):
    t0, t1 = PIP_IN + 0.3, PIP_OUT
    h = 520
    v, dy, x0, y0, x1, y1 = panel(ctx, t, t0, t1, h)
    if v <= 0:
        return
    L = ctx.mid
    c = L.c
    cx = (x0 + x1) / 2
    tw_ = clamp01((t - (A["nhung"] - 0.05)) / 0.2)
    draw_text(L, "BẠN TƯỞNG", font("bold", 40), cx, y0 + 78 + dy, rgb=AMBER, a=255 * v * (1 - tw_), tracking=0.3 * 40)
    draw_text(L, "THỰC RA", font("bold", 40), cx, y0 + 78 + dy, rgb=CORAL, a=255 * v * tw_, tracking=0.3 * 40)
    ny = y0 + h * 0.47 + dy
    lx, rx = x0 + (x1 - x0) * 0.2, x0 + (x1 - x0) * 0.8
    ke = clamp01((t - (A["em_t"] - 0.1)) / 0.3)
    ka = clamp01((t - (A["ai_t"] - 0.1)) / 0.3)
    hit = clamp01((t - (A["em_w"] - 0.08)) / 0.5)
    shake = 10 * math.sin(hit * math.pi * 6) * (1 - hit) if 0 < hit < 1 else 0.0
    em_rgb = CORAL if t >= A["giao_w"] else AMBER
    if ke > 0:
        node(L, lx + shake, ny, "user", "EM", em_rgb, 255 * v * ke, 0.6 + 0.4 * spring(ke))
    if ka > 0:
        node(L, rx, ny, "robot", "AI", MINT, 255 * v * ka, 0.6 + 0.4 * spring(ka))
    # the arrow: drawn on "giao" (em -> AI); on "AI nó đang giao việc" it collapses to its middle and opens reversed
    kd = clamp01((t - (A["giao_t"] - 0.05)) / 0.4)
    if kd > 0:
        flip = ease_in_out_cubic(clamp01((t - (A["ai_w"] - 0.05)) / 0.5))
        sgn = math.cos(math.pi * flip)
        mid = (lx + rx) / 2
        half = (rx - lx) / 2 - 110
        xa, xb = mid - half * sgn, mid - half * sgn + 2 * half * sgn * ease_out_cubic(kd)
        rgb = (int(lerp(MINT[0], CORAL[0], flip)), int(lerp(MINT[1], CORAL[1], flip)), int(lerp(MINT[2], CORAL[2], flip)))
        c.drawLine(xa, ny, xb, ny, stroke(rgb, 110 * v, width=14, blur=8))
        c.drawLine(xa, ny, xb, ny, stroke(rgb, 255 * v, width=6))
        if kd >= 1 and abs(sgn) > 0.15:
            d = 1 if sgn > 0 else -1
            c.drawLine(xb, ny, xb - 22 * d, ny - 18, stroke(rgb, 255 * v, width=6))
            c.drawLine(xb, ny, xb - 22 * d, ny + 18, stroke(rgb, 255 * v, width=6))
        draw_text(L, "giao việc", font("semi", 40), mid, ny - 36, rgb=WHITE, a=255 * v * kd)
    L.mark(x0, y0 + dy, x1, y1 + dy)


# ============================================================================
# ACT V: the real agent, fast. Excel and email go to AI, wired up through MCP
# ============================================================================
def task_to_ai(L, t, t_task, t_ai, t1, label, ic):
    y = CHIP_Y
    chip(L, t, t_task - 0.08, t1, 300 + DX, y, label, ic, style="glow", size=42, accent=SKY)
    if t >= t_ai - 0.1:
        k = ease_out_cubic(clamp01((t - (t_ai - 0.1)) / 0.3))
        a = 255 * env(t, t_ai - 0.1, t1, 0.001, 0.22)
        L.c.drawLine(470 + DX, y, 470 + DX + 140 * k, y, stroke(MINT, a, width=5))
        if k >= 1:
            L.c.drawLine(610 + DX, y, 594 + DX, y - 12, stroke(MINT, a, width=5))
            L.c.drawLine(610 + DX, y, 594 + DX, y + 12, stroke(MINT, a, width=5))
        L.mark(460 + DX, y - 30, 620 + DX, y + 30)
        chip(L, t, t_ai - 0.05, t1, 760 + DX, y, "AI làm", "robot", style="glow", size=42, accent=MINT)


@ev(beat_start("q_real") - 0.05, beat_end("mcp"))
def real(ctx, t):
    depth_word(ctx, t, A["the_nao"] - 0.08, beat_end("q_real") - 0.04, "THẾ NÀO?", size=270, kind="serif_ib", rgb=AMBER,
               tracking=0.0, enter="pop", stagger=0.05, fade_out=0.06, glow=(255, 170, 60))
    depth_word(ctx, t, A["hanh_a"] - 0.06, A["lam_a"] - 0.08, "HÀNH ĐỘNG", size=235, gradient=(WHITE, (200, 255, 236)),
               enter="pop", stagger=0.03, fade_out=0.05)
    depth_word(ctx, t, A["lam_a"] - 0.06, beat_end("act") - 0.03, "LÀM THAY", size=250, gradient=(WHITE, GOLD), enter="scale",
               fade_out=0.05, sheen=0.3)
    task_to_ai(ctx.front, t, A["excel"], A["no_x"], beat_end("excel") - 0.04, "làm Excel", "file")
    depth_word(ctx, t, A["khong_x"] - 0.08, beat_end("excel") - 0.03, "KHÔNG PHẢI EM", size=225, gradient=(WHITE, DUSK),
               enter="scale", fade_out=0.05)
    task_to_ai(ctx.front, t, A["email"], A["ai_e"], beat_end("email") - 0.04, "gửi email", "upload")
    # MCP: email and Excel wired to the agent
    t1 = beat_end("mcp") - 0.05
    L = ctx.front
    y = CHIP_Y
    chip(L, t, A["email_m"] - 0.08, t1, W / 2 - 330, y, "email", "upload", style="glow", size=40, accent=SKY)
    chip(L, t, A["excel_m"] - 0.08, t1, W / 2 + 330, y, "Excel", "file", style="glow", size=40, accent=SKY)
    for (ts, xa, xb) in ((A["email_m"], W / 2 - 210, W / 2 - 70), (A["excel_m"], W / 2 + 210, W / 2 + 70)):
        if t >= ts:
            k = ease_out_cubic(clamp01((t - ts) / 0.35))
            a = 255 * env(t, ts, t1, 0.001, 0.22)
            L.c.drawLine(xa, y, lerp(xa, xb, k), y, stroke(MINT, a, width=5))
            L.mark(min(xa, xb) - 10, y - 20, max(xa, xb) + 10, y + 20)
    if t >= A["email_m"] - 0.1:
        badge(ctx, t, A["email_m"] - 0.1, t1, W / 2, y, 52, "robot", MINT)
    depth_word(ctx, t, A["mcp"] - 0.06, t1, "MCP", size=300, gradient=(WHITE, MINT), enter="scale", fade_out=0.05, sheen=0.3)


# ============================================================================
# the warm part: you can sweep and cook, but you would still like someone to do it for you
# ============================================================================
@ev(beat_start("analogy") - 0.05, beat_end("analogy"))
def analogy(ctx, t):
    t1 = beat_end("analogy") - 0.05
    depth_word(ctx, t, A["quet"] - 0.06, A["com"] - 0.12, "QUÉT NHÀ", size=245, gradient=(WHITE, SKY), enter="pop",
               stagger=0.035, fade_out=0.06)
    depth_word(ctx, t, A["com"] - 0.06, t1, "NẤU CƠM", size=245, gradient=(WHITE, GOLD), enter="pop", stagger=0.035,
               fade_out=0.06)
    chip(ctx.front, t, A["quet2"] - 0.1, A["com"] - 0.15, W / 2, CHIP_Y, "vẫn muốn có người làm thay", "user", style="glow", size=40,
         accent=MINT)
    chip(ctx.front, t, A["com2"] - 0.1, t1, W / 2, CHIP_Y, "vẫn muốn có người làm thay", "user", style="glow", size=40, accent=MINT)


@ev(beat_start("end") - 0.05, DUR)
def ending(ctx, t):
    depth_word(ctx, t, A["hoi_e"] - 0.08, A["agent_e"] - 0.1, "HỎI ĐÁP", size=250, gradient=(WHITE, DUSK), enter="pop",
               stagger=0.03, fade_out=0.05)
    depth_word(ctx, t, A["agent_e"] - 0.08, DUR - 0.01, "AGENT", size=290, gradient=(WHITE, MINT), enter="scale", fade_out=0.02,
               sheen=0.2)


for beat_ in ("act", "excel", "email", "mcp", "end"):
    flash(beat_start(beat_))


# ============================================================================
# the title on black, then the call to follow
# ============================================================================
TITLE_T = DUR + 0.35
CTA_T = DUR + 2.5


@card(DUR, TOTAL + 1, close=0.0, open_=0.0)      # a hard cut to black on "agent."
def k_end(ctx, t, t0, t1):
    L = ctx.ui
    up = ease_in_out_cubic(clamp01((t - (CTA_T - 0.25)) / 0.45))
    y = H / 2 + 40 - pick(290, 230) * up
    title_slam(L, t, TITLE_T, "AI AGENT", sub="Không chỉ trả lời. Làm thay bạn.", y=y)
    if t >= CTA_T:
        # YouTube says "Đăng ký", and its call sits higher so the lower third stays free for the end-screen elements
        size, punch = pick(66, 58), pick(62, 54)
        card_text(L, t, CTA_T, TOTAL + 1, pick("Đăng ký kênh để học cách", "Follow để học cách"), pick(-60, 60), kind="bold",
                  size=size, track=0.0, push=0.0)
        card_text(L, t, CTA_T, TOTAL + 1, "giao việc cho AI…", pick(33, 140), kind="bold", size=size, track=0.0, push=0.0,
                  delay=0.12)
        card_text(L, t, CTA_T, TOTAL + 1, "trước khi AI giao thêm việc cho bạn.", pick(150, 250), kind="serif_ib", size=punch,
                  rgb=AMBER, track=0.0, push=0.0, delay=0.9, glow=(255, 170, 60))


flash(TITLE_T)


# ============================================================================
# sound: cues on top, then the trailer score
# ============================================================================
cue(A["dai"] - 0.06, "whoosh", 0.45, length=0.5, direction=1)
cue(A["latinh"] - 0.08, "pop", 0.4, f0=520, f1=1000)
cue(A["hoi_p"] - 0.08, "pop", 0.4, f0=480, f1=900)
cue(A["chua_p"], "swipe", 0.45)
cue(A["lam_p"] - 0.08, "pop", 0.45, f0=620, f1=1180)
cue(A["chatgpt_q"] - 0.08, "pop", 0.4, f0=560, f1=1080)
cue(A["claude_q"] - 0.08, "pop", 0.4, f0=640, f1=1200)
cue(A["ai_ed"] - 0.08, "pop", 0.4, f0=600, f1=1150)
cue(A["sai"] - 0.08, "glitch", 0.5)
cue(A["em_t"] - 0.1, "pop", 0.45, f0=500, f1=950)
cue(A["giao_t"] - 0.05, "whoosh", 0.4, length=0.4, direction=1)
cue(A["ai_t"] - 0.1, "pop", 0.45, f0=620, f1=1180)
cue(A["ai_w"] - 0.05, "rewind", 0.5)
cue(A["excel"] - 0.08, "pop", 0.4, f0=560, f1=1080)
cue(A["no_x"] - 0.1, "ding", 0.3, f=1318.5)
cue(A["email"] - 0.08, "pop", 0.4, f0=620, f1=1180)
cue(A["ai_e"] - 0.1, "ding", 0.3, f=1567.98)
cue(A["email_m"] - 0.08, "connect", 0.4)
cue(A["excel_m"] - 0.08, "connect", 0.4)
cue(A["quet2"] - 0.1, "pop", 0.35, f0=520, f1=980)
cue(A["com2"] - 0.1, "pop", 0.35, f0=600, f1=1120)
cue(CTA_T, "shimmer", 0.4)
cue(CTA_T + 0.9, "pop", 0.35, f0=520, f1=1000)

CUTS3 = [beat_start("m_ask"), beat_start("m_copy"), A["sua"] - 0.06, A["gui"] - 0.06]
# act I: a boom as the bars slide in, a drone and a heartbeat under her question, a hit on "đại lý AI"
score("boom", 0.0)
score("pad", 0.0, notes=[38, 45, 50], dur=K_LATIN[0], gain=0.9, bright=0.12, att=0.25, rel=0.6)
score("heartbeat", 0.35, until=A["dai"] - 0.2, bpm=72)
score("taiko", A["dai"] - 0.04, gain=0.8, f0=140, f1=60)
score("boom", A["dai"] - 0.04, gain=0.4, length=1.4)
# act II: a low hit on each word of the root over black, a pulse under "chỉ hỏi đáp", a braam on the card
score("taiko", K_LATIN[0], gain=0.6, f0=150, f1=60)
for tt_ in (A["lam_l"], A["thuc_l"], A["day_l"]):
    score("taiko", tt_ - 0.05, gain=0.45, f0=125, f1=55)
score("pad", beat_start("meaning"), notes=[46, 50, 53, 58], dur=beat_end("power") - beat_start("meaning") + 0.2,
      gain=0.7, bright=0.25, att=0.4, rel=0.5)
score("heartbeat", beat_start("power") + 0.1, until=G1[0] - 0.3, bpm=80, gain=0.8)
score("braam", G1[0] + 0.12, chord=BB_MAJ, length=3.2)
score("boom", G1[0] + 0.12, gain=0.7)
# act III: tension under her question, then the clock, the ostinato and a drum hit on every step, a dissonant swell
# and a riser into the held beat before the twist
score("pad", beat_start("q_daily"), notes=[57, 64, 69, 76], dur=beat_end("q_daily") - beat_start("q_daily") + 0.3,
      gain=0.8, bright=0.35, att=1.0, rel=0.35, trem=0.4)
score("clock", G2[0] + 0.2, until=beat_end("edit") - 0.02, bpm=100, fast_from=A["sua"] - 0.06, loud_from=beat_start("you"))
score("ostinato", beat_start("m_ask"), until=beat_end("edit") - 0.05, bpm=100, fast_from=A["sua"] - 0.06)
for k_, tc_ in enumerate(CUTS3):
    score("taiko", tc_, gain=0.45 + 0.03 * k_, f0=120 + 6 * k_, f1=55)
score("taiko", beat_start("you") + 0.02, gain=0.7, f0=150, f1=60)
score("taiko", beat_start("edit") + 0.02, gain=0.5, f0=130, f1=58)
score("pad", beat_start("off"), notes=[38, 39, 45, 51], dur=G3[0] - beat_start("off") + 0.05, bright=0.35, att=1.2,
      rel=0.05, trem=0.35)
score("riser", G3[0], length=G3[0] - beat_start("off"), gain=0.8)
# the twist: silence on the held beat, a swell, then a braam kept low under "AI nó đang giao việc cho em"
score("swell", A["ai_w"] - 0.02, length=0.5)
score("braam", A["ai_w"] - 0.03, chord=D_MIN, length=3.0, gain=0.42)
score("boom", A["ai_w"] - 0.03, gain=0.7)
score("pad", beat_start("q_real"), notes=[50, 54, 57, 62], dur=beat_end("q_real") - beat_start("q_real") + 0.2,
      gain=0.8, bright=0.3, att=0.3, rel=0.4)
# act V: the drive, a hit on every cut
score("drive", beat_start("act"), until=beat_end("mcp"), bpm=120)
for tc_ in (beat_start("act"), beat_start("excel"), beat_start("email"), beat_start("mcp")):
    score("taiko", tc_, gain=0.65, f0=135, f1=55)
# the warm part: the drive stops, a warm pad and bells under the sweeping and the cooking
score("swell", beat_start("analogy"), length=0.4, gain=0.6)
score("pad", beat_start("analogy"), notes=[50, 54, 57, 62, 66], dur=beat_end("analogy") - beat_start("analogy") + 0.1,
      gain=0.85, bright=0.25, att=0.5, rel=0.5)
score("bells", A["quet2"] - 0.05, notes=[74, 78, 81])
score("bells", A["com2"] - 0.05, notes=[76, 79, 83])
# the last line: a heartbeat and a riser into the black
score("heartbeat", beat_start("end") + 0.05, until=DUR - 0.4, bpm=96, gain=0.9)
score("riser", DUR, length=DUR - beat_start("end"))
# the title, then a lighter tail under the call to follow
score("swell", TITLE_T, length=0.35, gain=0.8)
score("braam", TITLE_T - 0.01, chord=D_MIN + [50], length=3.0, gain=1.15)
score("boom", TITLE_T - 0.01, length=3.0)
score("crash", TITLE_T - 0.01, gain=0.9)
score("pad", CTA_T - 0.2, notes=[50, 57, 62, 66], dur=TOTAL - CTA_T, gain=0.6, bright=0.2, att=0.6, rel=0.3)
score("piano", CTA_T, notes=[(0.0, 62), (0.45, 69), (0.9, 74), (1.6, 78)])
