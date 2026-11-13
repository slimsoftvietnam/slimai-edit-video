"""MCP là gì? as a movie trailer for TikTok (9:16, about 89 s), from a 5-minute talk between two people, shot on an
iPhone in HLG outdoors and kept in the camera's own colour (the "iphone" look).

Her question, as a split screen (him on top, her below); a date card (Anthropic, November 2024); "mình đi từng từ";
MCP spelled out letter by letter; M = model (the myth: Claude is the product, Opus the model); C = context (a brain
with no eyes and no hands, plug them in; Gmail and Notion in a fast drive; the laptop and the USB stick as the warm
part); P = protocol (one standard shared by all software); the twist: the P in HTTP, and her "À" in the split; the
last line; the title and a call to follow that lands the plug-in idea.

What it adds to examples/ai-agent-trailer (no darkening, wide shots only, anchors from word_in(), the good lines kept):
- the split screen, split_screen(): her question and her "À" show both people, him on top and her below, with text
  over his legs and behind her head. The user asked for this layout on this video and then approved it for the skill;
- letter cards M / C / P as the chapters of an explainer;
- cut points in measured silences, with "hard" edges in select.json where Whisper stretched the word ends.
"""
import math

import skia

from gfx import big_text
from story import *
from trailer import *
from trailer_score import BB_MAJ, D_MAJ, D_MIN

# word anchors in output seconds: (name, beat, word[, n-th]), looked up inside that beat's own clips
for name_, beat_, word_, *n_ in [
        ("mcp_h", "hook", "mcp"), ("ai2_h", "hook", "ai", 2), ("nhac_h", "hook", "nhắc"), ("tung", "word", "từng"),
        ("mcp_n", "name", "mcp"), ("model_n", "name", "model"), ("context_n", "name", "context"),
        ("protocol_n", "name", "protocol"), ("model_m", "model", "model"), ("mo_m", "model", "mô"),
        ("ngon_m", "model", "ngôn"), ("nham", "myth", "nhầm"), ("claude_y", "myth", "claude"),
        ("thuc", "truth", "thực"), ("claude_t", "truth", "claude"), ("san", "truth", "sản"),
        ("model_t", "truth", "model"), ("opus", "truth", "opus"), ("context_c", "context", "context"),
        ("ngu_c", "context", "ngữ"), ("model_b", "brain", "model"), ("bo", "brain", "bộ"), ("nao", "noeyes", "não"),
        ("mat", "noeyes", "mắt"), ("tay", "noeyes", "tay"), ("cam_p", "plug", "cắm"), ("tay_p", "plug", "tay"),
        ("mat_p", "plug", "mắt"), ("lam_p", "plug", "làm"), ("du_g", "gmail", "dữ"), ("gmail", "gmail", "gmail"),
        ("cam_g", "gmail2", "cắm"), ("ngu_g", "gmail2", "ngữ"), ("file", "notion", "file"),
        ("notion", "notion", "notion"), ("laptop", "usb", "laptop"), ("usb", "usb", "usb"),
        ("cam_u", "usb", "cắm", 2), ("vao", "usb", "vào"), ("p_p", "protocol", "p"),
        ("protocol_p", "protocol", "protocol"), ("giao", "protocol", "giao"), ("chuan", "protocol", "chuẩn"),
        ("dung", "protocol", "dùng"), ("tat_p", "protocol", "tất"), ("chu_h", "http", "chữ"),
        ("trong", "http", "trong"), ("http", "http", "http"), ("dia", "http", "địa"), ("a_a", "aha", "à"),
        ("protocol_a", "aha", "protocol"), ("tat_e", "end", "tất"), ("ket", "end", "kết"),
        ("model_e", "end", "model"), ("nhat", "end", "nhất"), ("hieu", "end", "hiệu"), ("vay", "end", "vậy")]:
    A[name_] = word_in(beat_, word_, *n_)

KEYS.update({
    "mcp": ("xbold", MINT, 1.0), "model": ("xbold", AMBER, 1.0), "context": ("xbold", AMBER, 1.0),
    "protocol": ("xbold", AMBER, 1.0), "claude": ("xbold", WHITE, 1.0), "opus": ("xbold", MINT, 1.0),
    "nhầm tưởng": ("serif_ib", CORAL, 1.1), "tên sản phẩm": ("serif_ib", AMBER, 1.1), "mô hình": ("serif_ib", GOLD, 1.1),
    "ngữ cảnh": ("serif_ib", GOLD, 1.15), "bộ não": ("serif_ib", AMBER, 1.15), "mắt": ("xbold", CORAL, 1.0),
    "tay": ("xbold", CORAL, 1.0), "cắm thêm": ("serif_ib", MINT, 1.1), "gmail": ("xbold", SKY, 1.0),
    "notion": ("xbold", SKY, 1.0), "laptop": ("xbold", SKY, 1.0), "usb": ("xbold", SKY, 1.0),
    "giao thức": ("serif_ib", GOLD, 1.1), "chuẩn chung": ("serif_ib", AMBER, 1.1), "http": ("xbold", AMBER, 1.0),
    "kết nối": ("serif_ib", MINT, 1.1), "nhất quán": ("serif_ib", GOLD, 1.1), "hiệu quả": ("serif_ib", GOLD, 1.1),
})
KEEP_CASE.update({"mcp": "MCP", "claude": "Claude", "opus": "Opus", "gmail": "Gmail", "notion": "Notion",
                  "usb": "USB", "http": "HTTP"})
NO_BREAK.update({"MCP", "Model", "Context", "Protocol", "Claude", "Opus", "Gmail", "Notion", "USB", "HTTP"})
COMPOUNDS.update({"mô hình", "ngôn ngữ", "nhầm tưởng", "sản phẩm", "tên sản phẩm", "ngữ cảnh", "bộ não", "cắm thêm",
                  "dữ liệu", "làm việc", "giao thức", "chuẩn chung", "dùng chung", "tất cả", "phần mềm", "kết nối",
                  "nhất quán", "hiệu quả", "địa chỉ", "ám chỉ", "thực ra"})

