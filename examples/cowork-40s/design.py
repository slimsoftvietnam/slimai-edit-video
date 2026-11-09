"""Claude Cowork and ChatGPT Work: do they have a repo? A 40 s clip, rendered as TikTok and YouTube HD."""
import math

from story import *

for key, word, near in [
    ("cowork", "Cowork", 0.66), ("chatgpt", "ChatGPT", 1.40), ("repo_q", "repo", 2.76), ("dat", "Đấy", 3.89), ("su", "sự", 5.19),
    ("khac", "khác", 5.99), ("thuong", "Thường", 6.95), ("moitruong", "môi", 8.46), ("khongphai", "không", 9.55),
    ("repo1", "repo", 9.97), ("folder1", "folder", 10.95), ("upload", "upload", 12.58), ("gan", "gắn", 13.98),
    ("thaotac", "thao", 15.44), ("repo2", "Repo", 16.55), ("coding1", "coding", 20.02), ("vithe", "Vì", 20.72),
    ("coding2", "coding", 22.66), ("nhung", "Nhưng", 23.58), ("lichsu_q", "lịch", 25.12), ("cai", "Cái", 26.50),
    ("dau", "đâu", 26.88), ("cunglam", "cùng", 28.00), ("xoa", "xóa", 28.48), ("thungrac", "thùng", 28.96),
    ("restore", "restore", 29.80), ("con", "Còn", 30.79), ("lichsu2", "lịch", 32.08), ("nhieu", "nhiều", 32.46),
    ("moi1", "mỗi", 33.32), ("edit1", "edit", 34.06), ("moi2", "mỗi", 34.58), ("commit", "commit", 35.53), ("tao", "tạo", 38.31), ("phien", "phiên", 39.42),
]:
    A[key] = at(word, near)

KEYS.update({"repo": ("xbold", MINT, 1.0), "folder": ("xbold", WHITE, 1.0), "lịch sử": ("serif_ib", AMBER, 1.22),
             "khác biệt": ("serif_ib", AMBER, 1.22), "coding agent": ("xbold", MINT, 1.0), "commit": ("xbold", AMBER, 1.0),
             "phiên bản": ("serif_ib", AMBER, 1.22), "thùng rác": ("serif_ib", CORAL, 1.15), "restore": ("xbold", WHITE, 1.0)})
KEEP_CASE.update({"cowork": "Cowork", "chatgpt": "ChatGPT"})
NO_BREAK.update({"Cowork", "ChatGPT", "Work"})

SHOT_OVERRIDES.append((A["commit"] - 0.05, DUR, "M_wide"))
PUNCHES.extend([(A["repo_q"], 0.04, 0.10, 0.4, 0.5), (A["khac"], 0.04, 0.10, 0.3, 0.6), (A["repo2"], 0.04, 0.10, 0.3, 0.6)])
PIP.extend([(A["thuong"] + 0.05, A["repo2"] - 0.18), (A["cai"] - 0.1, A["con"] - 0.25), (A["moi1"] - 0.45, DUR - 0.35)])
LEAKS.extend([A["repo2"] - 0.15, A["con"] - 0.1])
LABELS.extend([(A["thuong"] - 0.1, "01", "Cowork làm việc với folder"), (A["repo2"] - 0.1, "02", "Repo đi với coding agent"),
               (A["con"] - 0.1, "03", "Lịch sử nhiều lần")])
YT_CHAPTERS.extend([(0.0, "Claude Cowork, ChatGPT Work có repo không?"), (A["repo2"] - 0.1, "Repo đi với coding agent"),
                    (A["con"] - 0.1, "Mỗi commit là một phiên bản lịch sử")])
MUSIC.update(drop=A["khac"] - 0.04, stops=[A["repo2"] - 0.32], sections=[
    (A["khac"], "light", "main"), (A["repo2"], "groove", "main"), (A["nhung"], "break", "calm"), (A["con"], "lift", "main"),
    (DUR - 0.5, "outro", "calm")])


