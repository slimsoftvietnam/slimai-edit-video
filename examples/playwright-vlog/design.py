"""Tập 16 · Playwright (IMG_8457): the vlog style's worked example, a 4:44 YouTube cut of a 6.6-minute talk.

The user, 2026-11-25: "làm thêm 1 phiên bản ngang cho youtube nhưng biên tập theo phong cách tiêu chuẩn thật chill kiểu
vlog du lịch"; colour "Màu phim ấm"; music "Nhạc do code viết"; then "biên tập hình nên khớp beat nhạc mới tạo cảm xúc".
Approved, then put in the skill as the style "Vlog chill (khớp nhạc)" (references/vlog.md).

The cut comes from vlog_cut.json through beat_fit.py: every cut on the beat, chapters on downbeats. setup() does the
fixed parts (reframes every two bars, chapter cards and tags, captions off over B-roll, the opening overlay); this file
writes the content, chapter by chapter, with every graphic timed by on() so it lands on a beat or a half beat.
pieces.py holds the mock sign-in page and its code; design_b.py chapters 4-7 and the end card.
"""
from vlog import *
import vlog as V
from pieces import *

assert YT, "this design is laid out for the 16:9 YouTube format only"

# ----------------------------------------------------------------------------
# captions
# ----------------------------------------------------------------------------
KEYS.update({
    "playwright": ("xbold", MINT, 1.0), "kịch bản": ("serif_ib", AMBER, 1.2), "nhà biên kịch": ("serif_ib", AMBER, 1.2),
    "biên kịch": ("serif_ib", AMBER, 1.2), "trình duyệt": ("xbold", WHITE, 1.0), "computer use": ("xbold", SKY, 1.0),
    "đọc mã": ("serif_ib", MINT, 1.22), "không nhìn": ("serif_ib", CORAL, 1.15), "token": ("xbold", AMBER, 1.0),
    "tiết kiệm": ("serif_ib", MINT, 1.2), "html": ("xbold", SKY, 1.0), "javascript": ("xbold", SKY, 1.0),
    "button": ("xbold", SKY, 1.0), "login": ("xbold", SKY, 1.0), "username": ("xbold", SKY, 1.0),
    "password": ("xbold", SKY, 1.0), "zalo": ("xbold", SKY, 1.0), "tự động": ("serif_ib", AMBER, 1.15),
    "20": ("black", AMBER, 1.15), "comment": ("xbold", AMBER, 1.0), "skill": ("xbold", MINT, 1.0),
    "như là người": ("serif_ib", AMBER, 1.15), "bộ não": ("serif_ib", AMBER, 1.15), "làm sao": ("serif_ib", AMBER, 1.2),
    "tất cả": ("serif_ib", AMBER, 1.2), "tóm lại": ("serif_ib", AMBER, 1.15),
})
KEEP_CASE.update({"playwright": "Playwright", "zalo": "Zalo", "html": "HTML", "javascript": "JavaScript", "abc": "ABC"})
NO_BREAK.update({"Playwright", "Zalo", "HTML", "JavaScript", "ABC", "AI"})
COMPOUNDS.update({"trình duyệt", "kịch bản", "máy tính", "điều khiển", "thư viện", "đăng nhập", "tin nhắn", "nhắn tin",
                  "màn hình", "giao diện", "mã nguồn", "trang web", "biên kịch", "nhà biên", "tự động", "suy luận",
                  "tiết kiệm", "sử dụng", "phần mềm", "thao tác", "chế độ", "computer use", "thông tin", "văn bản",
                  "đường link", "bước 1", "bước 2", "bước 3", "bước 4", "ví dụ", "cơ bản", "cơ chế", "hiệu quả",
                  "trường hợp", "phương pháp", "vị trí", "quy trình", "bộ não", "năng lực", "thông minh", "quá trình",
                  "thực thi", "vấn đề", "bình thường", "tác vụ", "20 người", "20 lần", "cái mã", "cái nút", "cái thẻ",
                  "nút login", "mã html", "zalo web", "thiết kế", "tự mở", "tự bấm", "tự gõ", "mở web", "như thế",
                  "hai cái", "một cái", "cái skill", "phần comment", "khó viết", "viết đúng", "lần đầu", "lần sau",
                  "bắt đầu", "ban đầu", "mắt thường", "cảm giác", "toàn bộ", "phức tạp", "tóm lại", "rất nhiều",
                  "chụp ảnh", "tìm ra", "quay lại", "nhiệm vụ", "tab mới", "hình như", "tại sao", "ở đây",
                  # pairs a line should not end between (seen in the first render's captions)
                  "bước 1:", "bước 2:", "cái ô", "của nó", "động hóa", "lần nào", "cái model", "và có", "có vấn",
                  "bạn em", "cho bạn", "của mình", "nó sẽ", "mà nó", "nó nhìn", "anh sẽ", "sẽ biết", "để em",
                  "em nhập", "em làm", "làm được", "có tên", "đã có", "một kịch", "nó thông", "để sử", "thì có",
                  "đến nó", "nó đọc", "của cái", "trên trình", "cái thư", "với trình", "nó đang", "có nhìn",
                  "bấm vào", "bản đấy", "đọc mã", "các step", "những người", "nếu có", "có playwright", "có tốn",
                  "tốn token", "token của", "là abc", "cái kịch", "tải về", "khiển zalo", "comment playwright",
                  "vào nút", "nhập tên", "sẽ cần", "sẽ hiệu"})