G_DATE, G_M, G_TR, G_C, G_P, G_TW = gap("hook"), gap("name"), gap("myth"), gap("truth"), gap("usb"), gap("protocol")
CHIP_Y = 330
STEEL = (178, 198, 222)
DUSK = (255, 150, 132)

# ----------------------------------------------------------------------------
# split screen: him on top, her below, for her question and for her "À" (the captions sit on the seam meanwhile)
# ----------------------------------------------------------------------------
split_screen(0.0, beat_end("hook"))
split_screen(beat_start("aha"), beat_end("aha"))
SPLIT_FRAME.update({"M": (1190, 668, 560), "W": (665, 621, 560)})   # source centre x, y and height shown per half


# ----------------------------------------------------------------------------
# small drawing helpers
# ----------------------------------------------------------------------------
def node(L, x, y, kind, label, rgb, a, scale=1.0, r=78):
    c = L.c
    rr = r * scale
    c.drawCircle(x, y, rr * 1.3, fill(rgb, 0.25 * a, blur=22))
    c.drawCircle(x, y, rr, fill(INK, 0.72 * a))
    c.drawCircle(x, y, rr, stroke(rgb, a, width=4))
    icon(c, kind, x, y, rr * 1.05, rgb, a, sw=5)
    if label:
        draw_text(L, label, font("black", 40), x, y + rr + 54, rgb=WHITE, a=a, tracking=0.12 * 40)
    L.mark(x - rr * 1.45, y - rr * 1.45, x + rr * 1.45, y + rr + 80)


def wire(L, t, t0, t1, xa, ya, xb, yb, rgb=MINT, dur=0.35, width=5):
    """a line that draws itself from a to b at t0 and fades out with t1."""
    if t < t0:
        return
    k = ease_out_cubic(clamp01((t - t0) / dur))
    a = 255 * env(t, t0, t1, 0.001, 0.22)
    if a <= 0:
        return
    L.c.drawLine(xa, ya, lerp(xa, xb, k), lerp(ya, yb, k), stroke(rgb, a * 0.45, width=width * 2.6, blur=6))
    L.c.drawLine(xa, ya, lerp(xa, xb, k), lerp(ya, yb, k), stroke(rgb, a, width=width))
    L.mark(min(xa, xb) - 20, min(ya, yb) - 20, max(xa, xb) + 20, max(ya, yb) + 20)


def dashes(L, xa, ya, xb, yb, rgb, a, n=7):
    """a dashed line: a socket with nothing plugged in."""
    for i in range(n):
        u0, u1 = i / n, (i + 0.5) / n
        L.c.drawLine(lerp(xa, xb, u0), lerp(ya, yb, u0), lerp(xa, xb, u1), lerp(ya, yb, u1), stroke(rgb, a, width=4))
    L.mark(min(xa, xb) - 10, min(ya, yb) - 10, max(xa, xb) + 10, max(ya, yb) + 10)


def box(L, x, y, w, h, rgb, a, r=30):
    L.c.drawRRect(rrect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, r), fill(INK, 0.72 * a))
    L.c.drawRRect(rrect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, r), stroke(rgb, 0.85 * a, width=3))
    L.mark(x - w / 2 - 8, y - h / 2 - 8, x + w / 2 + 8, y + h / 2 + 8)


def letter_card(ctx, t, t0, t1, nth, letter, word):
    """a chapter card: CHỮ THỨ NHẤT / M / MODEL."""
    card_text(ctx.ui, t, t0, t1, nth, -290, kind="bold", size=36, rgb=AMBER, track=0.34)
    card_text(ctx.ui, t, t0, t1, letter, 70, kind="black", size=330, track=0.0, delay=0.05, glow=(255, 170, 60))
    card_text(ctx.ui, t, t0, t1, word, 205, kind="bold", size=56, track=0.34, delay=0.2)


# ============================================================================
# ACT I: her question in the split screen. MCP? ... everyone who uses AI mentions it
# ============================================================================
@ev(0.0, beat_end("hook"))
def hook(ctx, t):
    t1 = beat_end("hook") - 0.04
    # behind her head in the lower half (a split puts the behind layer behind the person in each half)
    big_text(ctx.behind, t, A["mcp_h"] - 0.12, t1, "MCP?", W / 2, 1232, size=236, kind="black", rgb=WHITE, max_w=900,
             enter="pop", glow=None, gradient=(WHITE, (200, 255, 236)), tracking=-0.02, stagger=0.06, alpha=1.0,
             fade_out=0.06, sheen=0.5)
    # "ai khi mà dùng AI cũng nhắc đến": the word keeps popping up around him
    for k_, (x_, y_) in enumerate([(235, 800), (850, 765), (560, 880)]):
        chip(ctx.front, t, A["nhac_h"] - 0.25 + 0.14 * k_, t1, x_, y_, "MCP", "chat", style="glow", size=38, accent=MINT)


@card(*G_DATE, close=0.16, open_=0.24)
def k_date(ctx, t, t0, t1):
    card_text(ctx.ui, t, t0, t1, "THÁNG 11 · 2024", -170, kind="bold", size=40, rgb=AMBER, track=0.34)
    card_text(ctx.ui, t, t0, t1, "ANTHROPIC", -20, kind="black", size=118, track=0.04, delay=0.12)
    card_text(ctx.ui, t, t0, t1, "công bố một chuẩn chung.", 112, kind="serif_ib", size=74, rgb=GOLD, track=0.0,
              delay=0.45, glow=(255, 170, 60))