@ev(-0.5, A["dat"] + 0.1)
def hook(ctx, t):
    # 16:9: "REPO?" comes out from behind her head, so the head never hides the middle of the word
    depth_word(ctx, t, -0.4, A["dat"] - 0.02, pick("REPO?", "CÓ REPO?"), size=pick(320, 280), gradient=(WHITE, (205, 255, 238)), enter="settle",
               stagger=0.04, fade_out=0.14, sheen=0.5, spk="W", xoff=pick(300, 0))
    x, y, an = place(ctx, (165, 45, "left"), (MX + 15, 300, "left"), "W")
    chip(ctx.front, t, A["cowork"] - 0.1, A["dat"] - 0.05, x, y, "Claude Cowork", "spark", style="glow", size=pick(42, 40), accent=AMBER, anchor=an)
    x, y, an = place(ctx, (165, 140, "left"), (W - MX - 15, 300, "right"), "W")
    chip(ctx.front, t, A["chatgpt"] - 0.05, A["dat"] - 0.05, x, y, "ChatGPT Work", "spark", style="glow", size=pick(42, 40), accent=SKY, anchor=an)


cue(0.05, "whoosh", 0.6, length=0.6, direction=1)
cue(A["cowork"] - 0.1, "pop", 0.5, f0=520, f1=1000)
cue(A["chatgpt"] - 0.05, "pop", 0.5, f0=600, f1=1150)


@ev(A["dat"] - 0.05, A["thuong"] + 0.3)
def turn(ctx, t):
    x, y, an = place(ctx, (-170, -20, "right"), (W / 2, 300, "center"))
    chip(ctx.front, t, A["dat"] + 0.15, A["khac"] - 0.12, x, y, "Câu trả lời", "spark", style="glow", size=44, accent=AMBER, anchor=an)
    depth_word(ctx, t, A["khac"] - 0.12, A["thuong"] + 0.25, "khác biệt", size=pick(290, 250), kind="serif_ib", rgb=AMBER,
               glow=(255, 170, 60), enter="rise", tracking=0.0, fade_out=0.15)


cue(A["dat"] + 0.15, "pop", 0.4, f0=480, f1=900)
cue(A["khac"] - 0.12, "whoosh", 0.5, length=0.5, direction=1)


@ev(A["thuong"] + 0.3, A["repo2"] - 0.1)
def folder_panel(ctx, t):
    t0, t1 = A["thuong"] + 0.35, A["repo2"] - 0.18
    h = pick(570, 520)
    v, dy, x0, y0, x1, y1 = panel(ctx, t, t0, t1, h)
    if v <= 0:
        return
    c = ctx.mid.c
    a = 255 * v
    cx = (x0 + x1) / 2
    draw_text(ctx.mid, "Claude Cowork · ChatGPT Work", font("bold", pick(46, 44)), cx, y0 + h * 0.15 + dy, rgb=WHITE, a=a)
    my = y0 + h * 0.47 + dy
    ax, fx = x0 + 180, x1 - 190
    icon(c, "robot", ax, my, 130, MINT, a, sw=7)
    draw_text(ctx.mid, "Agent", font("semi", 40), ax, my + 112, rgb=MINT, a=a)
    # the repo it does not have, struck through on the word
    rk = clamp01((t - (A["khongphai"] - 0.1)) / 0.3)
    r = chip(ctx.mid, t, A["khongphai"] - 0.1, A["folder1"] + 0.5, (ax + fx) / 2, my - 4, "Repo", "branch", style="dark", size=40, accent=CORAL)
    if r is not None and t >= A["repo1"] + 0.25:
        strike(ctx.mid, t, A["repo1"] + 0.25, r[0] + 6, r[2] - 6, (r[1] + r[3]) / 2, rgb=CORAL, width=7, t1=A["folder1"] + 0.5)
    if t >= A["folder1"] - 0.15:
        ka = clamp01((t - (A["folder1"] - 0.15)) / 0.45)
        arrow(c, ax + 100, my, fx - 110, ka, AMBER, a)
        kf = clamp01((t - (A["folder1"] - 0.05)) / 0.4)
        icon(c, "folder", fx, my, 150 * (0.6 + 0.4 * spring(kf)), WHITE, a * kf, sw=8)
        draw_text(ctx.mid, "Folder", font("bold", 44), fx, my + 112, rgb=WHITE, a=a * kf)
    yy = y1 - h * 0.1 + dy
    for tt, lab, ic, xx in ((A["upload"], "Upload folder", "upload", x0 + 90), (A["gan"], "Gắn folder local", "link", (x0 + x1) / 2 + pick(10, 0))):
        if t >= tt - 0.1:
            kk = clamp01((t - (tt - 0.1)) / 0.3)
            icon(c, ic, xx + 24, yy - 15, 46, AMBER, a * kk, sw=5)
            draw_text(ctx.mid, lab, font("semi", pick(42, 40)), xx + 62, yy, rgb=WHITE, a=a * kk, align="left")