# ----------------------------------------------------------------------------
# the picture's rhythm: chapters, shots that change on bar lines, light leaks, a small push on each chapter's downbeat
# ----------------------------------------------------------------------------
TITLES = {1: "AI tự điều khiển máy tính?", 2: "playwright là gì?", 3: "vì sao là “nhà biên kịch”?",
          4: "AI có nhìn màn hình không?", 5: "làm được những gì?", 6: "có tốn token không?",
          7: "nhận skill điều khiển Zalo"}
T_LIVE = gb(4)                     # the bar-2 downbeat: the opening B-roll cuts to her
T_END = V.T_END                    # she walks off: the end card starts
setup(TITLES, yt_chapters={
    1: "AI tự điều khiển máy tính bằng cách nào?", 2: "Playwright là gì?",
    3: "Vì sao gọi là “nhà biên kịch”: kịch bản 4 bước", 4: "AI có nhìn màn hình không? Đọc mã chứ không nhìn",
    5: "Playwright làm được gì: ví dụ nhắn tin Zalo", 6: "Dùng Playwright có tốn token không?",
    7: "Cách nhận skill Playwright điều khiển Zalo"},
    tag_holds={1: 2.6, 3: 0.9}, no_tags=(7,),            # chapter 3 opens with the dictionary card in the top band
    pip_view={"M": (800.0, 12.0), "W": (720.0, -22.0)})  # the two sit close: each PiP card shows one person
# the music, per chapter: (first bar from 1, style, progression); calm under the questions, fuller under the examples
V.ARRANGE.update({
    1: [(1, "intro", "main"), (2, "stroll", "main"), (5, "light", "main")],
    2: [(1, "stroll", "main")],
    3: [(1, "light", "calm"), (5, "groove", "main"), (11, "light", "main")],
    4: [(1, "break", "calm"), (3, "light", "main"), (7, "stroll", "main"), (12, "break", "calm"), (14, "light", "main"),
        (17, "groove", "main")],
    5: [(1, "break", "calm"), (2, "groove", "main"), (9, "light", "calm"), (13, "stroll", "main")],
    6: [(1, "break", "calm"), (3, "light", "main"), (6, "groove", "main"), (10, "light", "calm"), (14, "break", "calm")],
    7: [(1, "lift", "main"), (6, "outro", "calm")],
})