# ============================================================================
# ACT II: word by word. M C P spelled out, then M = model and the Claude myth
# ============================================================================
@ev(beat_start("word") - 0.05, beat_end("word"))
def word(ctx, t):
    depth_word(ctx, t, A["tung"] - 0.08, beat_end("word") - 0.03, "TỪNG TỪ", size=250, kind="serif_ib", rgb=AMBER,
               tracking=0.0, enter="pop", stagger=0.05, fade_out=0.06, glow=(255, 170, 60))


ROWS = [("M", "odel", "model_n", 410), ("C", "ontext", "context_n", 600), ("P", "rotocol", "protocol_n", 790)]


@ev(beat_start("name") - 0.05, beat_end("name") + 0.1)
def name(ctx, t):
    """MCP: the three initials stand in a column, each word slides out of its letter as he says it."""
    t0, t1 = A["mcp_n"] - 0.1, beat_end("name") - 0.02
    v = env(t, t0, t1, 0.2, 0.12)
    if v <= 0:
        return
    L = ctx.front
    fi, fr = font("black", 160), font("bold", 104)
    wmax = max(text_width(a_, fi) + 10 + text_width(b_, fr) for a_, b_, _, _ in ROWS)
    x0 = W / 2 - wmax / 2
    for k_, (a_, b_, key, y_) in enumerate(ROWS):
        ki = clamp01((t - (t0 + 0.07 * k_)) / 0.3)
        if ki <= 0:
            continue
        wi = text_width(a_, fi)
        draw_text(L, a_, fi, x0 + wi / 2, y_, rgb=AMBER, a=255 * v * ki, scale=0.6 + 0.4 * spring(ki),
                  glow=(255, 170, 60), glow_a=110, shadow=8, shadow_a=150)
        kr = clamp01((t - (A[key] - 0.06)) / 0.3)
        if kr > 0:
            e = ease_out_cubic(kr)
            wr = text_width(b_, fr)
            draw_text(L, b_, fr, x0 + wi + 10 + wr / 2 - 30 * (1 - e), y_, rgb=WHITE, a=255 * v * e, shadow=8,
                      shadow_a=150)


@card(*G_M)
def k_m(ctx, t, t0, t1):
    letter_card(ctx, t, t0, t1, "CHỮ THỨ NHẤT", "M", "MODEL")


@ev(beat_start("model") - 0.05, beat_end("model"))
def model(ctx, t):
    t1 = beat_end("model") - 0.04
    depth_word(ctx, t, A["model_m"] - 0.06, A["mo_m"] - 0.12, "MODEL", size=260, gradient=(WHITE, GOLD), enter="pop",
               stagger=0.04, fade_out=0.06)
    depth_word(ctx, t, A["mo_m"] - 0.06, t1, "MÔ HÌNH", size=250, gradient=(WHITE, (200, 255, 236)), enter="pop",
               stagger=0.04, fade_out=0.06)
    chip(ctx.front, t, A["ngon_m"] - 0.08, t1, W / 2, CHIP_Y, "ngôn ngữ lớn · LLM", "brain", style="glow", size=40,
         accent=MINT)


@ev(beat_start("myth") - 0.05, beat_end("truth"))
def myth(ctx, t):
    # "nhiều người hay nhầm tưởng Claude là model" ... "thực ra" strikes it out
    r = chip(ctx.front, t, A["claude_y"] - 0.08, A["thuc"] + 0.45, W / 2, CHIP_Y, "Claude = model?", "spark",
             style="glow", size=42, accent=CORAL)
    if r is not None and t >= A["thuc"] - 0.02:
        strike(ctx.front, t, A["thuc"] - 0.02, r[0] + 10, r[2] - 10, (r[1] + r[3]) / 2, rgb=CORAL, width=6,
               t1=A["thuc"] + 0.45, dur=0.22)
    depth_word(ctx, t, A["nham"] - 0.08, beat_end("myth") - 0.03, "NHẦM TƯỞNG", size=230, kind="serif_ib", rgb=CORAL,
               tracking=0.0, enter="pop", stagger=0.04, fade_out=0.06, glow=(255, 90, 70))
    # the truth: Claude is the product, Opus is the model
    t1 = beat_end("truth") - 0.05
    L, y = ctx.front, 520
    for (x, nm, lab, tn, tl, rgb) in ((275, "Claude", "TÊN SẢN PHẨM", A["claude_t"], A["san"], AMBER),
                                      (805, "Opus", "MODEL", A["opus"], A["opus"], MINT)):
        v = env(t, tn - 0.08, t1, 0.001, 0.2)
        if v <= 0:
            continue
        sc = 0.7 + 0.3 * spring(clamp01((t - (tn - 0.08)) / 0.35))
        box(L, x, y, 410 * sc, 170 * sc, rgb, 255 * v, r=36 * sc)
        draw_text(L, nm, font("black", 78 * sc), x, y + 27 * sc, rgb=WHITE, a=255 * v)
        kl = clamp01((t - (tl - 0.06)) / 0.25)
        if kl > 0:
            draw_text(L, lab, font("bold", 34), x, y - 85 * sc - 28, rgb=rgb, a=255 * v * kl, tracking=0.3 * 34)
    wire(L, t, A["model_t"] - 0.05, t1, 488, y, 592, y, rgb=WHITE, dur=0.3)
    if t >= A["model_t"] + 0.25:
        a = 255 * env(t, A["model_t"] + 0.25, t1, 0.001, 0.22)
        L.c.drawLine(592, y, 574, y - 14, stroke(WHITE, a, width=5))
        L.c.drawLine(592, y, 574, y + 14, stroke(WHITE, a, width=5))


@card(G_TR[0], G_TR[1], close=0.06, open_=0.1)          # a breath of black before the reveal
def k_truth(ctx, t, t0, t1):
    card_text(ctx.ui, t, t0, t1, "THỰC RA…", 30, kind="serif_ib", size=110, rgb=CORAL, delay=0.02, glow=(255, 90, 70))


