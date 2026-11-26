"""Chapters 4-7 and the end card of the vlog example (imported at the end of design.py; same clock, same helpers)."""
from vlog import *
import vlog as V
from pieces import *

T_END = V.T_END


# ============================================================================
# CHAPTER 4 · it reads the page's code, it does not look at the screen
# ============================================================================
@ev(DOWN[4] - 0.05, CUT["code"] + 0.05)
def she_doubts(ctx, t):
    depth_word(ctx, t, on("see", "nhìn") - 0.02, CUT["code"], "có nhìn đâu?", size=230, kind="serif_ib", rgb=CORAL,
               glow=(255, 90, 60), enter="rise", stagger=0.025, tracking=0.0, fade_out=0.12, spk="W")
    side_chip(ctx, t, on("see", "bấm"), CUT["code"], "W", 0, "sao bấm đúng nút?", "warn", AMBER, size=36)


cue(on("see", "nhìn"), "shimmer", 0.28)
cue(on("see", "bấm"), "pop", 0.28, f0=520, f1=980)

T_SHOT, T_NOT, T_READ = on("code", "chụp"), on("code", "đâu."), on("code", "đọc")


@ev(CUT["code"] - 0.05, CUT["tag"] + 0.05)
def not_a_screenshot(ctx, t):
    L = ctx.front
    side_chip(ctx, t, on("code", "vẫn"), on("code", "Thì") - 0.05, "M", 0, "AI vẫn nhìn được", "camera", SKY)
    t_out = CUT["tag"]
    r = V.mini(L, 670, 212, 560, 156, t, T_SHOT, t_out, "chụp ảnh màn hình", "rồi tìm cái nút trong ảnh", icon_kind="camera",
               accent=CORAL, dim=clamp01((t - T_NOT) / 0.3))
    if r is not None and t >= T_NOT:
        strike_line(L, r[0] + 24, r[2] - 24, 212, clamp01((t - T_NOT) / 0.3), rgb=CORAL, a=255, width=8)
    V.mini(L, 1250, 212, 560, 156, t, T_READ, t_out, "đọc mã trang web", "biết chính xác đâu là nút", icon_kind="code",
           accent=MINT, glow=clamp01((t - T_READ) / 0.4))


cue(on("code", "vẫn"), "pop", 0.26, f0=520, f1=980)
cue(T_SHOT, "shutter", 0.3)
cue(T_NOT, "swipe", 0.34)
cue(T_READ, "pop", 0.32, f0=620, f1=1180)

T_PIP4 = qb(w("tag", "đọc")) - BEAT / 2
T_PIP4_OUT = CUT["nolook"]
T_LINK = on("tag", "nút")
T_BTN = on("tag", "button,")
T_PW = on("tag", "Playwright")
T_JS = on("tag", "JavaScript.")
PIP.append((T_PIP4, T_PIP4_OUT))