# ============================================================================
# CHAPTER 1 · the opening: she walks in under her own voice, then asks
# ============================================================================
@ev(-0.5, T_LIVE + 0.02)
def opening(ctx, t):
    if V.overlay_at(t) is None:          # the B-roll of her walking in (vlog_cut.json overlays; setup() draws it)
        return
    V.shade(ctx.mid, 0, 620, 150, 0)
    L = ctx.front
    # the title block sits on the right, over the trees: she crosses the left and the middle of the frame
    xr = 1812
    k0 = ease_out_cubic(clamp01((t + 0.25) / 0.45))
    draw_text(L, "tập 16 · playwright", font("bold", 36), xr - 4, 122 + (1 - k0) * 10, rgb=AMBER, a=255, align="right",
              tracking=7.0, shadow=10, shadow_a=180)
    for i, (line, yb) in enumerate((("AI tự điều khiển", 232), ("máy tính", 340))):
        fnt = font("xbold", 108)
        tw_ = text_width(line, fnt, -0.02 * 108)
        big_text(L, t, -0.42 + 0.06 * i, T_LIVE, line, xr - tw_ / 2, yb, size=108, kind="xbold", rgb=WHITE, max_w=1000,
                 tracking=-0.02, enter="settle", stagger=0.010, shadow=16, fade_out=0.001)
    # beat 3: the question, with a marker line under it on beat 4
    fnt = font("serif_ib", 112)
    tw_ = text_width("bằng cách nào?", fnt)
    r = big_text(L, t, gb(2) - 0.03, T_LIVE, "bằng cách nào?", xr - tw_ / 2, 458, size=112, kind="serif_ib", rgb=AMBER, max_w=1000,
                 tracking=0.0, enter="rise", stagger=0.022, shadow=16, fade_out=0.001, glow=(255, 170, 60), glow_a=90)
    if r is not None and t >= gb(3):
        V.underline(L, xr - tw_ + 6, xr - 6, 488, clamp01((t - gb(3)) / 0.4), rgb=AMBER, a=235, width=6)


cue(0.04, "whoosh", 0.32, length=0.7, direction=1)
cue(gb(2), "pop", 0.3, f0=520, f1=980)
cue(T_LIVE, "shutter", 0.3)


@ev(T_LIVE - 0.05, CUT["modes"] + 0.05)
def her_question(ctx, t):
    # a small browser does what she says, each action on its beat: opens a page, clicks, types
    t_open, t_click, t_type = on("open", "mở"), on("open", "bấm"), on("open", "gõ")
    t_out = on("open", "thì")
    v = V.fade(t, t_open - 0.02, t_out, 0.12, 0.25)
    if v > 0:
        L = ctx.front
        a = 255 * v
        s = 0.80
        x0, y0, wv, hv = 1190, 74, 760, 400
        kpop = 0.7 + 0.3 * V.pop(t, t_open)
        with V.tilt(L, x0 + wv * s / 2, y0 + hv * s / 2, 0.0, kpop):
            with scaled(L, x0, y0, s):
                page = U.window(L, (0, 0, wv, hv), a, url="trang-web.vn", url_k=clamp01((t - t_open) / 0.5), t=t,
                                typing=t < t_open + 0.5, r=26, bar=70)
                c = L.c
                px0, py0, px1, py1 = page
                kp = clamp01((t - t_open - 0.5) / 0.3)                      # the page loads
                if kp > 0:
                    c.drawRRect(rrect(px0 + 40, py0 + 34, px0 + 330, py0 + 70, 10), fill(U.LINE, a * kp))
                    c.drawRRect(rrect(px0 + 40, py0 + 92, px1 - 330, py0 + 116, 8), fill(U.LINE, a * kp * 0.7))
                    press = 1.0 if t_click - 0.02 <= t < t_click + 0.12 else 0.0
                    U.button(L, px1 - 290, py0 + 30, 250, 62, "Đăng nhập", a * kp, press=press,
                             done=clamp01((t - t_click) / 0.25), size=28)
                    U.field(L, px0 + 40, py0 + 178, wv - 80, 72, None, "xin chào, mình là AI", clamp01((t - t_type) / 0.75),
                            a * kp, t=t, focus=t >= t_type - 0.3, size=32)
        cur = U.Cursor([(t_open + 0.3, x0 + 300, y0 + 250), (t_click, x0 + (wv - 165) * s, y0 + (70 + 62) * s),
                        (t_type - 0.05, x0 + 120 * s, y0 + (70 + 214) * s)], clicks=[t_click], move=0.42, scale=2.6,
                       t_in=t_open + 0.3, t_out=t_out)
        cur.draw(L, t, a)
        L.mark(x0 - 20, y0 - 20, x0 + wv * s + 20, y0 + hv * s + 40)
    # her question stands behind her
    depth_word(ctx, t, on("open", "sao") - 0.02, CUT["modes"], "làm sao?", size=250, kind="serif_ib", rgb=AMBER,
               glow=(255, 170, 60), enter="rise", stagger=0.03, tracking=0.0, fade_out=0.12, spk="W")