@card(*G_C)
def k_c(ctx, t, t0, t1):
    letter_card(ctx, t, t0, t1, "CHỮ THỨ HAI", "C", "CONTEXT")


# ============================================================================
# ACT III: C = context. A brain with no eyes and no hands; plug them in; Gmail and Notion; the USB stick
# ============================================================================
@ev(beat_start("context") - 0.05, beat_end("context"))
def context(ctx, t):
    depth_word(ctx, t, A["context_c"] - 0.06, A["ngu_c"] - 0.1, "CONTEXT", size=240, gradient=(WHITE, GOLD),
               enter="pop", stagger=0.035, fade_out=0.05)
    depth_word(ctx, t, A["ngu_c"] - 0.06, beat_end("context") - 0.03, "NGỮ CẢNH", size=250, kind="serif_ib",
               rgb=GOLD, tracking=0.0, enter="pop", stagger=0.04, fade_out=0.06, glow=(255, 170, 60))


BRAIN_X, BRAIN_Y = W / 2, 560
SLOT_L, SLOT_R = 185, 895


@ev(beat_start("brain") - 0.05, beat_end("notion"))
def brain(ctx, t):
    """the model as a brain; two empty sockets (eyes, hands) that get plugged in; then Gmail and Notion."""
    L = ctx.front
    t_in, t_out = A["model_b"] - 0.1, beat_end("notion") - 0.05
    v = env(t, t_in, t_out, 0.001, 0.22)
    if v <= 0:
        return
    kb = clamp01((t - t_in) / 0.4)
    lit = ease_out_cubic(clamp01((t - (A["lam_p"] - 0.05)) / 0.4))
    rgb = (int(lerp(AMBER[0], MINT[0], lit)), int(lerp(AMBER[1], MINT[1], lit)), int(lerp(AMBER[2], MINT[2], lit)))
    pulse = 1 + 0.06 * math.sin(math.pi * clamp01((t - (A["nao"] - 0.05)) / 0.35)) if t >= A["nao"] - 0.05 else 1
    node(L, BRAIN_X, BRAIN_Y, "brain", "BỘ NÃO" if t >= A["bo"] - 0.06 else None, rgb, 255 * v,
         (0.6 + 0.4 * spring(kb)) * pulse, r=98)
    # eyes and hands: empty (dashed, crossed) until he plugs them in
    t_sock = beat_end("plug") - 0.05
    for (x, lab, t_show, t_plug) in ((SLOT_L, "mắt", A["mat"], A["mat_p"]), (SLOT_R, "tay", A["tay"], A["tay_p"])):
        if not (t_show - 0.08 <= t <= t_sock + 0.25):
            continue
        a = 255 * v * env(t, t_show - 0.08, t_sock, 0.001, 0.22)
        plugged = t >= t_plug - 0.04
        xa, xb = (x + 105, BRAIN_X - 122) if x < BRAIN_X else (x - 105, BRAIN_X + 122)
        if plugged:
            wire(L, t, t_plug - 0.04, t_sock, xa, BRAIN_Y, xb, BRAIN_Y, rgb=MINT)
        else:
            dashes(L, xa, BRAIN_Y, xb, BRAIN_Y, CORAL, 0.7 * a)
        chip(L, t, t_show - 0.08, t_sock, x, BRAIN_Y, lab, "check" if plugged else "cross", style="glow", size=52,
             accent=MINT if plugged else CORAL, alpha=v)
    # Gmail, then Notion, wired into the brain as context
    for (x, lab, ic, t_show, t_wire) in ((SLOT_L, "Gmail", "upload", A["gmail"], A["cam_g"]),
                                         (SLOT_R, "Notion", "file", A["file"], A["notion"])):
        if t < t_show - 0.1:
            continue
        chip(L, t, t_show - 0.08, t_out, x, BRAIN_Y, lab, ic, style="glow", size=48, accent=SKY, alpha=v)
        xa, xb = (x + 125, BRAIN_X - 122) if x < BRAIN_X else (x - 125, BRAIN_X + 122)
        wire(L, t, t_wire - 0.05, t_out, xa, BRAIN_Y, xb, BRAIN_Y, rgb=SKY)


@ev(beat_start("brain") - 0.05, beat_end("notion"))
def context_words(ctx, t):
    depth_word(ctx, t, A["bo"] - 0.06, beat_end("brain") - 0.03, "BỘ NÃO", size=250, kind="serif_ib", rgb=AMBER,
               tracking=0.0, enter="pop", stagger=0.04, fade_out=0.06, glow=(255, 170, 60))
    depth_word(ctx, t, A["mat"] - 0.06, beat_end("noeyes") - 0.03, "KHÔNG MẮT, KHÔNG TAY", size=180, gradient=(WHITE, DUSK),
               enter="scale", fade_out=0.05)
    depth_word(ctx, t, A["cam_p"] - 0.06, beat_end("plug") - 0.03, "CẮM THÊM", size=250, gradient=(WHITE, MINT),
               enter="pop", stagger=0.04, fade_out=0.06, sheen=0.3)
    depth_word(ctx, t, A["gmail"] - 0.06, beat_end("gmail") - 0.03, "GMAIL", size=270, gradient=(WHITE, SKY),
               enter="pop", stagger=0.04, fade_out=0.05)
    depth_word(ctx, t, A["ngu_g"] - 0.06, beat_end("gmail2") - 0.03, "NGỮ CẢNH", size=250, kind="serif_ib", rgb=GOLD,
               tracking=0.0, enter="pop", stagger=0.04, fade_out=0.05, glow=(255, 170, 60))
    depth_word(ctx, t, A["notion"] - 0.06, beat_end("notion") - 0.03, "NOTION", size=270, gradient=(WHITE, SKY),
               enter="pop", stagger=0.04, fade_out=0.05)