@ev(T_PIP4, CUT["nolook"] + 0.32)
def the_tag(ctx, t):
    """the button on the page and the tag behind it: Playwright reads the tag and acts on it with JavaScript"""
    t0, t1 = T_PIP4 + 0.3, T_PIP4_OUT + 0.25
    h = 600
    v, dy, x0, y0, x1, y1 = panel(ctx, t, t0, t1, h)
    if v <= 0:
        return
    L = ctx.mid
    a = 255 * v
    c = L.c
    draw_text(L, "trên màn hình", font("bold", 34), x0 + 50, y0 + 66 + dy, rgb=(220, 220, 210), a=a, align="left")
    draw_text(L, "trong mã trang web", font("bold", 34), x0 + 500, y0 + 66 + dy, rgb=MINT, a=a, align="left")
    s = 0.60
    wx, wy = x0 + 44, y0 + 96 + dy
    click = t >= T_JS + BEAT / 2
    press = 1.0 if T_JS + BEAT / 2 - 0.02 <= t < T_JS + BEAT / 2 + 0.14 else 0.0
    with scaled(L, wx, wy, s):
        login_page(L, a, t, user_k=1.0, pass_k=1.0, press=press, done=clamp01((t - T_JS - BEAT / 2 - 0.1) / 0.25), wv=640, hv=640,
                   hot_btn=clamp01((t - T_LINK) / 0.3) * (0.0 if click else 1.0))
    L.mark(wx, wy, wx + 640 * s, wy + 640 * s + 30)
    # the code, typed while he says "nó đọc cái mã"
    cx0, cy0 = x0 + 480, y0 + 112 + dy
    c.drawRRect(rrect(cx0, cy0, x1 - 40, cy0 + 300, 22), fill((16, 20, 30), 235 * v))
    hot = 3 if t >= T_LINK else None
    code_lines(L, cx0 + 26, cy0 + 62, FORM_CODE, a, size=22, k=clamp01((t - t0) / 1.6), lh=2.0, hot=hot,
               hot_a=clamp01((t - T_LINK) / 0.3), hot_rgb=AMBER, width=x1 - 40 - cx0 - 30)
    L.mark(cx0, cy0, x1 - 40, cy0 + 300)
    # the thread from the button on the page to its tag
    kl = clamp01((t - T_LINK) / 0.45)
    if kl > 0:
        bx, by = wx + (640 - 56) * s + 6, wy + (72 + 401) * s
        tx, ty = cx0 + 14, cy0 + 62 + 3 * 22 * 2.0 - 7
        path = skia.Path()
        path.moveTo(bx, by)
        path.cubicTo(bx + 70, by, tx - 80, ty, tx, ty)
        E_ = stroke(AMBER, 255 * v, width=4)
        pm = skia.PathMeasure(path, False)
        seg = skia.Path()
        pm.getSegment(0, pm.getLength() * ease_out_cubic(kl), seg, True)
        c.drawPath(seg, E_)
        c.drawCircle(bx, by, 8, fill(AMBER, a))
        L.mark(min(bx, tx) - 20, min(by, ty) - 20, max(bx, tx) + 20, max(by, ty) + 20)
    yy = cy0 + 352
    chip(L, t, T_BTN, t1, cx0 + 8, yy, "thẻ <button>", "code", style="glow", size=34, accent=AMBER, anchor="left", alpha=v)
    chip(L, t, T_PW, t1, cx0 + 8, yy + 84, "playwright đọc mã này", "check", style="glow", size=34, accent=MINT, anchor="left",
         alpha=v)
    kj = clamp01((t - T_JS) / 0.3)
    if kj > 0:
        c.drawRRect(rrect(cx0 + 348, yy - 36, x1 - 40, yy + 36, 14), fill((16, 20, 30), 235 * v * kj))
        code_lines(L, cx0 + 368, yy + 9, [[("button", C_TXT), (".click()", C_ATTR)]], a * kj, size=26, k=clamp01((t - T_JS) / 0.4))
        draw_text(L, "JavaScript", font("semi", 24), x1 - 56, yy + 68, rgb=(170, 180, 195), a=a * kj, align="right")
    if click:
        u = t - (T_JS + BEAT / 2)
        if 0 <= u < 0.5:
            bx, by = wx + 320 * s, wy + (72 + 401) * s
            kk = ease_out_cubic(u / 0.5)
            c.drawCircle(bx, by, 12 + 70 * kk, stroke(MINT, 255 * v * (1 - u / 0.5), width=max(2.0, 8 * (1 - kk))))
            L.mark(bx - 100, by - 100, bx + 100, by + 100)


cue(T_PIP4 + 0.3, "typing", 0.24, until=T_PIP4 + 1.7)
cue(T_LINK, "connect", 0.3)
cue(T_BTN, "pop", 0.28, f0=560, f1=1040)
cue(T_PW, "pop", 0.3, f0=640, f1=1200)
cue(T_JS, "tick", 0.3, f=2500)
cue(T_JS + BEAT / 2, "click", 0.42)

T_READS = on("nolook", "đọc")
T_NOLOOK = on("nolook", "nhìn.")
T_BOTH = on("nolook", "kết")
T_M1 = on("nolook", "chụp")
T_M2 = on("render", "đọc")
T_PIP5 = qb(w("render", "Thì")) - BEAT / 2
T_PIP5_OUT = CARD["card5"] - BEAT / 2
PIP.append((T_PIP5, T_PIP5_OUT))


@ev(CUT["nolook"] - 0.05, T_PIP5 + 0.3)
def reads_not_looks(ctx, t):
    depth_word(ctx, t, T_READS - 0.02, on("nolook", "Trong") - 0.05, "đọc mã", size=300, kind="black",
               gradient=(WHITE, (190, 255, 236)), enter="rise", stagger=0.035, fade_out=0.15, sheen=0.5, spk="M")
    L = ctx.front
    side_chip(ctx, t, T_NOLOOK, on("nolook", "Trong") - 0.05, "M", 0, "không cần nhìn", "cross", CORAL)
    side_chip(ctx, t, on("nolook", "hiệu"), on("nolook", "Trong") - 0.05, "M", 1, "hiệu quả hơn", "check", MINT)
    # sometimes the AI uses both ways
    t_out = T_PIP5
    v = V.fade(t, T_BOTH, t_out, 0.2, 0.2)
    if v > 0:
        kk = ease_out_cubic(clamp01((t - T_BOTH) / 0.45))
        draw_text(L, "đôi khi AI kết hợp cả hai", font("bold", 40), W / 2, 96 + (1 - kk) * 10, rgb=AMBER, a=255 * v, align="center",
                  tracking=5.0, shadow=10, shadow_a=180)
    V.mini(L, 680, 212, 540, 156, t, T_M1, t_out, "chụp ảnh", "tìm vị trí cái nút", num="1", accent=SKY)
    V.mini(L, 1250, 212, 560, 156, t, T_M2, t_out, "đọc mã HTML", "mã nguồn của trang web", num="2", accent=MINT)