cue(on("open", "mở"), "pop", 0.3, f0=480, f1=900)
cue(on("open", "bấm"), "click", 0.42)
cue(on("open", "gõ"), "typing", 0.3, until=on("open", "gõ") + 0.75)
cue(on("open", "sao"), "shimmer", 0.3)


@ev(CUT["modes"] - 0.05, CARD["card2"] + 0.05)
def two_modes(ctx, t):
    """he narrows it down: two ways an AI drives a computer; this video is about the first"""
    L = ctx.front
    t_a, t_b = on("modes", "Một"), on("modes", "hai", 2)
    t_pick = on("modes", "hẹp")
    t_out = CARD["card2"]
    t_k = on("modes", "hai", 1)
    v = V.fade(t, t_k, t_out, 0.2, 0.001)
    if v > 0:
        kk = ease_out_cubic(clamp01((t - t_k) / 0.45))
        draw_text(L, "AI điều khiển máy tính · 2 chế độ", font("bold", 40), W / 2, 96 + (1 - kk) * 10, rgb=AMBER, a=255 * v,
                  align="center", tracking=5.0, shadow=10, shadow_a=180)
    pick = clamp01((t - t_pick) / 0.35)
    V.mini(L, 680, 212, 540, 156, t, t_a, t_out, "trình duyệt", "chỉ riêng trình duyệt", num="1", accent=MINT, glow=pick)
    V.mini(L, 1250, 212, 560, 156, t, t_b, t_out, "computer use", "toàn bộ máy tính, mọi phần mềm", num="2", accent=SKY,
           dim=pick)
    if pick > 0 and t < t_out:
        chip(L, t, t_pick + BEAT / 2, t_out, 680, 334, "video này nói về cái này", "check", style="glow", size=32, accent=MINT)


cue(on("modes", "Một"), "pop", 0.3, f0=520, f1=980)
cue(on("modes", "hai", 2), "pop", 0.3, f0=600, f1=1120)
cue(on("modes", "hẹp"), "tick", 0.35, f=2500)


# ============================================================================
# CHAPTER 2 · playwright là gì?
# ============================================================================
@ev(DOWN[2] - 0.05, CARD["card3"] + 0.05)
def what_is_it(ctx, t):
    t_name = on("lib", "Playwright", 1, div=1)
    t_like = on("job2", "như")
    # the name stands behind him from the beat he says it
    depth_word(ctx, t, t_name - 0.03, t_like - 0.05, "playwright", size=300, kind="black", gradient=(WHITE, (190, 255, 236)),
               enter="rise", stagger=0.03, fade_out=0.14, sheen=0.5, spk="M")
    side_chip(ctx, t, t_name + BEAT, t_like - 0.05, "M", 0, "mã nguồn mở", "code", MINT)
    side_chip(ctx, t, t_name + 2 * BEAT, t_like - 0.05, "M", 1, "của Microsoft", "spark", AMBER)
    # its job: it works the browser the way a person does
    depth_word(ctx, t, t_like - 0.02, CUT["examples"] + BEAT, "như người", size=280, kind="serif_ib", rgb=AMBER,
               glow=(255, 170, 60), enter="rise", stagger=0.03, tracking=0.0, fade_out=0.15, spk="M")
    # what it can do, one chip per beat it is said on
    V.chip_row(ctx.front, t, [("login", "user", on("examples", "login"), MINT), ("mở tab mới", "browser", on("examples", "tab"), AMBER),
                              ("điền thông tin", "list", on("examples", "điền"), MINT),
                              ("nhập văn bản", "file", on("examples", "nhập"), AMBER)], 204, CARD["card3"], size=44, gap=28)