for beat_ in ("gmail", "gmail2", "notion"):
    flash(beat_start(beat_))


def laptop(L, x, y, a, glow):
    sw, sh = 440, 272
    c = L.c
    if glow > 0:
        c.drawRRect(rrect(x - sw / 2 - 40, y - sh / 2 - 40, x + sw / 2 + 40, y + sh / 2 + 40, 50),
                    fill(MINT, 0.4 * a * glow, blur=34))
    c.drawRRect(rrect(x - sw / 2, y - sh / 2, x + sw / 2, y + sh / 2, 22), fill((24, 32, 48), 0.94 * a))
    c.drawRRect(rrect(x - sw / 2 + 18, y - sh / 2 + 18, x + sw / 2 - 18, y + sh / 2 - 18, 10),
                fill((58, 74, 104), 0.9 * a))
    if glow > 0:
        c.drawRRect(rrect(x - sw / 2 + 18, y - sh / 2 + 18, x + sw / 2 - 18, y + sh / 2 - 18, 10),
                    fill(MINT, 0.85 * a * glow))
    c.drawRRect(rrect(x - sw / 2, y - sh / 2, x + sw / 2, y + sh / 2, 22), stroke(WHITE, a, width=6))
    c.drawRRect(rrect(x - sw / 2 - 70, y + sh / 2 + 10, x + sw / 2 + 70, y + sh / 2 + 44, 14), fill(STEEL, 0.95 * a))
    c.drawRRect(rrect(x - sw / 2 - 70, y + sh / 2 + 10, x + sw / 2 + 70, y + sh / 2 + 44, 14), stroke(WHITE, a, width=5))
    L.mark(x - sw / 2 - 90, y - sh / 2 - 50, x + sw / 2 + 90, y + sh / 2 + 60)


def usb_stick(L, x, y, a):
    """the stick, its connector tip at x."""
    c = L.c
    c.drawRRect(rrect(x, y - 20, x + 52, y + 20, 5), fill(STEEL, 0.95 * a))
    c.drawRRect(rrect(x + 50, y - 34, x + 220, y + 34, 16), fill(SKY, 0.97 * a))
    c.drawRRect(rrect(x + 50, y - 34, x + 220, y + 34, 16), stroke(WHITE, a, width=5))
    L.mark(x - 10, y - 46, x + 232, y + 46)


@ev(beat_start("usb") - 0.05, beat_end("usb"))
def usb(ctx, t):
    """the warm part: the laptop, the USB stick, plugged in, the screen lights up."""
    L = ctx.front
    t1 = beat_end("usb") - 0.05
    v = env(t, A["laptop"] - 0.1, t1, 0.001, 0.25)
    if v <= 0:
        return
    x, y = W / 2 - 95, 540
    glow = ease_out_cubic(clamp01((t - (A["vao"] - 0.05)) / 0.35))
    laptop(L, x, y, 255 * v, glow)
    port_x, port_y = x + 220 + 70, y + 136 + 27
    if t >= A["usb"] - 0.1:
        ks = clamp01((t - (A["usb"] - 0.1)) / 0.3)
        slide = ease_in_out_cubic(clamp01((t - (A["cam_u"] - 0.05)) / 0.45))
        sx = lerp(port_x + 150, port_x, slide)
        usb_stick(L, sx + 30 * (1 - ks), port_y, 255 * v * ks)
    if t >= A["usb"] - 0.1:
        chip(L, t, A["usb"] - 0.1, t1, W / 2, CHIP_Y, "ổ USB = ngữ cảnh", "link", style="glow", size=44,
             accent=SKY, alpha=v)


@card(*G_P)
def k_p(ctx, t, t0, t1):
    letter_card(ctx, t, t0, t1, "CHỮ CUỐI", "P", "PROTOCOL")


# ============================================================================
# ACT IV: P = protocol. One standard shared by every piece of software; then the P you meet every day
# ============================================================================
APPS = [(170, "browser"), (390, "database"), (690, "file"), (910, "chat")]


@ev(beat_start("protocol") - 0.05, beat_end("protocol"))
def protocol(ctx, t):
    t1 = beat_end("protocol") - 0.04
    depth_word(ctx, t, A["protocol_p"] - 0.06, A["giao"] - 0.1, "PROTOCOL", size=230, gradient=(WHITE, GOLD),
               enter="pop", stagger=0.035, fade_out=0.05)
    depth_word(ctx, t, A["giao"] - 0.06, A["dung"] - 0.1, "GIAO THỨC", size=240, kind="serif_ib", rgb=GOLD,
               tracking=0.0, enter="pop", stagger=0.04, fade_out=0.06, glow=(255, 170, 60))
    depth_word(ctx, t, A["dung"] - 0.06, t1, "DÙNG CHUNG", size=240, gradient=(WHITE, MINT), enter="scale",
               fade_out=0.05, sheen=0.3)
    # every app on one shared socket
    L = ctx.front
    hub_y, row_y = 660, 410
    chip(L, t, A["chuan"] - 0.08, t1, W / 2, hub_y, "chuẩn chung", "link", style="glow", size=48, accent=AMBER)
    for k_, (x_, ic) in enumerate(APPS):
        badge(ctx, t, A["dung"] - 0.1 + 0.12 * k_, t1, x_, row_y, 58, ic, SKY)
        wire(L, t, A["tat_p"] - 0.05 + 0.06 * k_, t1, x_, row_y + 70, lerp(x_, W / 2, 0.55), hub_y - 44, rgb=AMBER,
             dur=0.3, width=6)


@card(*G_TW)
def k_twist(ctx, t, t0, t1):
    card_text(ctx.ui, t, t0, t1, "CHỮ P ẤY", -10, kind="black", size=112, track=0.04, delay=0.08)
    card_text(ctx.ui, t, t0, t1, "bạn gặp mỗi ngày.", 120, kind="serif_ib", size=96, rgb=GOLD, track=0.0, delay=0.4,
              glow=(255, 170, 60))