cue(T_READS, "impact", 0.2, length=1.3)
cue(T_NOLOOK, "pop", 0.28, f0=480, f1=860)
cue(on("nolook", "hiệu"), "pop", 0.28, f0=600, f1=1120)
cue(T_M1, "pop", 0.28, f0=520, f1=980)
cue(T_M2, "pop", 0.28, f0=620, f1=1160)

T_OPENED = on("render", "mở")
T_SHOWS = on("render", "hiện")
T_NOSEE = on("render", "không")
T_SEES = on("render", "nhìn", 2)
T_BTN2 = on("render", "nút", 2)
T_BOX2 = on("render", "textbox")


@ev(T_PIP5, CARD["card5"])
def code_becomes_page(ctx, t):
    """the code, opened by a browser, becomes the pretty page; Playwright looks at the code underneath"""
    t0, t1 = T_PIP5 + 0.3, T_PIP5_OUT + 0.22
    h = 600
    v, dy, x0, y0, x1, y1 = panel(ctx, t, t0, t1, h)
    if v <= 0:
        return
    L = ctx.mid
    a = 255 * v
    c = L.c
    see = clamp01((t - T_SEES) / 0.4)
    nosee = clamp01((t - T_NOSEE) / 0.35)
    # left: the code
    cx0, cy0, cw_, ch_ = x0 + 40, y0 + 120 + dy, 470, 330
    draw_text(L, "mã HTML", font("bold", 36), cx0 + 6, cy0 - 26, rgb=MINT, a=a, align="left")
    c.drawRRect(rrect(cx0, cy0, cx0 + cw_, cy0 + ch_, 22), fill((16, 20, 30), 235 * v))
    if see > 0:
        c.drawRRect(rrect(cx0, cy0, cx0 + cw_, cy0 + ch_, 22), stroke(MINT, 255 * v * see, width=5))
        c.drawRRect(rrect(cx0, cy0, cx0 + cw_, cy0 + ch_, 22), stroke(MINT, 160 * v * see, width=12, blur=12))
    hot, hot_a, hot_rgb = None, 0.0, AMBER
    if t >= T_BOX2:
        hot, hot_a, hot_rgb = 1, clamp01((t - T_BOX2) / 0.25), SKY
    elif t >= T_BTN2:
        hot, hot_a, hot_rgb = 3, clamp01((t - T_BTN2) / 0.25), AMBER
    lines = [FORM_CODE[0], FORM_CODE[1], FORM_CODE[2],
             [("  <button ", C_TAG), ("id", C_ATTR), ("=", C_DIM), ('"login"', C_STR), (">", C_TAG)], FORM_CODE[4]]
    code_lines(L, cx0 + 24, cy0 + 70, lines, a, size=22, k=clamp01((t - t0) / 0.8), lh=2.1, hot=hot, hot_a=hot_a, hot_rgb=hot_rgb,
               width=cw_ - 36)
    L.mark(cx0 - 10, cy0 - 70, cx0 + cw_ + 10, cy0 + ch_ + 10)
    # middle: the browser opens it
    ax0, ax1, ay = cx0 + cw_ + 20, cx0 + cw_ + 150, cy0 + ch_ / 2
    arrow_h(L, ax0, ax1, ay, clamp01((t - T_OPENED) / 0.4), rgb=AMBER, a=a, width=6, head=18)
    ko = clamp01((t - T_OPENED) / 0.3)
    if ko > 0:
        icon(c, "browser", (ax0 + ax1) / 2, ay - 62, 62 * (0.7 + 0.3 * V.pop(t, T_OPENED)), AMBER, a * ko, sw=5)
        draw_text(L, "trình duyệt", font("semi", 26), (ax0 + ax1) / 2, ay + 52, rgb=AMBER, a=a * ko, align="center")
    # right: the page people see
    s = 0.52
    wx, wy = ax1 + 24, y0 + 100 + dy
    kp = clamp01((t - T_SHOWS) / 0.3)
    if kp > 0:
        pa = a * kp * (1 - 0.55 * nosee)
        draw_text(L, "giao diện", font("bold", 36), wx + 6, wy - 0, rgb=(220, 220, 210), a=pa, align="left")
        with V.tilt(L, wx + 320 * s, wy + 30 + 320 * s, 0.0, 0.8 + 0.2 * V.pop(t, T_SHOWS)):
            with scaled(L, wx, wy + 26, s):
                login_page(L, pa, t, user_k=0.0, pass_k=0.0, wv=640, hv=640)
        L.mark(wx, wy - 40, wx + 640 * s, wy + 30 + 640 * s + 30)
        if nosee > 0:
            U.cross(L, wx + 320 * s, wy + 26 + 330 * s, 70, 255 * v, k=nosee, rgb=(255, 112, 92), width=14)
    # what it tells apart
    yy = cy0 + ch_ + 58
    chip(L, t, T_SEES, t1, cx0 + 4, yy, "playwright nhìn cái mã bên trong", "check", style="glow", size=32, accent=MINT, anchor="left",
         alpha=v)
    chip(L, t, T_BTN2, t1, cx0 + 4, yy + 78, "<button> = nút login", "code", style="glow", size=32, accent=AMBER, anchor="left",
         alpha=v)
    chip(L, t, T_BOX2, t1, cx0 + 452, yy + 78, "<input> = ô username", "code", style="glow", size=32, accent=SKY, anchor="left",
         alpha=v)