cue(on("lib", "Playwright", 1, div=1), "impact", 0.22, length=1.4)
cue(on("lib", "Playwright", 1, div=1) + BEAT, "pop", 0.28, f0=520, f1=980)
cue(on("lib", "Playwright", 1, div=1) + 2 * BEAT, "pop", 0.28, f0=600, f1=1120)
cue(on("job2", "như"), "shimmer", 0.28)
for _w, _f in (("login", 520), ("tab", 580), ("điền", 640), ("nhập", 700)):
    cue(on("examples", _w), "pop", 0.28, f0=_f, f1=_f * 1.9)


# ============================================================================
# CHAPTER 3 · vì sao là "nhà biên kịch": a script of four steps
# ============================================================================
T_DICT = on("name", "nghĩa")
T_DICT2 = on("name", "nhà")
T_WHY = on("name", "kịch", 3)                 # "Thì tại sao lại là kịch bản?"
T_PIP3 = qb(w("name", "Ví")) - BEAT / 2       # the speaker shrinks into the card: done on the beat of "Ví dụ…"
T_STEP = [on("name", "bước", 1), on("name", "Bước", 2), on("name", "Bước", 3), on("name", "Bước", 4)]
T_ACT = [on("name", "mở"), on("name", "điền"), on("name", "nhập", 2), on("name", "ấn")]
T_ONE = on("name", "step")
T_RUN = on("name", "run")
T_DONE = q(w("name", "xong") - 0.2)            # the stamp lands on "là xong", half a beat before the cut
T_PIP3_OUT = CUT["human"]                     # he grows back to the full frame as the next line starts
PIP.append((T_PIP3, T_PIP3_OUT))


@ev(DOWN[3] - 0.05, T_PIP3 + 0.3)
def the_name(ctx, t):
    # a page of the journal: the dictionary entry
    v = V.fade(t, T_DICT, T_WHY, 0.1, 0.22)
    if v > 0:
        L = ctx.front
        cx, cy, wd, hd = 960, 190, 860, 224
        k = 0.7 + 0.3 * V.pop(t, T_DICT)
        with V.tilt(L, cx, cy, -2.0, k):
            V.paper(L, cx - wd / 2, cy - hd / 2, cx + wd / 2, cy + hd / 2, v)
            x = cx - wd / 2 + 48
            draw_text(L, "play·wright", font("serif_b", 78), x, cy - 16, rgb=INKB, a=255 * v, align="left")
            wn = text_width("play·wright", font("serif_b", 78))
            U.text(L.c, "/ˈpleɪ.raɪt/", V.ipa_font(36), x + wn + 30, cy - 20, (128, 112, 96), 255 * v)
            draw_text(L, "danh từ", font("medium", 28), cx + wd / 2 - 48, cy - 22, rgb=(128, 112, 96), a=255 * v, align="right")
            k2 = clamp01((t - T_DICT2) / 0.3)
            if k2 > 0:
                draw_text(L, "nhà biên kịch, người viết kịch bản", font("serif_i", 48), x + (1 - ease_out_cubic(k2)) * 14,
                          cy + 66, rgb=(176, 92, 30), a=255 * v * k2, align="left")
        L.mark(cx - wd / 2 - 30, cy - hd / 2 - 40, cx + wd / 2 + 30, cy + hd / 2 + 40)
    depth_word(ctx, t, T_WHY - 0.02, T_PIP3 + 0.05, "kịch bản?", size=270, kind="serif_ib", rgb=AMBER, glow=(255, 170, 60),
               enter="rise", stagger=0.03, tracking=0.0, fade_out=0.15, spk="M")