def address_bar(L, t, t_in, t_type0, t_type1, t_glow, t1, y=500):
    """a browser address bar that types http:// and lights up its p."""
    v = env(t, t_in, t1, 0.25, 0.2)
    if v <= 0:
        return
    k = 0.85 + 0.15 * ease_out_cubic(clamp01((t - t_in) / 0.3))
    x0, x1 = W / 2 - 400 * k, W / 2 + 400 * k
    h = 120
    L.c.drawRRect(rrect(x0, y - h / 2, x1, y + h / 2, h / 2), fill(INK, 190 * v))
    L.c.drawRRect(rrect(x0, y - h / 2, x1, y + h / 2, h / 2), stroke(WHITE, 90 * v, width=2.5))
    icon(L.c, "browser", x0 + 78, y, 58, WHITE, 230 * v, sw=4)
    L.mark(x0 - 6, y - h / 2 - 6, x1 + 6, y + h / 2 + 6)
    text = "http://"
    n = int(round(len(text) * clamp01((t - t_type0) / max(0.05, t_type1 - t_type0))))
    f = font("bold", 68)
    tx = x0 + 150
    glow = ease_out_cubic(clamp01((t - (t_glow - 0.05)) / 0.3))
    for i, ch in enumerate(text[:n]):
        cw = text_width(ch, f)
        is_p = i == 3
        rgb = AMBER if (is_p and glow > 0) else WHITE
        sc = 1.0 + (0.35 * glow if is_p else 0.0)
        draw_text(L, ch, f, tx + cw / 2, y + 24, rgb=rgb, a=255 * v, scale=sc,
                  glow=(255, 170, 60) if (is_p and glow > 0) else None, glow_a=200 * glow)
        tx += cw
    if n < len(text) or (int(t * 2.4) % 2 == 0):
        L.c.drawRect(skia.Rect.MakeLTRB(tx + 6, y - 34, tx + 11, y + 34), fill(WHITE, 220 * v))


@ev(beat_start("http") - 0.05, beat_end("http"))
def http(ctx, t):
    t1 = beat_end("http") - 0.04
    depth_word(ctx, t, A["chu_h"] - 0.06, A["trong"] - 0.1, "CHỮ P", size=270, kind="serif_ib", rgb=AMBER,
               tracking=0.0, enter="pop", stagger=0.05, fade_out=0.06, glow=(255, 170, 60))
    address_bar(ctx.front, t, A["trong"] - 0.3, A["trong"] - 0.1, A["http"] + 0.25, A["http"] + 0.1, t1)
    chip(ctx.front, t, A["dia"] - 0.08, t1, W / 2, 660, "địa chỉ web", "browser", style="glow", size=42, accent=SKY)
    depth_word(ctx, t, A["http"] - 0.06, t1, "HTTP", size=290, gradient=(WHITE, GOLD), enter="scale", fade_out=0.05,
               sheen=0.3)


@ev(beat_start("aha") - 0.02, beat_end("aha"))
def aha(ctx, t):
    """split screen: her "À". HTTP and MCP side by side, both P's light up on "protocol"."""
    L = ctx.front
    t1 = beat_end("aha") - 0.03
    v = env(t, beat_start("aha"), t1, 0.15, 0.1)
    if v <= 0:
        return
    glow = ease_out_cubic(clamp01((t - (A["protocol_a"] - 0.05)) / 0.3))
    f = font("black", 104)
    for (cx, word_) in ((290, "HTTP"), (790, "MCP")):
        wt = text_width(word_, f)
        x = cx - wt / 2
        for i, ch in enumerate(word_):
            cw = text_width(ch, f)
            last = i == len(word_) - 1
            rgb = AMBER if (last and glow > 0) else WHITE
            draw_text(L, ch, f, x + cw / 2, 850, rgb=rgb, a=255 * v, scale=1.0 + (0.18 * glow if last else 0.0),
                      glow=(255, 170, 60) if last else None, glow_a=210 * glow, shadow=10, shadow_a=170)
            x += cw
    if glow > 0:
        draw_text(L, "=", font("black", 90), W / 2 + 10, 845, rgb=WHITE, a=255 * v * glow, shadow=10, shadow_a=170)


# ============================================================================
# the last line: every app, one standard, into the model. Then the black
# ============================================================================
@ev(beat_start("end") - 0.05, DUR)
def ending(ctx, t):
    L = ctx.front
    t_out = A["nhat"] - 0.15
    hub_y, ai_y, row_y = 580, 750, 390
    for k_, (x_, ic) in enumerate(APPS):
        badge(ctx, t, A["tat_e"] - 0.1 + 0.1 * k_, t_out, x_, row_y, 56, ic, SKY)
        wire(L, t, A["ket"] - 0.05 + 0.05 * k_, t_out, x_, row_y + 66, lerp(x_, W / 2, 0.6), hub_y - 44, rgb=AMBER,
             dur=0.3, width=6)
    chip(L, t, A["ket"] - 0.08, t_out, W / 2, hub_y, "MCP", "link", style="glow", size=56, accent=MINT)
    wire(L, t, A["model_e"] - 0.05, t_out, W / 2, hub_y + 50, W / 2, ai_y - 62, rgb=AMBER, dur=0.25, width=6)
    if t >= A["model_e"] - 0.1:
        badge(ctx, t, A["model_e"] - 0.1, t_out, W / 2, ai_y, 56, "brain", MINT)
    depth_word(ctx, t, A["nhat"] - 0.06, A["hieu"] - 0.1, "NHẤT QUÁN", size=240, kind="serif_ib", rgb=GOLD,
               tracking=0.0, enter="pop", stagger=0.04, fade_out=0.05, glow=(255, 170, 60))
    depth_word(ctx, t, A["hieu"] - 0.06, DUR - 0.01, "HIỆU QUẢ", size=250, gradient=(WHITE, MINT), enter="scale",
               fade_out=0.02, sheen=0.25)