cue(A["khongphai"] - 0.1, "pop", 0.4, f0=480, f1=850)
cue(A["repo1"] + 0.25, "swipe", 0.55)
cue(A["folder1"] - 0.05, "pop", 0.5, f0=600, f1=1150)
cue(A["upload"] - 0.1, "tick", 0.45, f=2400)
cue(A["gan"] - 0.1, "tick", 0.45, f=2700)


@ev(A["repo2"] - 0.1, A["nhung"] - 0.05)
def repo_beat(ctx, t):
    depth_word(ctx, t, A["repo2"] - 0.08, A["nhung"] - 0.08, "REPO", size=pick(330, 320), gradient=(WHITE, (205, 255, 238)), enter="rise",
               stagger=0.05, sheen=0.5, fade_out=0.15)
    x, y, an = place(ctx, (190, 90, "left"), (W - MX - 15, 262, "right"))
    chip(ctx.front, t, A["coding1"] - 0.05, A["nhung"] - 0.12, x, y, "liên quan coding", "code", style="glow", size=pick(42, 40), accent=SKY, anchor=an)
    x, y, an = place(ctx, (190, 195, "left"), (W - MX - 15, 358, "right"))
    chip(ctx.front, t, A["coding2"] - 0.05, A["nhung"] - 0.12, x, y, "coding agent", "robot", style="glow", size=pick(42, 40), accent=MINT, anchor=an)


cue(A["repo2"] - 0.08, "impact", 0.4, length=1.4)
cue(A["coding1"] - 0.05, "pop", 0.45, f0=520, f1=980)
cue(A["coding2"] - 0.05, "pop", 0.45, f0=620, f1=1180)


@ev(A["nhung"] - 0.05, A["cai"] + 0.1)
def question(ctx, t):
    depth_word(ctx, t, A["lichsu_q"] - 0.12, A["cai"] + 0.05, "lịch sử?", size=pick(300, 270), kind="serif_ib", rgb=AMBER,
               glow=(255, 170, 60), enter="pop", stagger=0.03, tracking=0.0, fade_out=0.12, spk="W")


cue(A["lichsu_q"] - 0.1, "shimmer", 0.45)


@ev(A["cai"] + 0.15, A["con"] - 0.1)
def trash_panel(ctx, t):
    t0, t1 = A["cai"] + 0.2, A["con"] - 0.25
    h = pick(520, 480)
    v, dy, x0, y0, x1, y1 = panel(ctx, t, t0, t1, h)
    if v <= 0:
        return
    c = ctx.mid.c
    a = 255 * v
    hx = x0 + 80
    hy = y0 + h * 0.17 + dy
    icon(c, "folder", hx, hy - 16, 62, WHITE, a, sw=5)
    draw_text(ctx.mid, "Folder", font("xbold", 54), hx + 56, hy, rgb=WHITE, a=a, align="left")
    wf = text_width("Folder", font("xbold", 54))
    kx = clamp01((t - A["dau"]) / 0.4)
    draw_text(ctx.mid, "· không có lịch sử", font("serif_ib", pick(56, 52)), hx + 56 + wf + 18, hy + 2, rgb=CORAL, a=a * kx, align="left")
    my = y0 + h * 0.58 + dy
    fx, tx = x0 + (x1 - x0) * 0.26, x0 + (x1 - x0) * 0.74
    icon(c, "trash", tx, my, 140, CORAL, a, sw=7)
    draw_text(ctx.mid, "Thùng rác", font("semi", 40), tx, my + 118, rgb=CORAL, a=a)
    go = ease_in_out_cubic(clamp01((t - (A["thungrac"] - 0.45)) / 0.55))
    back = ease_in_out_cubic(clamp01((t - (A["restore"] - 0.05)) / 0.55))
    u = go * (1 - back)
    px = lerp(fx, tx, u)
    py = my - 120 * math.sin(math.pi * u) - 8 * u
    icon(c, "file", px, py, 118 * (1 - 0.35 * u), WHITE, a * (1 - 0.65 * clamp01((u - 0.8) / 0.2)), sw=6)
    if back > 0:
        draw_text(ctx.mid, "restore, thế là hết", font("semi", 40), fx, my + 118, rgb=WHITE, a=a * back)