cue(T_DICT, "shutter", 0.3)
cue(T_DICT2, "tick", 0.3, f=2300)
cue(T_WHY, "shimmer", 0.28)


@ev(T_PIP3, CUT["human"] + 0.32)
def the_script(ctx, t):
    """the worked example: a sign-in as a script of four steps; then the same script runs again by itself"""
    t0, t1 = T_PIP3 + 0.3, T_PIP3_OUT + 0.25
    h = 610
    v, dy, x0, y0, x1, y1 = panel(ctx, t, t0, t1, h)
    if v <= 0:
        return
    L = ctx.mid
    a = 255 * v
    c = L.c
    icon(c, "list", x0 + 78, y0 + 62 + dy, 50, AMBER, a, sw=5)
    draw_text(L, "kịch bản đăng nhập", font("bold", 42), x0 + 122, y0 + 77 + dy, rgb=WHITE, a=a, align="left")
    # the replay after "run": every step again, a quarter beat apart
    rerun = t >= T_RUN
    rs = [T_RUN + BEAT / 2 + i * BEAT / 2 for i in range(4)]
    acts = rs if rerun else T_ACT
    url_k = clamp01((t - acts[0]) / (0.25 if rerun else 0.6))
    user_k = clamp01((t - acts[1]) / (0.2 if rerun else 0.7))
    pass_k = clamp01((t - acts[2]) / (0.2 if rerun else 0.6))
    press = 1.0 if acts[3] - 0.02 <= t < acts[3] + 0.14 else 0.0
    done = clamp01((t - acts[3] - 0.1) / 0.25)
    if rerun and t < rs[0]:
        url_k = user_k = pass_k = done = 0.0
    focus = None
    if acts[1] - 0.2 <= t < acts[2] - 0.2:
        focus = "user"
    elif acts[2] - 0.2 <= t < acts[3] - 0.1:
        focus = "pass"
    s = 0.70
    wx, wy = x0 + 44, y0 + 118 + dy
    shown = clamp01((t - acts[0] - (0.1 if rerun else 0.45)) / 0.25)
    with scaled(L, wx, wy, s):
        login_page(L, a, t, url_k=url_k, user_k=user_k, pass_k=pass_k, press=press, done=done, focus=focus, wv=640, hv=640,
                   show_page=shown)
        if shown < 1:                                  # an empty new tab until the link is opened
            U.text(c, "tab mới", font("semi", 34), 320, 330, U.MUTE, a * (1 - shown) * 0.85, align="center")
            c.drawRRect(rrect(170, 362, 470, 406, 22), stroke(U.LINE, a * (1 - shown), width=3))
    L.mark(wx, wy, wx + 640 * s, wy + 640 * s + 30)
    # the four steps
    rx = x0 + 44 + 640 * s + 78
    rows = ["mở đường link", "điền username", "nhập password", "ấn nút login"]
    for i, txt in enumerate(rows):
        yy = y0 + 172 + i * 88 + dy
        if t < T_STEP[i]:                              # the steps to come: empty slots, so the eye knows there are four
            step_slot(L, rx, yy, i + 1, v, i % 2)
        step_row(L, rx, yy, i + 1, txt, t, T_STEP[i], a, accent=AMBER, done_t=(rs[i] + 0.12) if rerun else None,
                 hot_t=rs[i] if rerun else None, size=40)
    # "it becomes steps, and the steps are one script"
    k1 = clamp01((t - T_ONE) / 0.4)
    if k1 > 0:
        bx = rx - 44
        ya, yb = y0 + 172 - 44 + dy, y0 + 172 + 3 * 88 + 44 + dy
        c.drawLine(bx, ya, bx, lerp(ya, yb, ease_out_cubic(k1)), stroke(AMBER, 200 * v, width=4))
        draw_text(L, "= một kịch bản", font("serif_ib", 48), rx - 20, yb + 58 + (1 - ease_out_cubic(k1)) * 10, rgb=AMBER,
                  a=a * k1, align="left")
        L.mark(bx - 10, ya, bx + 420, yb + 80)
    # run it again
    kr = clamp01((t - T_RUN + 0.1) / 0.25)
    if kr > 0:
        bw, bh = 250, 70
        bxr, byr = x1 - 60 - bw, y0 + 42 + dy
        pr = 1.0 if T_RUN - 0.02 <= t < T_RUN + 0.16 else 0.0
        with V.tilt(L, bxr + bw / 2, byr + bh / 2, 0.0, (0.7 + 0.3 * V.pop(t, T_RUN - 0.1)) * (1 - 0.05 * pr)):
            c.drawRRect(rrect(bxr, byr, bxr + bw, byr + bh, bh / 2), fill(MINT, 245 * v * kr))
            path = skia.Path()
            path.moveTo(bxr + 36, byr + 20)
            path.lineTo(bxr + 36, byr + bh - 20)
            path.lineTo(bxr + 62, byr + bh / 2)
            path.close()
            c.drawPath(path, fill(INK, 255 * v * kr))
            draw_text(L, "chạy lại", font("bold", 36), bxr + 82, byr + bh / 2 + 13, rgb=INK, a=a * kr, align="left")
        L.mark(bxr - 20, byr - 20, bxr + bw + 20, byr + bh + 20)
    kd = clamp01((t - T_DONE) / 0.3)
    if kd > 0:
        cxw, cyw = wx + 640 * s / 2, wy + 640 * s / 2 + 30
        with V.tilt(L, cxw, cyw, -7.0, 0.6 + 0.4 * V.pop(t, T_DONE)):
            c.drawRRect(rrect(cxw - 150, cyw - 54, cxw + 150, cyw + 54, 18), fill((36, 196, 118), 240 * v * kd))
            draw_text(L, "xong", font("black", 74), cxw - 18, cyw + 26, rgb=WHITE, a=a * kd, align="center")
            U.tick(L, cxw + 104, cyw, 26, a * kd, k=clamp01((t - T_DONE - 0.08) / 0.3), rgb=(255, 255, 255))
        L.mark(cxw - 190, cyw - 90, cxw + 190, cyw + 90)


for _i in range(4):
    cue(T_STEP[_i], "pop", 0.3, f0=480 + 60 * _i, f1=900 + 110 * _i)
cue(T_ACT[0], "typing", 0.26, until=T_ACT[0] + 0.6)
cue(T_ACT[1], "typing", 0.26, until=T_ACT[1] + 0.7)
cue(T_ACT[2], "typing", 0.26, until=T_ACT[2] + 0.6)
cue(T_ACT[3], "click", 0.42)
cue(T_ONE, "swipe", 0.3)
cue(T_RUN, "click", 0.42)
for _i in range(4):
    cue(T_RUN + BEAT / 2 + _i * BEAT / 2, "tick", 0.32, f=2200 + 200 * _i)
cue(T_DONE, "ding", 0.3, f=1318.5)


@ev(CUT["human"] - 0.05, CARD["card4"] + 0.05)
def like_a_person(ctx, t):
    chip(ctx.front, t, on("human", "cảm"), CARD["card4"], W / 2, 204, "trông như người thật đang thao tác", "user", style="glow",
         size=44, accent=AMBER)


cue(on("human", "cảm"), "pop", 0.28, f0=520, f1=980)

import design_b  # noqa: E402,F401  (chapters 4-7 and the ending)