# ============================================================================
# the title on black, then the call to follow
# ============================================================================
TITLE_T = DUR + 0.35
CTA_T = DUR + 2.5


@card(DUR, TOTAL + 1, close=0.0, open_=0.0)      # a hard cut to black on "vậy thôi."
def k_end(ctx, t, t0, t1):
    L = ctx.ui
    up = ease_in_out_cubic(clamp01((t - (CTA_T - 0.25)) / 0.45))
    y = H / 2 + 40 - 290 * up
    title_slam(L, t, TITLE_T, "MCP", sub="Cổng USB chung cho bộ não AI.", y=y)
    if t >= CTA_T:
        card_text(L, t, CTA_T, TOTAL + 1, "Follow để biết cắm gì vào AI…", 70, kind="bold", size=60, track=0.0,
                  push=0.0)
        card_text(L, t, CTA_T, TOTAL + 1, "trước khi AI cắm luôn", 175, kind="serif_ib", size=62, rgb=AMBER, track=0.0,
                  push=0.0, delay=0.9, glow=(255, 170, 60))
        card_text(L, t, CTA_T, TOTAL + 1, "vào não bạn.", 260, kind="serif_ib", size=62, rgb=AMBER, track=0.0,
                  push=0.0, delay=1.05, glow=(255, 170, 60))


flash(TITLE_T)


# ============================================================================
# sound: cues on top, then the trailer score
# ============================================================================
cue(A["mcp_h"] - 0.1, "whoosh", 0.45, length=0.5, direction=1)
for k_ in range(3):
    cue(A["nhac_h"] - 0.25 + 0.14 * k_, "pop", 0.35, f0=520 + 80 * k_, f1=1000 + 120 * k_)
cue(A["tung"] - 0.08, "pop", 0.4, f0=520, f1=1000)
cue(A["mcp_n"] - 0.1, "whoosh", 0.35, length=0.35, direction=1)
for key_, f_ in (("model_n", 1046.5), ("context_n", 1174.66), ("protocol_n", 1318.5)):
    cue(A[key_] - 0.06, "ding", 0.25, f=f_)
cue(A["ngon_m"] - 0.08, "pop", 0.4, f0=560, f1=1080)
cue(A["nham"] - 0.08, "glitch", 0.45)
cue(A["claude_y"] - 0.08, "pop", 0.4, f0=600, f1=1150)
cue(A["thuc"] - 0.02, "swipe", 0.45)
cue(A["claude_t"] - 0.08, "pop", 0.4, f0=520, f1=1000)
cue(A["model_t"] - 0.05, "whoosh", 0.35, length=0.35, direction=1)
cue(A["opus"] - 0.08, "ding", 0.3, f=1567.98)
cue(A["model_b"] - 0.1, "pop", 0.4, f0=480, f1=900)
cue(A["mat"] - 0.08, "glitch", 0.3)
cue(A["tay"] - 0.08, "glitch", 0.3)
cue(A["tay_p"] - 0.04, "connect", 0.4)
cue(A["mat_p"] - 0.04, "connect", 0.4)
cue(A["lam_p"] - 0.05, "shimmer", 0.35)
cue(A["gmail"] - 0.08, "pop", 0.4, f0=560, f1=1080)
cue(A["cam_g"] - 0.05, "connect", 0.4)
cue(A["file"] - 0.08, "pop", 0.4, f0=620, f1=1180)
cue(A["notion"] - 0.05, "connect", 0.4)
cue(A["laptop"] - 0.1, "pop", 0.35, f0=480, f1=900)
cue(A["usb"] - 0.1, "pop", 0.35, f0=600, f1=1120)
cue(A["cam_u"] - 0.05, "swipe", 0.35)
cue(A["vao"] - 0.05, "connect", 0.45)
cue(A["chuan"] - 0.08, "pop", 0.4, f0=520, f1=1000)
for k_ in range(4):
    cue(A["dung"] - 0.1 + 0.12 * k_, "pop", 0.3, f0=560 + 60 * k_, f1=1080 + 80 * k_)
cue(A["tat_p"] - 0.05, "connect", 0.35)
cue(A["trong"] - 0.1, "typing", 1.0, until=A["http"] + 0.25)
cue(A["http"] + 0.1, "ding", 0.3, f=1318.5)
cue(A["dia"] - 0.08, "pop", 0.35, f0=600, f1=1150)
cue(A["protocol_a"] - 0.05, "shimmer", 0.4)
for k_ in range(4):
    cue(A["tat_e"] - 0.1 + 0.1 * k_, "pop", 0.3, f0=560 + 60 * k_, f1=1080 + 80 * k_)
cue(A["ket"] - 0.05, "connect", 0.4)
cue(A["model_e"] - 0.1, "ding", 0.3, f=1567.98)
cue(CTA_T, "shimmer", 0.4)
cue(CTA_T + 0.9, "pop", 0.35, f0=520, f1=1000)

# act I: a boom as the bars slide in, a drone and a heartbeat under her question, a braam on the date card
score("boom", 0.0)
score("pad", 0.0, notes=[38, 45, 50], dur=G_DATE[0], gain=0.9, bright=0.12, att=0.25, rel=0.6)
score("heartbeat", 0.35, until=G_DATE[0] - 0.3, bpm=72)
score("taiko", A["mcp_h"] - 0.04, gain=0.7, f0=140, f1=60)
score("braam", G_DATE[0] + 0.12, chord=BB_MAJ, length=3.0)
score("boom", G_DATE[0] + 0.12, gain=0.7)
# act II: a pad under "từng từ", a hit on each of the three words, a hit on the M card
score("pad", beat_start("word"), notes=[46, 50, 53, 58], dur=G_M[0] - beat_start("word") + 0.2, gain=0.7, bright=0.25,
      att=0.4, rel=0.5)