cue(T_PIP5 + 0.3, "typing", 0.24, until=T_PIP5 + 1.1)
cue(T_OPENED, "swipe", 0.3)
cue(T_SHOWS, "pop", 0.32, f0=560, f1=1100)
cue(T_NOSEE, "glitch", 0.2)
cue(T_SEES, "shimmer", 0.3)
cue(T_BTN2, "tick", 0.32, f=2300)
cue(T_BOX2, "tick", 0.32, f=2700)


# ============================================================================
# CHAPTER 5 · what it can do: the Zalo example; the first time needs the AI, later runs do not
# ============================================================================
T_PIP6 = qb(w("zalo", "muốn")) - BEAT / 2
T_PIP6_OUT = CUT["first"]
T_Z1, T_Z2, T_Z3, T_Z4 = on("zalo", "đăng"), on("send", "tìm"), on("send", "nhắn"), on("send", "Playwright")
PIP.append((T_PIP6, T_PIP6_OUT))


@ev(DOWN[5] - 0.05, T_PIP6 + 0.3)
def what_can_it_do(ctx, t):
    depth_word(ctx, t, on("what", "làm") - 0.02, CUT["all"], "làm được gì?", size=240, kind="serif_ib", rgb=AMBER,
               glow=(255, 170, 60), enter="rise", stagger=0.025, tracking=0.0, fade_out=0.12, spk="W")
    depth_word(ctx, t, CUT["all"] + 0.04, on("all", "Anh") - 0.05, "tất cả", size=300, kind="serif_ib", rgb=AMBER,
               glow=(255, 170, 60), enter="rise", stagger=0.035, tracking=0.0, fade_out=0.15, spk="M")
    chip(ctx.front, t, on("all", "trình"), on("all", "Anh") - 0.05, W / 2, 204, "mọi việc bạn làm được trên trình duyệt", "browser",
         style="glow", size=44, accent=MINT)


cue(on("what", "làm"), "shimmer", 0.28)
cue(CUT["all"] + 0.04, "impact", 0.2, length=1.3)
cue(on("all", "trình"), "pop", 0.28, f0=560, f1=1040)


@ev(T_PIP6, CUT["first"] + 0.32)
def zalo_example(ctx, t):
    """a message sent through Zalo web in three steps (a plain mock: no logo, generic shapes)"""
    t0, t1 = T_PIP6 + 0.3, T_PIP6_OUT + 0.25
    h = 600
    v, dy, x0, y0, x1, y1 = panel(ctx, t, t0, t1, h)
    if v <= 0:
        return
    L = ctx.mid
    a = 255 * v
    c = L.c
    icon(c, "chat", x0 + 78, y0 + 62 + dy, 50, SKY, a, sw=5)
    draw_text(L, "việc cần làm: nhắn tin cho bạn qua Zalo", font("bold", 38), x0 + 122, y0 + 76 + dy, rgb=WHITE, a=a, align="left")
    s = 0.70
    wx, wy = x0 + 44, y0 + 118 + dy
    wv, hv = 640, 640
    with scaled(L, wx, wy, s):
        page = U.window(L, (0, 0, wv, hv), a, url="chat.zalo.me", url_k=clamp01((t - T_Z1) / 0.5), t=t, typing=t < T_Z1 + 0.5, r=26, bar=72)
        px0, py0, px1, py1 = page
        k1 = clamp01((t - T_Z1 - 0.45) / 0.3)
        if k1 < 1:
            U.text(c, "tab mới", font("semi", 34), wv / 2, 330, U.MUTE, a * (1 - k1) * 0.85, align="center")
            c.drawRRect(rrect(170, 362, 470, 406, 22), stroke(U.LINE, a * (1 - k1), width=3))
        if k1 > 0:
            pa = a * k1
            c.drawRect(skia.Rect.MakeLTRB(px0, py0, px0 + 230, py1 - 26), fill((240, 243, 248), pa))
            # the search box
            ks = clamp01((t - T_Z2) / 0.5)
            U.field(L, px0 + 16, py0 + 22, 198, 56, None, "ABC", ks, pa, t=t, focus=T_Z2 - 0.2 <= t < T_Z3 - 0.2, size=28)
            names = ["Chị Lan", "ABC", "Nhóm dự án", "Anh Minh"]
            for i, nm in enumerate(names):
                yy = py0 + 112 + i * 84
                hit = nm == "ABC" and t >= T_Z2 + 0.45
                if hit:
                    c.drawRRect(rrect(px0 + 8, yy - 8, px0 + 222, yy + 68, 14), fill((48, 110, 255), 46 * k1 * v))
                c.drawCircle(px0 + 46, yy + 30, 24, fill((48, 110, 255) if hit else (190, 198, 210), pa))
                U.text(c, nm, font("bold" if hit else "medium", 26), px0 + 84, yy + 39, U.INK, pa)
            # the conversation
            if t >= T_Z2 + 0.45:
                kc = clamp01((t - T_Z2 - 0.45) / 0.25)
                U.text(c, "ABC", font("xbold", 30), px0 + 256, py0 + 58, U.INK, a * kc)
                c.drawLine(px0 + 246, py0 + 84, px1 - 16, py0 + 84, stroke(U.LINE, a * kc, width=2))
                U.bubble(L, px0 + 256, py0 + 112, 330, "Tối nay cà phê nhé?", a * kc, mine=False, size=26, k=kc)
                km = clamp01((t - T_Z3) / 0.6)
                msg = "Ok, 8 giờ nhé!"
                # the message box, typed, then sent as a bubble
                sent = t >= T_Z3 + 0.7
                U.field(L, px0 + 250, py1 - 110, 330, 60, None, "" if sent else msg, km, a * kc, t=t, focus=T_Z3 - 0.2 <= t and not sent,
                        size=26)
                if sent:
                    kb = clamp01((t - T_Z3 - 0.7) / 0.25)
                    U.bubble(L, px1 - 26, py0 + 200, 330, msg, a, mine=True, size=26, k=kb)
                    U.tick(L, px1 - 46, py0 + 290, 15, a, k=clamp01((t - T_Z3 - 0.85) / 0.3))
    L.mark(wx, wy, wx + wv * s, wy + hv * s + 30)
    rx = wx + wv * s + 78
    rows = [("đăng nhập Zalo web", T_Z1), ("tìm người tên “ABC”", T_Z2), ("nhắn tin", T_Z3)]
    for i, (txt, ts) in enumerate(rows):
        nxt_t = rows[i + 1][1] if i + 1 < len(rows) else T_Z3 + 0.9
        yy = y0 + 196 + i * 96 + dy
        if t < ts:
            step_slot(L, rx, yy, i + 1, v, i % 2)
        step_row(L, rx, yy, i + 1, txt, t, ts, a, accent=SKY, done_t=nxt_t, size=38)
    chip(L, t, T_Z4, t1, rx - 30, y0 + 196 + 3 * 96 + 14 + dy, "playwright làm được hết", "check", style="glow", size=34, accent=MINT,
         anchor="left", alpha=v)