cue(A["dau"], "glitch", 0.3)
cue(A["thungrac"] - 0.45, "whoosh", 0.4, length=0.45, direction=1)
cue(A["restore"] - 0.05, "rewind", 0.55)


@ev(A["con"] - 0.05, A["moi1"] + 0.1)
def many(ctx, t):
    depth_word(ctx, t, A["con"] + 0.15, A["moi1"] - 0.2, "LỊCH SỬ", size=pick(300, 270), gradient=(WHITE, GOLD), enter="rise", stagger=0.04, fade_out=0.12)
    x, y, an = place(ctx, (190, 90, "left"), (W / 2, 300, "center"))
    chip(ctx.front, t, A["nhieu"] - 0.05, A["moi1"] - 0.2, x, y, "nhiều lần", "history", style="glow", size=pick(44, 42), accent=MINT, anchor=an)


cue(A["con"] + 0.15, "whoosh", 0.45, length=0.5, direction=1)
cue(A["nhieu"] - 0.05, "pop", 0.45, f0=560, f1=1050)


@ev(A["moi1"] - 0.2, DUR + 0.1)
def commits(ctx, t):
    t0, t1 = A["moi1"] - 0.15, DUR - 0.35
    h = pick(500, 470)
    v, dy, x0, y0, x1, y1 = panel(ctx, t, t0, t1, h)
    if v <= 0:
        return
    c = ctx.mid.c
    a = 255 * v
    hx = x0 + 80
    hy = y0 + h * 0.18 + dy
    icon(c, "history", hx, hy - 16, 62, MINT, a, sw=5)
    draw_text(ctx.mid, "Repo", font("black", 54), hx + 56, hy, rgb=MINT, a=a, align="left")
    wr = text_width("Repo", font("black", 54))
    draw_text(ctx.mid, "· nhớ từng lần", font("serif_ib", 56), hx + 56 + wr + 18, hy + 2, rgb=AMBER, a=a, align="left")
    ly = y0 + h * 0.58 + dy
    xs = [lerp(x0 + 110, x1 - 150, i / 3) for i in range(4)]
    times = [A["edit1"] - 0.1, A["moi2"] + 0.2, A["commit"] - 0.05, A["phien"] - 0.1]
    labs = ["edit", "edit", "commit", "bản mới"]
    shown = sum(1 for tt in times if t >= tt)
    if shown >= 2:
        k = clamp01((t - times[shown - 1]) / 0.3)
        c.drawLine(xs[0], ly, lerp(xs[shown - 2], xs[shown - 1], ease_out_cubic(k)), ly, stroke(MINT, 170 * v, width=5))
    for i, (x, tt, lab) in enumerate(zip(xs, times, labs)):
        if t < tt:
            continue
        k = clamp01((t - tt) / 0.35)
        last = i == 3
        rgb = GOLD if last else MINT
        dot(c, x, ly, (26 if last else 18) * (0.5 + 0.5 * spring(k)), rgb, a * clamp01(k * 3))
        draw_text(ctx.mid, f"v{i + 1}", font("black", 50), x, ly - 56, rgb=WHITE, a=a * clamp01(k * 2))
        draw_text(ctx.mid, lab, font("semi", 38), x, ly + 78, rgb=rgb, a=a * clamp01(k * 2))


for tt_ in ("edit1", "commit"):
    cue(A[tt_] - 0.1, "pop", 0.45, f0=600, f1=1100)
cue(A["moi2"] + 0.2, "pop", 0.45, f0=680, f1=1250)
cue(A["phien"] - 0.1, "ding", 0.4, f=1318.5)
cue(A["phien"] - 0.1, "shimmer", 0.45)


@ev(DUR + 0.65, TOTAL)
def end_card(ctx, t):
    takeaway(ctx, t, DUR + 0.7, "Folder: lưu được, không nhớ", "Repo: nhớ từng lần", "Mỗi commit là một phiên bản lịch sử")


cue(DUR + 0.72, "whoosh", 0.4, length=0.6, direction=-1)
cue(DUR + 1.25, "pop", 0.4, f0=500, f1=1000)