for key_ in ("model_n", "context_n", "protocol_n"):
    score("taiko", A[key_] - 0.04, gain=0.5, f0=125, f1=55)
score("taiko", G_M[0] + 0.05, gain=0.65, f0=150, f1=60)
score("boom", G_M[0] + 0.05, gain=0.5, length=1.4)
# the myth: an ostinato builds, a riser into the breath of black, then the truth under a low braam
score("ostinato", beat_start("model"), until=G_TR[0] - 0.05, bpm=100)
score("riser", G_TR[0], length=G_TR[0] - A["nham"] + 0.3, gain=0.8)
score("swell", A["thuc"] - 0.05, length=0.4, gain=0.7)
score("braam", A["thuc"] - 0.04, chord=D_MAJ, length=3.0, gain=0.38)
score("pad", beat_start("truth"), notes=[50, 54, 57, 62], dur=G_C[0] - beat_start("truth") + 0.2, gain=0.75, bright=0.3,
      att=0.3, rel=0.4)
score("bells", A["opus"] - 0.04, notes=[74, 78, 81])
score("taiko", G_C[0] + 0.05, gain=0.65, f0=150, f1=60)
score("boom", G_C[0] + 0.05, gain=0.5, length=1.4)
# act III: a dark pad and a heartbeat under the brain without eyes or hands, a swell as he plugs them in,
# the drive under Gmail and Notion, then the warm part: the drive stops for the laptop and the USB stick
score("pad", beat_start("context"), notes=[38, 45, 50, 53], dur=beat_start("plug") - beat_start("context"), gain=0.8,
      bright=0.25, att=0.6, rel=0.3, trem=0.3)
score("heartbeat", beat_start("brain") + 0.1, until=beat_end("noeyes") - 0.2, bpm=80, gain=0.8)
score("taiko", A["mat"] - 0.05, gain=0.4, f0=120, f1=55)
score("taiko", A["tay"] - 0.05, gain=0.45, f0=120, f1=55)
score("swell", beat_start("plug"), length=0.4, gain=0.6)
score("pad", beat_start("plug"), notes=[50, 54, 57, 62], dur=beat_end("plug") - beat_start("plug"), gain=0.75, bright=0.3,
      att=0.3, rel=0.2)
score("riser", beat_start("gmail"), length=1.4, gain=0.6)
score("drive", beat_start("gmail"), until=beat_end("notion"), bpm=120)
for tc_ in (beat_start("gmail"), beat_start("gmail2"), beat_start("notion")):
    score("taiko", tc_, gain=0.65, f0=135, f1=55)
score("swell", beat_start("usb"), length=0.4, gain=0.6)
score("pad", beat_start("usb"), notes=[50, 54, 57, 62, 66], dur=beat_end("usb") - beat_start("usb") + 0.1, gain=0.85,
      bright=0.25, att=0.5, rel=0.5)
score("bells", A["usb"] - 0.05, notes=[74, 78, 81])
score("bells", A["vao"] - 0.05, notes=[76, 79, 83])
score("braam", G_P[0] + 0.12, chord=BB_MAJ, length=3.0)
score("boom", G_P[0] + 0.12, gain=0.7)
# act IV: a pad and a heartbeat under "giao thức chuẩn chung", a riser into the twist card, near silence on it,
# a piano under the typing, a hit on HTTP, bells on her "À"
score("pad", beat_start("protocol"), notes=[46, 50, 53, 58], dur=G_TW[0] - beat_start("protocol"), gain=0.75,
      bright=0.25, att=0.4, rel=0.2)
score("heartbeat", A["giao"], until=G_TW[0] - 0.2, bpm=88, gain=0.85)
score("taiko", A["chuan"] - 0.05, gain=0.5, f0=130, f1=58)
score("taiko", A["dung"] - 0.05, gain=0.5, f0=130, f1=58)
score("riser", G_TW[0], length=G_TW[0] - A["tat_p"] + 0.4, gain=0.8)
score("pad", G_TW[0], notes=[38, 45], dur=G_TW[1] - G_TW[0] + 0.3, gain=0.6, bright=0.1, att=0.2, rel=0.4)
score("piano", A["trong"] - 0.1, notes=[(0.0, 62), (0.3, 66), (0.6, 69)])
score("swell", A["http"] - 0.05, length=0.35, gain=0.7)
score("braam", A["http"] - 0.04, chord=D_MIN, length=3.0, gain=0.4)
score("boom", A["http"] - 0.04, gain=0.5)
score("bells", A["a_a"] - 0.04, notes=[79, 83, 86])
# the last line: the drive comes back, stops on "nhất quán", a heartbeat and a riser into the black
score("drive", beat_start("end"), until=A["nhat"] - 0.1, bpm=120)
score("taiko", A["ket"] - 0.05, gain=0.6, f0=135, f1=55)
score("taiko", A["model_e"] - 0.05, gain=0.6, f0=135, f1=55)
score("heartbeat", A["nhat"], until=DUR - 0.3, bpm=96, gain=0.9)
score("riser", DUR, length=DUR - A["nhat"] + 0.2)
# the title, then a lighter tail under the call to follow
score("swell", TITLE_T, length=0.35, gain=0.8)
score("braam", TITLE_T - 0.01, chord=D_MIN + [50], length=3.0, gain=1.15)
score("boom", TITLE_T - 0.01, length=3.0)
score("crash", TITLE_T - 0.01, gain=0.9)
score("pad", CTA_T - 0.2, notes=[50, 57, 62, 66], dur=TOTAL - CTA_T, gain=0.6, bright=0.2, att=0.6, rel=0.3)
score("piano", CTA_T, notes=[(0.0, 62), (0.45, 69), (0.9, 74), (1.6, 78)])