cue(T_Z1, "typing", 0.24, until=T_Z1 + 0.5)
cue(T_Z1, "pop", 0.28, f0=480, f1=900)
cue(T_Z2, "typing", 0.24, until=T_Z2 + 0.5)
cue(T_Z2, "pop", 0.28, f0=540, f1=1000)
cue(T_Z3, "typing", 0.24, until=T_Z3 + 0.6)
cue(T_Z3, "pop", 0.28, f0=600, f1=1120)
cue(T_Z3 + 0.7, "connect", 0.28)
cue(T_Z4, "ding", 0.26, f=1318.5)

T_FIRST, T_LATER = on("first", "lần", 1), on("first", "lần", 2)
T_BRAIN = on("first", "não")


@ev(CUT["first"] - 0.05, CARD["card6"] + 0.05)
def first_time_then(ctx, t):
    L = ctx.front
    t_out = CUT["process"]
    later = clamp01((t - T_BRAIN) / 0.35)
    V.mini(L, 660, 212, 560, 156, t, T_FIRST, t_out, "lần đầu", "AI nghĩ và viết kịch bản", icon_kind="brain", accent=AMBER,
           dim=later)
    V.mini(L, 1260, 212, 580, 156, t, T_LATER, t_out, "từ lần sau", "kịch bản tự chạy, khỏi nghĩ", icon_kind="history",
           accent=MINT, glow=later)
    side_chip(ctx, t, on("process", "quy"), CARD["card6"], "M", 0, "như một quy trình", "list", AMBER)
    side_chip(ctx, t, on("process", "bước"), CARD["card6"], "M", 1, "cứ làm từng bước", "check", MINT)


cue(T_FIRST, "pop", 0.3, f0=520, f1=980)
cue(T_LATER, "pop", 0.3, f0=620, f1=1160)
cue(T_BRAIN, "tick", 0.32, f=2400)
cue(on("process", "quy"), "pop", 0.26, f0=520, f1=980)
cue(on("process", "bước"), "pop", 0.26, f0=600, f1=1120)


# ============================================================================
# CHAPTER 6 · tokens
# ============================================================================
T_SAVE = on("save", "tiết")
T_PIP7 = qb(w("twenty", "20", 1)) - BEAT / 2
T_PIP7_OUT = CUT["think"]
T_RUN20 = on("twenty", "chạy")
T_ASK = on("twenty", "lôi")
T_HAS = on("twenty", "Bởi")
PIP.append((T_PIP7, T_PIP7_OUT))


@ev(DOWN[6] - 0.05, T_PIP7 + 0.3)
def tokens_question(ctx, t):
    depth_word(ctx, t, on("token", "tốn") - 0.02, CUT["save"], "tốn token?", size=240, kind="serif_ib", rgb=AMBER,
               glow=(255, 170, 60), enter="rise", stagger=0.025, tracking=0.0, fade_out=0.12, spk="W")
    side_chip(ctx, t, on("save", "tự"), T_SAVE - 0.05, "M", 0, "tự động hóa", "spark", AMBER)
    depth_word(ctx, t, T_SAVE - 0.02, T_PIP7 + 0.05, "tiết kiệm", size=290, kind="serif_ib", rgb=MINT, glow=(90, 230, 190),
               enter="rise", stagger=0.03, tracking=0.0, fade_out=0.15, spk="M")


cue(on("token", "tốn"), "shimmer", 0.28)
cue(on("save", "tự"), "pop", 0.26, f0=520, f1=980)
cue(T_SAVE, "impact", 0.2, length=1.3)


@ev(T_PIP7, CUT["think"] + 0.32)
def twenty_people(ctx, t):
    """twenty messages: the script runs twenty times; the model is not asked twenty times"""
    t0, t1 = T_PIP7 + 0.3, T_PIP7_OUT + 0.25
    h = 600
    v, dy, x0, y0, x1, y1 = panel(ctx, t, t0, t1, h)
    if v <= 0:
        return
    L = ctx.mid
    a = 255 * v
    c = L.c
    icon(c, "chat", x0 + 78, y0 + 62 + dy, 50, AMBER, a, sw=5)
    draw_text(L, "gửi tin nhắn cho 20 người", font("bold", 40), x0 + 122, y0 + 76 + dy, rgb=WHITE, a=a, align="left")
    # 20 people, ticked off in time with the music: five per half beat
    gx, gy = x0 + 70, y0 + 150 + dy
    n_done = int(clamp01((t - T_RUN20) / (2 * BEAT)) * 20 + 1e-6) if t >= T_RUN20 else 0
    for i in range(20):
        px, py = gx + (i % 5) * 84, gy + (i // 5) * 84
        done = i < n_done
        c.drawCircle(px + 30, py + 30, 30, fill((36, 196, 118) if done else (120, 128, 136), (255 if done else 150) * v))
        if done:
            p = stroke(WHITE, a, width=5)
            c.drawLine(px + 18, py + 31, px + 27, py + 40, p)
            c.drawLine(px + 27, py + 40, px + 43, py + 21, p)
        else:
            c.drawCircle(px + 30, py + 24, 9, fill(WHITE, 170 * v))
            c.drawRRect(rrect(px + 14, py + 36, px + 46, py + 54, 9), fill(WHITE, 170 * v))
    L.mark(gx - 10, gy - 10, gx + 5 * 84, gy + 4 * 84)
    draw_text(L, f"kịch bản chạy ×{n_done}", font("black", 46), gx, gy + 4 * 84 + 62, rgb=MINT if n_done >= 20 else WHITE, a=a,
              align="left")
    # right: asking the model every time versus running the script (a picture of the idea, not a measurement)
    bx = x0 + 560
    draw_text(L, "token phải trả", font("bold", 34), bx, y0 + 170 + dy, rgb=(220, 220, 210), a=a, align="left")
    k1 = clamp01((t - T_ASK) / (2 * BEAT))
    if k1 > 0:
        yy = y0 + 240 + dy
        icon(c, "brain", bx + 28, yy, 52, CORAL, a, sw=4)
        draw_text(L, "hỏi AI cả 20 lần", font("semi", 32), bx + 68, yy + 11, rgb=WHITE, a=a, align="left")
        c.drawRRect(rrect(bx, yy + 40, bx + 420 * ease_out_cubic(k1), yy + 78, 12), fill(CORAL, 235 * v))
        L.mark(bx - 10, yy - 40, bx + 440, yy + 90)
    k2 = clamp01((t - T_HAS) / BEAT)
    if k2 > 0:
        yy = y0 + 392 + dy
        icon(c, "history", bx + 28, yy, 52, MINT, a, sw=4)
        draw_text(L, "chạy kịch bản có sẵn", font("semi", 32), bx + 68, yy + 11, rgb=WHITE, a=a, align="left")
        c.drawRRect(rrect(bx, yy + 40, bx + 56 * ease_out_cubic(k2), yy + 78, 12), fill(MINT, 235 * v))
        L.mark(bx - 10, yy - 40, bx + 440, yy + 90)
    draw_text(L, "hình minh họa, không phải số đo", font("medium", 24), bx, y0 + 520 + dy, rgb=(170, 176, 170), a=a * 0.9,
              align="left")


cue(T_RUN20, "typing", 0.22, until=T_RUN20 + 2 * BEAT)
cue(T_RUN20 + 2 * BEAT, "ding", 0.28, f=1318.5)
cue(T_ASK, "swell", 0.3, length=1.0)
cue(T_HAS, "pop", 0.3, f0=640, f1=1200)

T_N1, T_N2, T_N3, T_BACK = on("think", "suy"), on("think", "thực"), on("think", "vấn"), on("think", "quay")
T_USE = on("think", "dùng")
T_SUM = on("sum", "tiết")


@ev(CUT["think"] - 0.05, CARD["card7"] + 0.05)
def the_loop(ctx, t):
    """writing the script needs reasoning; when a run hits a problem the AI comes back in"""
    L = ctx.front
    t_out = CUT["sum"]
    V.mini(L, 372, 212, 520, 150, t, T_N1, t_out, "AI viết kịch bản", "cần suy luận", icon_kind="brain", accent=AMBER,
           glow=V.pulse(t, T_USE, 0.6))
    V.mini(L, 960, 212, 520, 150, t, T_N2, t_out, "kịch bản tự chạy", "không tốn suy luận", icon_kind="history", accent=MINT)
    V.mini(L, 1548, 212, 520, 150, t, T_N3, t_out, "gặp vấn đề?", "gọi AI quay lại", icon_kind="warn", accent=CORAL)
    vv = V.fade(t, T_N2, t_out)
    if vv > 0:
        arrow_h(L, 642, 690, 212, clamp01((t - T_N2) / 0.3), rgb=WHITE, a=220 * vv, width=5, head=13)
    vv = V.fade(t, T_N3, t_out)
    if vv > 0:
        arrow_h(L, 1230, 1278, 212, clamp01((t - T_N3) / 0.3), rgb=WHITE, a=220 * vv, width=5, head=13)
    kb = clamp01((t - T_BACK) / 0.6)
    vb = V.fade(t, T_BACK, t_out)
    if kb > 0 and vb > 0:
        path = skia.Path()
        path.moveTo(1548, 132)
        path.cubicTo(1400, 44, 520, 44, 380, 126)
        pm = skia.PathMeasure(path, False)
        seg = skia.Path()
        pm.getSegment(0, pm.getLength() * ease_out_cubic(kb), seg, True)
        L.c.drawPath(seg, stroke(AMBER, 240 * vb, width=5))
        if kb >= 0.98:
            L.c.drawLine(380, 126, 412, 126, stroke(AMBER, 240 * vb, width=5))
            L.c.drawLine(380, 126, 394, 98, stroke(AMBER, 240 * vb, width=5))
        L.mark(350, 40, 1570, 150)
    # the summary: the music steps back, the line stands behind him
    v = V.fade(t, on("sum", "Tóm"), CARD["card7"], 0.2, 0.001)
    if v > 0:
        kk = ease_out_cubic(clamp01((t - on("sum", "Tóm")) / 0.45))
        draw_text(L, "tóm lại", font("bold", 46), W / 2, 122 + (1 - kk) * 10, rgb=AMBER, a=255 * v, align="center", tracking=9.0,
                  shadow=10, shadow_a=180)
    depth_word(ctx, t, T_SUM - 0.02, CARD["card7"], "tiết kiệm token", size=250, kind="black", gradient=(WHITE, (190, 255, 236)),
               enter="rise", stagger=0.028, fade_out=0.001, sheen=0.5, spk="M")


cue(T_N1, "pop", 0.3, f0=520, f1=980)
cue(T_N2, "pop", 0.3, f0=580, f1=1080)
cue(T_N3, "pop", 0.3, f0=640, f1=1180)
cue(T_BACK, "rewind", 0.26)
cue(T_USE, "tick", 0.3, f=2400)
cue(T_SUM, "impact", 0.22, length=1.4)


# ============================================================================
# CHAPTER 7 · how to get the skill, his laugh, the walk-off
# ============================================================================
T_SKILL = on("cta", "skill")
T_CMT = on("cta", "comment", 1)
T_SEND = on("cta", "nhá.")
T_TYPO = [qb(w("laugh", "khó")), qb(w("laugh", "khó")) + BEAT, qb(w("laugh", "khó")) + 2 * BEAT]
T_GONE = T_END - BEAT


@ev(DOWN[7] - 0.05, T_END + 0.05)
def get_the_skill(ctx, t):
    L = ctx.front
    # the skill, as a card from the journal
    v = V.fade(t, T_SKILL, T_GONE, 0.1, 0.3)
    if v > 0:
        cx, cy, wd, hd = 610, 196, 560, 196
        with V.tilt(L, cx, cy, -2.5, 0.7 + 0.3 * V.pop(t, T_SKILL)):
            V.paper(L, cx - wd / 2, cy - hd / 2, cx + wd / 2, cy + hd / 2, v)
            x = cx - wd / 2 + 40
            draw_text(L, "skill", font("bold", 30), x, cy - 40, rgb=(176, 92, 30), a=255 * v, align="left", tracking=6.0)
            draw_text(L, "Playwright", font("serif_b", 62), x, cy + 22, rgb=INKB, a=255 * v, align="left")
            draw_text(L, "điều khiển Zalo", font("serif_i", 46), x, cy + 74, rgb=INKB, a=255 * v, align="left")
        L.mark(cx - wd / 2 - 30, cy - hd / 2 - 40, cx + wd / 2 + 30, cy + hd / 2 + 40)
    # the comment box: the word is typed as she says it; then the typos he laughs about, one per beat
    v = V.fade(t, T_CMT - BEAT / 2, T_GONE, 0.15, 0.3)
    if v > 0:
        a = 255 * v
        x0, y0, wb, hb = 990, 120, 760, 150
        k = 0.7 + 0.3 * V.pop(t, T_CMT - BEAT / 2)
        with V.tilt(L, x0 + wb / 2, y0 + hb / 2, 0.0, k):
            V.plate(L, x0, y0, x0 + wb, y0 + hb, v, r=30, dark=200)
            c = L.c
            c.drawCircle(x0 + 66, y0 + hb / 2, 34, fill((120, 128, 136), a))
            c.drawCircle(x0 + 66, y0 + hb / 2 - 9, 12, fill(WHITE, 200 * v))
            c.drawRRect(rrect(x0 + 44, y0 + hb / 2 + 8, x0 + 88, y0 + hb / 2 + 30, 11), fill(WHITE, 200 * v))
            word, rgb, mark_ = "Playwright", WHITE, None
            kt = clamp01((t - T_CMT) / (1.5 * BEAT))
            if t >= T_TYPO[2]:
                word, mark_ = "Playwright", "ok"
            elif t >= T_TYPO[1]:
                word, rgb, mark_ = "Playwrite", CORAL, "bad"
            elif t >= T_TYPO[0]:
                word, rgb, mark_ = "Playright", CORAL, "bad"
            shown = U.typed(word, kt)
            tw_ = text_width(shown, font("semi", 50))
            draw_text(L, shown, font("semi", 50), x0 + 126, y0 + hb / 2 + 17, rgb=rgb, a=a, align="left")
            if kt < 1 and int(t * 2.6) % 2 == 0:
                c.drawRect(skia.Rect.MakeXYWH(x0 + 130 + tw_, y0 + hb / 2 - 26, 4, 50), fill(AMBER, a))
            c.drawLine(x0 + 122, y0 + hb / 2 + 40, x0 + wb - 200, y0 + hb / 2 + 40, stroke(WHITE, 90 * v, width=2))
            if mark_ == "bad":
                tb = T_TYPO[1] if t >= T_TYPO[1] else T_TYPO[0]
                V.underline(L, x0 + 126, x0 + 126 + tw_, y0 + hb / 2 + 34, clamp01((t - tb) / 0.2), rgb=CORAL, a=a, width=4)
            elif mark_ == "ok":
                U.tick(L, x0 + 150 + tw_ + 24, y0 + hb / 2, 22, a, k=clamp01((t - T_TYPO[2]) / 0.3))
            press = 1.0 if T_SEND - 0.02 <= t < T_SEND + 0.14 else 0.0
            sent = clamp01((t - T_SEND - 0.1) / 0.25) if t < T_TYPO[0] else 0.0
            with V.tilt(L, x0 + wb - 110, y0 + hb / 2, 0.0, 1 - 0.06 * press):
                c.drawRRect(rrect(x0 + wb - 196, y0 + hb / 2 - 32, x0 + wb - 26, y0 + hb / 2 + 32, 32),
                            fill((36, 196, 118) if sent > 0.5 else AMBER, a))
                draw_text(L, "Đã gửi" if sent > 0.5 else "Bình luận", font("bold", 30), x0 + wb - 111, y0 + hb / 2 + 11, rgb=INK, a=a,
                          align="center")
        L.mark(x0 - 30, y0 - 30, x0 + wb + 30, y0 + hb + 40)
        if t >= T_TYPO[0]:
            kk = clamp01((t - T_TYPO[2]) / 0.3)
            if kk > 0:
                draw_text(L, "p · l · a · y · w · r · i · g · h · t", font("semi", 34), x0 + wb / 2, y0 + hb + 62, rgb=AMBER, a=a * kk,
                          align="center", shadow=10, shadow_a=180)


cue(T_SKILL, "shutter", 0.3)
cue(T_CMT, "typing", 0.28, until=T_CMT + 1.5 * BEAT)
cue(T_SEND, "click", 0.42)
cue(T_TYPO[0], "glitch", 0.22)
cue(T_TYPO[1], "glitch", 0.22)
cue(T_TYPO[2], "ding", 0.3, f=1318.5)


@ev(T_END - 0.05, TOTAL)
def end_card(ctx, t):
    takeaway(ctx, t, T_END + 0.06, "viết kịch bản một lần", "chạy lại, tiết kiệm token", "comment “Playwright” để nhận skill",
             kick="tóm lại")


cue(T_END + 0.08, "whoosh", 0.3, length=0.7, direction=-1)
cue(T_END + BEAT, "pop", 0.3, f0=500, f1=1000)
