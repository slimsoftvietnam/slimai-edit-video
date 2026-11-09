"""Repo / AI agent interview: one story, rendered as TikTok (9:16) and YouTube (16:9).

Everything is anchored to spoken words, so graphics and sound stay in sync whatever the cut.
pick(youtube, tiktok) and place(ctx, yt, tk) carry the format differences.
"""
import math

import skia

from story import *

# ----------------------------------------------------------------------------
# anchors: at(word, near) = output time of `word` closest to `near` (from words.txt)
# ----------------------------------------------------------------------------
for key, word, near in [
    ("agent0", "Agent", 0.28), ("tulam", "tự", 0.48), ("tuquyet", "tự", 1.02), ("rat0", "rất", 2.70),
    ("dangso", "đáng", 2.92), ("thucra", "Thực", 3.58), ("rat1", "rất", 3.94), ("antoan0", "an", 4.08),
    ("setup", "Em", 5.09), ("repo_share", "repo", 6.87), ("hoi", "hỏi", 8.00), ("repo_q", "repo", 9.10),
    ("cai_gi", "gì", 9.90), ("def", "Repo", 10.53), ("repository", "Repository", 12.37), ("tienganh", "tiếng", 14.18),
    ("nghia", "Nghĩa", 15.02), ("kho", "kho", 15.82), ("myth", "Nhiều", 16.27), ("lamtuong", "lầm", 17.19),
    ("folder0", "folder", 19.17), ("thucra2", "Thực", 19.82), ("hon", "hơn", 20.86), ("quantrong", "quan", 21.62),
    ("mem", "Nó", 22.74), ("tailieu", "tài", 24.75), ("file0", "file", 25.77), ("dulieu", "dữ", 25.97),
    ("nhung", "Nhưng", 26.97), ("trinho0", "trí", 27.67), ("trinho_q", "Trí", 28.29), ("lichsu", "lịch", 29.45),
    ("binhthuong", "Bình", 30.49), ("copy", "copy", 31.57), ("xoa0", "xóa", 32.07), ("khongbiet0", "không", 32.91),
    ("sua0", "Sửa", 33.69), ("khongbiet1", "không", 34.49), ("history", "history", 35.67), ("xoa1", "xóa", 37.44),
    ("sua1", "sửa", 37.90), ("nobiet", "biết", 38.58), ("diem2", "Điểm", 38.93), ("khongchi", "Không", 41.07),
    ("nhanh0", "nhánh", 42.64), ("nhanh_q", "nhánh", 43.16), ("khi", "Khi", 44.51), ("tailieu2", "tài", 45.99),
    ("kA", "A", 48.35), ("kB", "B", 49.77), ("kC", "C", 50.91), ("renhanh", "rẽ", 52.00), ("thesis", "Repo", 52.90),
    ("nomna", "nôm", 54.08), ("nolamot", "Nó", 55.59), ("folder_t", "folder", 56.21), ("trinho_t", "trí", 56.85),
    ("why", "Vì", 57.40), ("sao_w", "sao", 57.61), ("agent_w", "agent", 59.43), ("trinho_w", "trí", 61.11),
    ("agent_m", "Agent", 61.90), ("uythac", "ủy", 63.24), ("tuquyetdinh", "tự", 63.81), ("dasocacviec", "đa", 65.25),
    ("vay", "Vậy", 66.63), ("giao", "giao", 67.53), ("muonbiet", "biết", 70.51), ("tuqd2", "tự", 69.6),
    ("lamgi", "gì", 71.33), ("nho", "Nhỡ", 71.86), ("sai0", "sai", 72.46), ("quayve", "quay", 74.18),
    ("hientrang", "hiện", 74.78), ("vithe", "Vì", 75.76), ("chuyennghiep", "chuyên", 77.60), ("ketnoi0", "kết", 78.62),
    ("repo_kn", "repo", 79.34), ("anh", "Anh", 80.03), ("coding", "coding", 81.09), ("khaantoan", "khá", 82.83),
    ("antoan1", "an", 83.23), ("trinho_s", "trí", 85.57), ("neusai", "sai", 86.73), ("quaytrolai", "quay", 87.79),
    ("phienban", "phiên", 88.72), ("chatbot", "chatbot", 91.64), ("khongco", "không", 92.84), ("camera", "camera", 94.37),
    ("giamsat", "giám", 94.81), ("nhanvien", "nhân", 95.37), ("practical", "Và", 96.82), ("ketnoi1", "kết", 98.89),
    ("ketqua", "kết", 99.87), ("repo_p", "repo", 101.25), ("github", "GitHub", 102.85), ("ketnoi2", "kết", 103.40),
    ("de", "dễ", 104.10), ("closing", "Và", 104.47), ("khongchi2", "không", 105.85), ("code", "code", 107.30),
    ("tailieu3", "tài", 109.10), ("plan", "plan", 110.25), ("kehoach", "kế", 110.95), ("cungduoc", "được", 111.75),
    ("banthan", "Bản", 112.08), ("coding2", "coding", 112.60), ("rat_end", "rất", 114.20), ("antoan_end", "an", 114.38),
]:
    A[key] = at(word, near)

KEYS.update({
    "trí nhớ": ("serif_ib", AMBER, 1.22), "lịch sử": ("serif_ib", AMBER, 1.22), "history": ("serif_ib", AMBER, 1.22),
    "nhánh": ("serif_ib", AMBER, 1.22), "rẽ nhánh": ("serif_ib", AMBER, 1.22), "an toàn": ("serif_ib", MINT, 1.22),
    "đáng sợ": ("serif_ib", CORAL, 1.22), "ủy thác": ("serif_ib", AMBER, 1.22), "làm sai": ("serif_ib", CORAL, 1.22),
    "không biết": ("serif_ib", CORAL, 1.15), "cái kho": ("serif_ib", AMBER, 1.22), "phiên bản trước": ("serif_ib", AMBER, 1.15),
    "camera giám sát": ("serif_ib", AMBER, 1.15), "hiện trạng cũ": ("serif_ib", AMBER, 1.15), "tự quyết": ("serif_ib", AMBER, 1.15),
    "hơn thế": ("serif_ib", AMBER, 1.2), "repo": ("xbold", MINT, 1.0), "repository": ("xbold", MINT, 1.0),
    "agent": ("xbold", MINT, 1.0), "github": ("xbold", MINT, 1.0), "folder": ("xbold", WHITE, 1.0),
    "chatbot": ("xbold", WHITE, 1.0), "kết nối": ("serif_ib", AMBER, 1.15), "rất dễ": ("serif_ib", MINT, 1.15),
})
KEEP_CASE.update({"repository": "Repository", "a": "A", "b": "B", "c": "C"})
NO_BREAK.update({"Anh"})    # "tiếng Anh" is not a sentence start
COMPOUNDS.update({"các repo", "cái kho", "cái folder", "một folder", "các file", "cái nhánh", "hàng a", "hàng b", "hàng c",
                  "trạng cũ", "đội coding", "bản plan", "làm coding", "một version", "với agent", "với repo", "cái repo",
                  "cái trí", "các agent", "họ đã", "đã làm", "em có", "có trí", "có lịch", "có history", "cái camera",
                  "camera giám", "dùng agent", "dùng repo", "em xóa", "em sửa", "em copy", "chứa các", "để chứa",
                  "cái tài", "cái kết", "nối cái"})

# ----------------------------------------------------------------------------
# camera, picture-in-picture, transitions, music, chapters
# ----------------------------------------------------------------------------
if YT:
    SHOT_OVERRIDES.append((0.0, A["dangso"] - 0.06, "TWO_M"))    # cold open on the two-shot, title behind both
SHOT_OVERRIDES.extend([
    (A["dangso"] - 0.06, CL[2], "M_close"),                      # punch in on "đáng sợ"
    (A["thesis"] - 0.02, A["why"] - 0.05, "M_med"),
])
PUNCHES.extend([
    (A["antoan0"], 0.04, 0.10, 0.3, 0.5), (A["repository"], 0.04, 0.10, 0.4, 0.6), (A["hon"], 0.05, 0.08, 0.3, 0.6),
    (A["trinho0"], 0.05, 0.08, 0.4, 0.6), (A["folder_t"], 0.05, 0.10, 0.6, 0.8), (A["trinho_t"], 0.04, 0.08, 0.6, 0.8),
    (A["uythac"], 0.04, 0.08, 0.4, 0.6), (A["sai0"], 0.05, 0.06, 0.3, 0.5), (A["antoan1"], 0.04, 0.08, 0.4, 0.6),
    (A["khongco"], 0.05, 0.08, 0.4, 0.6), (A["de"], 0.04, 0.08, 0.3, 0.5), (A["antoan_end"], 0.05, 0.10, 0.8, 1.0),
])
# each diagram: the speaker shrinks away over PIP_T from t_in, the card fades in at t_in + 0.3, leaves by t_out
PIP.extend([
    (A["lamtuong"] - 0.1, A["hon"] - 0.15),
    (A["mem"] - 0.35, A["nhung"] - 0.12),
    (A["binhthuong"] - 0.4, A["diem2"] - 0.1),
    (A["khi"] - 0.4, A["thesis"] - 0.12),
    (A["tuquyetdinh"], A["vay"] - 0.12),
    (A["neusai"] - 0.35, A["chatbot"] - 0.95),
    (A["ketnoi1"] - 0.5, A["github"] - 0.45),
    (A["tailieu3"] - 1.15, A["banthan"] - 0.15),
])
LEAKS.extend([CL[2] - 0.1, A["def"] - 0.15, A["mem"] - 0.15, A["diem2"] - 0.1, A["why"] - 0.1, A["anh"] - 0.15,
              A["practical"] - 0.15, A["closing"] - 0.1])
LABELS.extend([
    (CL[2], "01", "Repo là gì?"), (A["myth"] - 0.1, "02", "Repo khác folder ở đâu?"),
    (A["binhthuong"] - 0.1, "02", "Khác biệt #1 · Lịch sử"), (A["diem2"] - 0.1, "03", "Khác biệt #2 · Rẽ nhánh"),
    (A["agent_m"] - 0.15, "04", "Vì sao agent cần repo?"), (A["anh"] - 0.1, "05", "An toàn: quay lại được"),
    (A["practical"] - 0.1, "06", "Mẹo nhỏ"),
])
YT_CHAPTERS.extend([
    (0.0, "Repo là gì? AI agent tự quyết có đáng sợ không"), (A["myth"] - 0.1, "Repo khác folder ở đâu: repo có lịch sử"),
    (A["diem2"] - 0.1, "Rẽ nhánh (branch) và \"folder có trí nhớ\""), (A["why"] - 0.1, "Vì sao dùng AI agent cần repo"),
    (A["anh"] - 0.1, "Agent làm sai? Quay lại phiên bản trước"),
    (A["practical"] - 0.1, "Mẹo: kết nối repo với GitHub, lưu cả tài liệu và kế hoạch"),
])
MUSIC.update(drop=A["antoan0"] - 0.04, stops=[A["folder_t"] - 0.32, A["khongco"] - 0.05], sections=[
    (A["antoan0"], "light", "main"), (A["myth"], "groove", "main"), (A["diem2"], "lift", "main"), (A["thesis"], "break", "calm"),
    (A["why"], "light", "main"), (A["anh"], "lift", "main"), (A["camera"], "break", "calm"), (A["practical"], "groove", "main"),
    (A["closing"], "outro", "calm"),
])


# ============================================================================
# HOOK
# ============================================================================
@ev(-0.5, A["dangso"] + 0.1)
def hook_agent(ctx, t):
    t0, t1 = -0.4, A["dangso"] - 0.06
    if YT and t0 <= t <= t1:
        # 16:9 cold open: the title stands behind both heads
        z = ctx.cam[2]
        cx, base = src_to_screen(ctx.cam, 978.0, 532.0)
        big_text(ctx.behind, t, t0, t1, "AI AGENT", cx, base, size=360 * z, kind="black", max_w=1560 * z,
                 gradient=(WHITE, (255, 226, 190)), enter="settle", stagger=0.045, fade_out=0.05, sheen=0.35, tracking=-0.02)
    elif TK:
        depth_word(ctx, t, t0, t1, "AI AGENT", size=250, gradient=(WHITE, (255, 226, 190)), enter="settle", stagger=0.045,
                   fade_out=0.14, sheen=0.35, t_ref=0.5)
    ky = pick(210, 300)
    for (tk, txt, x, ul) in ((A["tulam"], "TỰ LÀM", W / 2 - pick(210, 170), False), (A["tuquyet"], "TỰ QUYẾT", W / 2 + pick(210, 170), True)):
        v = env(t, tk - 0.05, A["dangso"] - 0.1, 0.25, 0.2)
        if v > 0:
            e = ease_out_cubic(clamp01((t - tk + 0.05) / 0.5))
            r = draw_text(ctx.front, txt, font("black", pick(56, 50)), x, ky + (1 - e) * 16, rgb=WHITE, a=255 * v, align="center",
                          tracking=pick(56, 50) * 0.16 * (1.0 + 0.6 * (1 - e)), shadow=16, shadow_a=235)
            ku = ease_in_out_cubic(clamp01((t - tk - 0.15) / 0.35))
            if ul and r is not None and ku > 0:
                xa, xb = r[0] + 44, r[2] - 44
                c = ctx.front.c
                c.drawLine(xa, ky + 26, lerp(xa, xb, ku), ky + 26, stroke(AMBER, 120 * v, width=14, blur=8))
                c.drawLine(xa, ky + 26, lerp(xa, xb, ku), ky + 26, stroke(AMBER, 255 * v, width=6))
                ctx.front.mark(xa - 20, ky + 6, xb + 20, ky + 46)


cue(0.05, "whoosh", 0.7, length=0.6, direction=1)
cue(A["tulam"], "tick", 0.55)
cue(A["tuquyet"], "tick", 0.55, f=3000)


@ev(A["dangso"] - 0.08, A["antoan0"] + 0.3)
def hook_scary(ctx, t):
    t0, t1 = A["dangso"] - 0.06, A["rat1"] + 0.05
    r = depth_word(ctx, t, t0, t1, "đáng sợ?", size=pick(310, 240), kind="serif_ib", rgb=CORAL, glow=(255, 80, 60),
                   enter="pop", stagger=0.03, tracking=0.0, fade_out=0.18)
    if r is not None and t >= A["thucra"]:
        x0, y0, x1, y1 = r
        strike(ctx.front, t, A["thucra"], x0 + 40, x1 - 40, y0 + (y1 - y0) * 0.56, rgb=WHITE, width=12, t1=t1, dur=0.28)


cue(A["dangso"] - 0.05, "impact", 0.55, length=1.6)
cue(A["thucra"], "swipe", 0.6)


@ev(A["rat1"] - 0.1, CL[2] + 0.1)
def hook_safe(ctx, t):
    depth_word(ctx, t, A["rat1"] - 0.08, CL[2] + 0.05, "RẤT AN TOÀN", size=pick(250, 200), gradient=(WHITE, (200, 255, 236)),
               enter="rise", stagger=0.03, fade_out=0.1)
    if t >= A["antoan0"]:
        x, y, _ = place(ctx, (-290, 25, ""), (W - 170, 420, ""))
        badge(ctx, t, A["antoan0"], CL[2] + 0.05, x, y, 78, "shield", MINT)


cue(A["antoan0"] - 0.02, "pop", 0.7, f0=600, f1=1250)
cue(A["antoan0"] - 1.0, "swell", 0.8, length=1.0)
cue(A["antoan0"] - 0.02, "shimmer", 0.5)


# ============================================================================
# SETUP: she asks; a repo card floats next to her
# ============================================================================
@ev(A["repo_share"] - 0.4, A["repo_q"] - 0.1)
def setup_card(ctx, t):
    t0, t1 = A["repo_share"] - 0.35, A["repo_q"] - 0.15
    if YT:
        hx, hy, yf = [src_to_screen(shot_cam("W_med"), FACE["W"][0], 0)[0], 0, src_to_screen(shot_cam("W_med"), 0, FACE["W"][1])[1]]
        x0, y0 = hx + 140, yf - 175
    else:
        x0, y0 = W / 2 - 250, 300
    x1, y1 = x0 + 500, y0 + 250
    v, dy = glass_panel(ctx, ctx.front, t, t0, t1, x0, y0, x1, y1, r=30)
    if v <= 0:
        return
    c = ctx.front.c
    a = 255 * v
    icon(c, "folder", x0 + 62, y0 + 78 + dy, 54, MINT, a, sw=5)
    draw_text(ctx.front, "awesome-agents", font("bold", 38), x0 + 102, y0 + 91 + dy, rgb=WHITE, a=a, align="left")
    c.drawLine(x0 + 34, y0 + 132 + dy, x1 - 34, y0 + 132 + dy, stroke(WHITE, 45 * v, width=1.5))
    chip(ctx.front, t, t0 + 0.2, t1, x0 + 34, y0 + 190 + dy, "24.1k", "star", style="glow", size=32, accent=AMBER, anchor="left")
    chip(ctx.front, t, t0 + 0.4, t1, x0 + 236, y0 + 190 + dy, "Fork", "fork", style="glow", size=32, accent=SKY, anchor="left")


cue(A["repo_share"] - 0.33, "pop", 0.45, f0=500, f1=900)
cue(A["repo_share"] - 0.15, "pop", 0.45, f0=560, f1=1000)
cue(A["repo_share"] + 0.05, "pop", 0.45, f0=620, f1=1100)


@ev(A["repo_q"] - 0.15, A["def"] - 0.05)
def setup_q(ctx, t):
    t0, t1 = A["repo_q"] - 0.1, A["def"] - 0.12
    r = depth_word(ctx, t, t0, t1, "REPO", size=pick(330, 300), gradient=(WHITE, (210, 255, 240)), enter="pop", stagger=0.05, spk="W")
    if r is not None and t >= A["cai_gi"] - 0.1:
        f = font("serif_ib", pick(260, 200) * ctx.cam[2] / z_max(round(t0, 3), round(t1, 3)))
        v = env(t, A["cai_gi"] - 0.1, t1, 0.001, 0.2)
        k = clamp01((t - (A["cai_gi"] - 0.1)) / 0.5)
        x0, y0, x1, y1 = r
        draw_text(ctx.front, "?", f, min(W - MX - 50, x1 + pick(40, 10)), y1 - 50 + (1 - ease_out_back(k)) * 60, rgb=AMBER, a=255 * v,
                  shadow=12, shadow_a=150, glow=AMBER, glow_a=110)


cue(A["repo_q"] - 0.1, "whoosh", 0.6, length=0.5, direction=-1)
cue(A["cai_gi"] - 0.08, "pop", 0.55, f0=700, f1=1300)


# ============================================================================
# DEFINITION
# ============================================================================
@ev(A["def"] - 0.1, A["myth"] - 0.05)
def def_repository(ctx, t):
    t_type = A["repository"] - 0.05
    t_end = A["nghia"] - 0.1
    if t < t_type:
        depth_word(ctx, t, A["def"] - 0.08, t_end, "REPO", size=pick(300, 280), enter="rise", gradient=(WHITE, (210, 255, 240)))
    else:
        n_extra = int(clamp01((t - t_type) / 0.42) * 6 + 0.0001)
        depth_word(ctx, t, A["def"] - 0.08, t_end, "REPO" + "SITORY"[:n_extra], size=pick(300, 280), enter="none",
                   gradient=(WHITE, (210, 255, 240)))
    depth_word(ctx, t, A["nghia"] + 0.05, A["myth"] - 0.1, "cái kho", size=pick(240, 230), kind="serif_ib", rgb=AMBER,
               glow=(255, 170, 60), enter="rise", tracking=0.0, fade_out=0.15)


for k_ in range(6):
    cue(A["repository"] - 0.05 + k_ * 0.07, "tick", 0.35, f=2200 + 180 * k_)
cue(A["nghia"] + 0.05, "whoosh", 0.4, length=0.45, direction=1)
cue(A["kho"], "ding", 0.35, f=1318.5)


# ============================================================================
# MYTH
# ============================================================================
@ev(A["lamtuong"] + 0.15, A["hon"] - 0.1)
def myth(ctx, t):
    t0, t1 = A["lamtuong"] + 0.2, A["hon"] - 0.15
    v, dy, x0, y0, x1, y1 = panel(ctx, t, t0, t1, 340, r=40, accent=CORAL)
    if v <= 0:
        return
    c = ctx.mid.c
    a = 255 * v
    icon(c, "warn", x0 + 70, y0 + 66 + dy, 40, CORAL, a, sw=4)
    draw_text(ctx.mid, "HIỂU LẦM PHỔ BIẾN", font("bold", 32), x0 + 104, y0 + 78 + dy, rgb=CORAL, a=a, align="left", tracking=5)
    cy = y0 + 236 + dy
    f_r, f_e, f_f = font("black", 92), font("bold", 84), font("black", 74)
    w_r, w_e, w_f = text_width("REPO", f_r), text_width("=", f_e), text_width("FOLDER", f_f)
    ic, gap = 66, 30
    xs = (x0 + x1) / 2 - (w_r + gap + w_e + gap + ic + 16 + w_f) / 2
    draw_text(ctx.mid, "REPO", f_r, xs, cy, rgb=MINT, a=a, align="left")
    xe = xs + w_r + gap
    draw_text(ctx.mid, "=", f_e, xe, cy - 4, rgb=WHITE, a=a, align="left")
    xi = xe + w_e + gap
    if t < A["folder0"] - 0.1:
        pulse = 0.82 + 0.18 * (0.5 + 0.5 * math.sin(t * 7.0))
        draw_text(ctx.mid, "?", font("serif_ib", 120), xi + (ic + 16 + w_f) / 2, cy + 6, rgb=AMBER,
                  a=a * pulse * clamp01((A["folder0"] - 0.1 - t) / 0.12), glow=AMBER, glow_a=90)
    if t >= A["folder0"] - 0.15:
        k = clamp01((t - (A["folder0"] - 0.15)) / 0.3)
        icon(c, "folder", xi + ic / 2, cy - 34, ic * (0.6 + 0.4 * spring(k)), WHITE, a * k, sw=7)
        draw_text(ctx.mid, "FOLDER", f_f, xi + ic + 16, cy, rgb=WHITE, a=a * k, align="left")
    if t >= A["thucra2"]:
        strike(ctx.mid, t, A["thucra2"], xe - 14, xi + ic + 16 + w_f + 14, cy - 32, rgb=CORAL, width=11, t1=t1, dur=0.3)


@ev(A["hon"] - 0.1, A["mem"] - 0.3)
def myth_more(ctx, t):
    depth_word(ctx, t, A["hon"] - 0.08, A["mem"] - 0.36, "HƠN THẾ", size=pick(270, 250), gradient=(WHITE, GOLD), enter="rise")


cue(A["folder0"] - 0.12, "pop", 0.45, f0=520, f1=1000)
cue(A["thucra2"], "swipe", 0.65)
cue(A["hon"] - 0.06, "impact", 0.35, length=1.2)


# ============================================================================
# MEMORY
# ============================================================================
@ev(A["mem"] - 0.1, A["nhung"] - 0.05)
def mem_folder(ctx, t):
    t0, t1 = A["mem"] - 0.05, A["nhung"] - 0.12
    h = pick(590, 530)
    v, dy, x0, y0, x1, y1 = panel(ctx, t, t0, t1, h)
    if v <= 0:
        return
    c = ctx.mid.c
    a = 255 * v
    cx = (x0 + x1) / 2
    cy = y0 + h * 0.6 + dy
    draw_text(ctx.mid, "Folder = chỗ chứa", font("bold", 56), cx, y0 + h * 0.17 + dy, rgb=WHITE, a=a)
    icon(c, "folder", cx, cy, h * 0.49, WHITE, a, sw=9)
    for i, (tt, lab) in enumerate(((A["tailieu"], "tài liệu"), (A["file0"], "file"), (A["dulieu"], "dữ liệu"))):
        if t < tt - 0.12:
            continue
        k = clamp01((t - (tt - 0.12)) / 0.5)
        e = ease_out_cubic(k)
        fx = cx - 240 + i * 240
        fy = lerp(y0 + h * 0.27, cy + 20, e)
        al = a * clamp01(k * 3) * (1 - 0.85 * clamp01((k - 0.75) / 0.25))
        icon(c, "file", fx, fy, 92, AMBER, al, sw=6)
        draw_text(ctx.mid, lab, font("semi", 38), fx, fy + 86, rgb=AMBER, a=al * (1 - e))


for tt_ in ("tailieu", "file0", "dulieu"):
    cue(A[tt_] - 0.08, "pop", 0.35, f0=700, f1=1100)


@ev(A["nhung"] - 0.1, A["binhthuong"] - 0.1)
def mem_trinho(ctx, t):
    depth_word(ctx, t, A["trinho0"] - 0.1, A["binhthuong"] - 0.15, "trí nhớ", size=pick(290, 250), kind="serif_ib", rgb=AMBER,
               glow=(255, 170, 60), enter="rise", tracking=0.0)
    if TK:
        chip(ctx.front, t, A["nhung"], A["binhthuong"] - 0.2, MX + 20, 260, "KHÁC BIỆT #1", None, style="glow", size=36, accent=AMBER, anchor="left")
    if t >= A["lichsu"] - 0.1:
        x, y, an = place(ctx, (190, 110, "left"), (W - MX - 20, 260, "right"))
        chip(ctx.front, t, A["lichsu"] - 0.05, A["binhthuong"] - 0.2, x, y, "Lịch sử", "history", style="glow", size=pick(44, 40), accent=MINT, anchor=an)


if TK:
    cue(A["nhung"], "pop", 0.45, f0=480, f1=880)
cue(A["trinho0"] - 0.1, "shimmer", 0.6)
cue(A["trinho0"] - 0.12, "whoosh", 0.45, length=0.5, direction=1)
cue(A["lichsu"] - 0.05, "pop", 0.5, f0=600, f1=1150)


@ev(A["binhthuong"] - 0.15, A["diem2"] - 0.05)
def mem_log(ctx, t):
    """Folder forgets (rows fade to '?') -> Repo remembers (commit log)."""
    t0, t1 = A["binhthuong"] - 0.1, A["diem2"] - 0.1
    h = pick(620, 550)
    v, dy, x0, y0, x1, y1 = panel(ctx, t, t0, t1, h, accent=MINT if t >= A["history"] - 0.15 else None)
    if v <= 0:
        return
    c = ctx.mid.c
    a = 255 * v
    repo_mode = t >= A["history"] - 0.15
    km = clamp01((t - (A["history"] - 0.15)) / 0.35)
    hdr_y = y0 + h * 0.168 + dy
    if not repo_mode:
        icon(c, "folder", x0 + 95, hdr_y - 20, 70, WHITE, a, sw=6)
        draw_text(ctx.mid, "Folder thường", font("xbold", 58), x0 + 158, hdr_y, rgb=WHITE, a=a, align="left")
    else:
        icon(c, "history", x0 + 95, hdr_y - 20, 70, MINT, a * km, sw=6)
        draw_text(ctx.mid, "Repo", font("black", 58), x0 + 158, hdr_y, rgb=MINT, a=a * km, align="left")
        draw_text(ctx.mid, "· nhớ hết", font("serif_ib", 60), x0 + 335, hdr_y + 2, rgb=AMBER, a=a * km, align="left")
    c.drawLine(x0 + 50, hdr_y + 44, x1 - 50, hdr_y + 44, stroke(WHITE, 55 * v, width=2))
    rows_folder = [(A["copy"], "copy  bao-cao.docx"), (A["xoa0"], "xóa  ke-hoach.xlsx"), (A["sua0"], "sửa  hop-dong.pdf")]
    rows_repo = [(A["history"] + 0.15, "14:02", "sửa hop-dong.pdf"), (A["xoa1"] - 0.05, "14:05", "xóa ke-hoach.xlsx"),
                 (A["sua1"] - 0.05, "14:09", "sửa bao-cao.docx")]
    ry0 = hdr_y + h * 0.24
    step = h * 0.194
    if not repo_mode:
        for i, (tt, lab) in enumerate(rows_folder):
            if t < tt - 0.08:
                continue
            k = clamp01((t - (tt - 0.08)) / 0.3)
            yy = ry0 + i * step
            forget = clamp01((t - (A["khongbiet0"] if i < 2 else A["khongbiet1"])) / 0.5)
            al = a * ease_out_cubic(k) * (1 - 0.78 * forget)
            dot(c, x0 + 95, yy - 17, 11, (210, 210, 210), al, glow=False)
            draw_text(ctx.mid, lab, font("semi", 50), x0 + 140 + (1 - ease_out_cubic(k)) * 30, yy, rgb=(240, 240, 240), a=al, align="left")
            if forget > 0:
                draw_text(ctx.mid, "?", font("serif_ib", 80), x1 - 95, yy + 8, rgb=CORAL, a=a * forget, align="center",
                          scale=0.7 + 0.3 * spring(forget))
    else:
        n_vis = sum(1 for (tt, *_r) in rows_repo if t >= tt - 0.1)
        if n_vis > 1:
            c.drawLine(x0 + 95, ry0 - 17, x0 + 95, ry0 - 17 + (n_vis - 1) * step, stroke(MINT, 170 * v, width=5))
        for i, (tt, tm, lab) in enumerate(rows_repo):
            if t < tt - 0.1:
                continue
            k = clamp01((t - (tt - 0.1)) / 0.3)
            e = ease_out_cubic(k)
            yy = ry0 + i * step
            al = a * e
            dot(c, x0 + 95, yy - 17, 14 * (0.6 + 0.4 * spring(k)), MINT, al)
            draw_text(ctx.mid, tm, font("bold", 44), x0 + 140 + (1 - e) * 40, yy, rgb=(170, 255, 225), a=al, align="left")
            draw_text(ctx.mid, lab, font("semi", 50), x0 + 300 + (1 - e) * 40, yy, rgb=WHITE, a=al, align="left")
            if t >= A["nobiet"] - 0.1:
                kk = clamp01((t - (A["nobiet"] - 0.1)) / 0.3)
                icon(c, "check", x1 - 95, yy - 17, 50, MINT, a * kk, sw=6)


for tt_ in ("copy", "xoa0", "sua0"):
    cue(A[tt_] - 0.08, "tick", 0.5, f=1800)
cue(A["khongbiet0"], "glitch", 0.35)
cue(A["khongbiet1"], "glitch", 0.3)
cue(A["history"] - 0.15, "shimmer", 0.5)
for tt_ in ("history", "xoa1", "sua1"):
    cue(A[tt_] - 0.05, "pop", 0.4, f0=650, f1=1200)
cue(A["nobiet"] - 0.1, "ding", 0.3, f=1567.98)


# ============================================================================
# BRANCHES
# ============================================================================
@ev(A["diem2"] - 0.1, A["khi"] - 0.05)
def br_intro(ctx, t):
    if TK:
        chip(ctx.front, t, A["diem2"], A["khi"] - 0.2, MX + 20, 260, "KHÁC BIỆT #2", None, style="glow", size=36, accent=AMBER, anchor="left")
    depth_word(ctx, t, A["nhanh0"] - 0.12, A["khi"] - 0.1, "nhánh", size=pick(300, 260), kind="serif_ib", rgb=AMBER,
               glow=(255, 170, 60), enter="rise", tracking=0.0)
    if A["khongchi"] - 0.1 <= t <= A["nhanh0"] + 0.2:
        x, y, an = place(ctx, (150, 90, "left"), (W - MX - 20, 350, "right"))
        chip(ctx.front, t, A["khongchi"] - 0.05, A["nhanh0"] + 0.1, x, y, "đã có trí nhớ", "check", style="glow", size=42, accent=AMBER, anchor=an)
    if t >= A["nhanh0"]:
        x, y, an = place(ctx, (175, 95, "left"), (W - MX - 20, 260, "right"))
        chip(ctx.front, t, A["nhanh0"] + 0.1, A["khi"] - 0.2, x, y, "branch", "branch", style="glow", size=pick(44, 40), accent=MINT, anchor=an)


if TK:
    cue(A["diem2"], "pop", 0.45, f0=480, f1=880)
cue(A["nhanh0"] - 0.12, "whoosh", 0.45, length=0.5, direction=1)
cue(A["khongchi"] - 0.05, "pop", 0.4, f0=520, f1=980)
cue(A["nhanh0"] + 0.1, "pop", 0.45, f0=600, f1=1150)


@ev(A["khi"] - 0.15, A["thesis"] - 0.05)
def br_graph(ctx, t):
    t0, t1 = A["khi"] - 0.1, A["thesis"] - 0.12
    h = pick(570, 530)
    v, dy, x0, y0, x1, y1 = panel(ctx, t, t0, t1, h, r=40)
    if v <= 0:
        return
    c = ctx.mid.c
    a = 255 * v
    my = (y0 + y1) / 2 + dy
    sx = x0 + 120
    kd = clamp01((t - t0 - 0.15) / 0.35)
    # the source document starts big in the middle, then glides left as the main line draws out of it
    km = ease_in_out_cubic(clamp01((t - (A["tailieu2"] - 0.2)) / 0.7))
    dx_, ds = lerp((x0 + x1) / 2, sx, km), lerp(150, 84, km)
    icon(c, "file", dx_, my, ds * (0.7 + 0.3 * ease_out_back(kd)), WHITE, a * kd, sw=lerp(7, 5, km))
    draw_text(ctx.mid, "Tài liệu gốc", font("semi", lerp(46, 36, km)), dx_, my + ds / 2 + 54, rgb=(235, 235, 235), a=a * kd)
    ex = x1 - 330
    pm = skia.Path()
    pm.moveTo(sx + 60, my)
    pm.lineTo(ex, my)
    draw_on_path(c, pm, clamp01((t - (A["tailieu2"] + 0.3)) / 0.6), stroke(WHITE, 140 * v, width=5))
    # a pulse runs along the main line while we wait for the first branch
    if A["tailieu2"] + 0.9 < t < A["kA"] - 0.3:
        u = ((t - A["tailieu2"] - 0.9) / 1.1) % 1.0
        dot(c, lerp(sx + 60, ex, ease_in_out_cubic(u)), my, 9, GOLD, a * math.sin(math.pi * u))
    off = h * 0.30
    branches = [(A["kA"], -off, "Bản khách A", AMBER), (A["kB"], 0, "Bản khách B", MINT), (A["kC"], off, "Bản khách C", SKY)]
    glow_on = clamp01((t - A["renhanh"]) / 0.4)
    for i, (tt, o, lab, rc) in enumerate(branches):
        if t < tt - 0.35:
            continue
        k = clamp01((t - (tt - 0.35)) / 0.55)
        bx0 = sx + 140 + i * 70
        ey = my + o
        path = skia.Path()
        path.moveTo(bx0, my)
        path.cubicTo(bx0 + 140, my, ex - 180, ey, ex, ey)
        draw_on_path(c, path, ease_out_cubic(k), stroke(rc, 255 * v, width=6 + 3 * glow_on))
        if glow_on > 0:
            draw_on_path(c, path, 1.0, stroke(rc, 110 * v * glow_on, width=16, blur=10))
        dot(c, bx0, my, 10, rc, a * clamp01(k * 3))
        if k > 0.7:
            kk = clamp01((k - 0.7) / 0.3)
            dot(c, ex, ey, 16 * (0.5 + 0.5 * spring(kk)), rc, a * kk)
            draw_text(ctx.mid, lab, font("bold", 44), ex + 32, ey + 15, rgb=WHITE, a=a * kk, align="left")


cue(A["tailieu2"] - 0.15, "pop", 0.35, f0=460, f1=820)
cue(A["kA"] - 0.1, "pluck", 0.55, note=74)
cue(A["kB"] - 0.1, "pluck", 0.55, note=78)
cue(A["kC"] - 0.1, "pluck", 0.55, note=81)
cue(A["renhanh"], "shimmer", 0.45)


# ============================================================================
# THESIS
# ============================================================================
@ev(A["thesis"] - 0.05, A["why"] - 0.05)
def thesis(ctx, t):
    x, y, an = place(ctx, (-190, -10, "right"), (W / 2, 280, "center"))
    chip(ctx.front, t, A["nomna"] - 0.05, A["folder_t"] - 0.15, x, y, "Nôm na là…", "spark", style="glow", size=46, accent=AMBER, anchor=an)
    t_end = A["why"] + 0.1
    if YT:
        depth_word(ctx, t, A["folder_t"] - 0.08, t_end, "FOLDER", size=320, gradient=(WHITE, (255, 236, 205)), enter="rise",
                   stagger=0.04, sheen=0.6, overlap=0.34)
        if t >= A["trinho_t"] - 0.14:
            x, y = anc(ctx, -315, 108)
            big_text(ctx.behind, t, A["trinho_t"] - 0.12, t_end, "có trí nhớ", x, y, size=112, kind="serif_ib", rgb=AMBER, glow=(255, 160, 50),
                     glow_a=150, enter="rise", stagger=0.03, tracking=0.0, max_w=680, shadow=14)
    else:
        hx, hy, _, _ = head(ctx)
        if t >= A["folder_t"] - 0.1:
            big_text(ctx.behind, t, A["folder_t"] - 0.08, t_end, "FOLDER", W / 2, hy - 215, size=270, kind="black",
                     gradient=(WHITE, (255, 236, 205)), enter="rise", stagger=0.04, max_w=880, sheen=0.6)
        if t >= A["trinho_t"] - 0.14:
            big_text(ctx.behind, t, A["trinho_t"] - 0.12, t_end, "có trí nhớ", W / 2, hy - 18, size=200, kind="serif_ib", rgb=AMBER,
                     glow=(255, 160, 50), glow_a=150, enter="rise", stagger=0.03, tracking=0.0, max_w=960)


cue(A["nomna"] - 0.05, "pop", 0.45, f0=450, f1=900)
cue(A["folder_t"] - 0.08, "whoosh", 0.55, length=0.5, direction=1)
cue(A["trinho_t"] - 0.12, "impact", 0.75, length=2.4)
cue(A["trinho_t"] - 0.12, "shimmer", 0.6)


# ============================================================================
# WHY AGENTS NEED IT
# ============================================================================
@ev(A["why"] - 0.05, A["agent_m"] - 0.05)
def why_q(ctx, t):
    depth_word(ctx, t, A["sao_w"] - 0.1, A["agent_m"] - 0.12, "VÌ SAO?", size=pick(300, 280), gradient=(WHITE, (255, 230, 200)),
               enter="pop", stagger=0.05, spk="W")
    if t >= A["agent_w"] - 0.2:
        x, y, an = place(ctx, (140, 30, "left"), (MX + 20, 300, "left"), "W")
        chip(ctx.front, t, A["agent_w"] - 0.1, A["agent_m"] - 0.15, x, y, "AI agent", "robot", style="glow", size=42, accent=MINT, anchor=an)
        x, y, an = place(ctx, (170, 120, "left"), (W - MX - 20, 300, "right"), "W")
        chip(ctx.front, t, A["trinho_w"] - 0.1, A["agent_m"] - 0.15, x, y, "trí nhớ", "brain", style="glow", size=42, accent=AMBER, anchor=an)


cue(A["agent_w"] - 0.1, "pop", 0.45, f0=520, f1=980)
cue(A["trinho_w"] - 0.1, "pop", 0.45, f0=600, f1=1150)


@ev(A["agent_m"] - 0.05, A["vay"] - 0.05)
def why_delegate(ctx, t):
    depth_word(ctx, t, A["agent_m"] + 0.42, A["tuquyetdinh"] + 0.4, "ỦY THÁC", size=pick(290, 250), gradient=(WHITE, GOLD), enter="rise",
               fade_out=0.2, sheen=0.5)
    t0, t1 = A["tuquyetdinh"] + 0.3, A["vay"] - 0.12
    h = pick(580, 530)
    v, dy, x0, y0, x1, y1 = panel(ctx, t, t0, t1, h)
    if v <= 0:
        return
    c = ctx.mid.c
    a = 255 * v
    my = y0 + h * 0.39 + dy
    ux, ax = x0 + 170, x1 - 190
    icon(c, "user", ux, my, 140, WHITE, a, sw=7)
    draw_text(ctx.mid, "Bạn", font("bold", 46), ux, my + 132, rgb=WHITE, a=a)
    k = clamp01((t - t0) / 0.6)
    arrow(c, ux + 100, my, ax - 110, k, AMBER, a)
    draw_text(ctx.mid, "giao việc", font("semi", 44), (ux + ax) / 2, my - 30, rgb=AMBER, a=a * k)
    kr = clamp01((t - t0 - 0.25) / 0.4)
    c.drawCircle(ax, my, 96, fill(MINT, 60 * v * kr, blur=26))
    icon(c, "robot", ax, my, 150 * (0.6 + 0.4 * spring(kr)), MINT, a * kr, sw=7)
    draw_text(ctx.mid, "Agent tự quyết", font("bold", 46), ax, my + 132, rgb=MINT, a=a * kr)
    c.drawLine(x0 + 50, y1 - h * 0.26 + dy, x1 - 50, y1 - h * 0.26 + dy, stroke(WHITE, 45 * v, width=1.5))
    labs = ["Đọc file", "Sửa", "Xóa bản cũ"]
    ft = font("semi", 42)
    ws = [46 + 14 + text_width(lab, ft) for lab in labs]
    g = (x1 - x0 - 120 - sum(ws)) / 2
    xx = x0 + 60
    for i, lab in enumerate(labs):
        tt = A["dasocacviec"] - 0.5 + i * 0.32
        if t >= tt:
            kk = clamp01((t - tt) / 0.25)
            yy = y1 - h * 0.12 + dy
            icon(c, "check", xx + 23, yy - 15, 46, MINT, a * kk, sw=6)
            draw_text(ctx.mid, lab, ft, xx + 60, yy, rgb=WHITE, a=a * kk, align="left")
        xx += ws[i] + g


cue(A["agent_m"] + 0.42, "whoosh", 0.5, length=0.5, direction=1)
for i_ in range(3):
    cue(A["dasocacviec"] - 0.5 + i_ * 0.32, "tick", 0.45, f=2400 + 200 * i_)


@ev(A["vay"] - 0.05, A["vithe"] - 0.05)
def why_risk(ctx, t):
    depth_word(ctx, t, A["tuqd2"] - 0.15, A["muonbiet"] - 0.12, "TỰ QUYẾT", size=pick(290, 240), gradient=(WHITE, GOLD), enter="rise", fade_out=0.2)
    x, y, an = place(ctx, (0, -170, "center"), (W / 2, 300, "center"))
    chip(ctx.front, t, A["muonbiet"] - 0.1, A["nho"] - 0.1, x, y, "Nó đã làm gì?", None, style="glow", size=46, accent=SKY, anchor=an)
    if t >= A["sai0"] - 0.15:
        x, y, an = place(ctx, (-165, -25, "right"), (MX + 30, 300, "left"))
        chip(ctx.front, t, A["sai0"] - 0.1, A["vithe"] - 0.12, x, y, "LÀM SAI", "warn", style="glow", size=pick(46, 40), accent=CORAL, anchor=an)
    if t >= A["quayve"] - 0.2:
        v = env(t, A["quayve"] - 0.15, A["vithe"] - 0.12, 0.001, 0.2)
        k = clamp01((t - (A["quayve"] - 0.15)) / 0.6)
        c = ctx.front.c
        x, y, _ = place(ctx, (255, -20, ""), (W - 210, 310, ""))
        c.drawCircle(x, y, 86, fill(INK, 150 * v))
        c.drawCircle(x, y, 86, stroke(AMBER, 230 * v, width=6, blur=9))
        c.drawCircle(x, y, 86, stroke(GOLD, 255 * v, width=2.6))
        c.save()
        c.translate(x, y)
        c.rotate(-360 * ease_out_cubic(k) * 0.35)
        icon(c, "undo", 0, 0, 100, AMBER, 255 * v, sw=7, prog=ease_out_cubic(k))
        c.restore()
        ctx.front.mark(x - 130, y - 130, x + 130, y + 130)
        if t >= A["hientrang"] - 0.1:
            chip(ctx.front, t, A["hientrang"] - 0.05, A["vithe"] - 0.12, x, y + 150, "trạng thái cũ", None, style="dark", size=38)


cue(A["muonbiet"] - 0.1, "pop", 0.45, f0=500, f1=950)
cue(A["tuqd2"] - 0.15, "whoosh", 0.4, length=0.5, direction=1)
cue(A["sai0"] - 0.1, "glitch", 0.45)
cue(A["quayve"] - 0.15, "rewind", 0.65)
cue(A["hientrang"] - 0.05, "pop", 0.4, f0=600, f1=1100)


@ev(A["vithe"] - 0.05, A["anh"] - 0.05)
def why_connect(ctx, t):
    t0, t1 = A["chuyennghiep"] - 0.2, A["anh"] - 0.12
    if t < t0:
        return
    v = env(t, t0, t1, 0.001, 0.25)
    c = ctx.front.c
    lx, y, _ = place(ctx, (-245, -150, ""), (300, 330, ""))
    rx = place(ctx, (245, -150, ""), (780, 330, ""))[0]
    k = clamp01((t - (A["ketnoi0"] - 0.1)) / 0.5)
    if k > 0:
        e = ease_in_out_cubic(k)
        xa, xb = lx + 120, rx - 120
        xm = lerp(xa, xb, e)
        c.drawLine(xa, y, xm, y, stroke(WHITE, 220 * v, width=5))
        c.drawLine(xa, y, xm, y, stroke(AMBER, 120 * v, width=14, blur=9))
        if k >= 1:
            dot(c, (xa + xb) / 2, y, 11, GOLD, 255 * v)
        ctx.front.mark(xa, y - 40, xb, y + 40)
    chip(ctx.front, t, t0, t1, lx, y, "Agent", "robot", style="glow", size=46, accent=MINT)
    chip(ctx.front, t, A["repo_kn"] - 0.15, t1, rx, y, "Repo", "history", style="glow", size=46, accent=AMBER)


cue(A["chuyennghiep"] - 0.2, "pop", 0.45, f0=500, f1=950)
cue(A["ketnoi0"] - 0.1, "connect", 0.6)
cue(A["repo_kn"] - 0.15, "pop", 0.45, f0=650, f1=1200)


# ============================================================================
# SAFETY
# ============================================================================
@ev(A["anh"] - 0.05, A["neusai"] - 0.05)
def safe_main(ctx, t):
    x, y, an = place(ctx, (0, -175, "center"), (W / 2, 330, "center"))
    chip(ctx.front, t, A["anh"] + 0.1, A["khaantoan"] - 0.2, x, y, "Anh hay nói với đội coding", "code", style="glow", size=pick(42, 40), accent=SKY, anchor=an)
    depth_word(ctx, t, A["antoan1"] - 0.12, A["neusai"] - 0.15, "AN TOÀN", size=pick(300, 260), gradient=(WHITE, (190, 255, 232)), enter="rise")
    if t >= A["antoan1"]:
        x, y, _ = place(ctx, (-235, 80, ""), (W - 150, 300, ""))
        badge(ctx, t, A["antoan1"], A["neusai"] - 0.15, x, y, 72, "shield", MINT)
    if t >= A["trinho_s"] - 0.15:
        x, y, an = place(ctx, (150, 90, "left"), (MX + 20, 300, "left"))
        chip(ctx.front, t, A["trinho_s"] - 0.1, A["neusai"] - 0.15, x, y, "vì có trí nhớ", "brain", style="glow", size=pick(44, 40), accent=AMBER, anchor=an)


cue(A["anh"] + 0.1, "pop", 0.4, f0=480, f1=900)
cue(A["antoan1"] - 0.12, "whoosh", 0.5, length=0.5, direction=1)
cue(A["antoan1"], "shimmer", 0.5)
cue(A["trinho_s"] - 0.1, "pop", 0.45, f0=600, f1=1100)


@ev(A["neusai"] - 0.05, A["chatbot"] - 0.9)
def safe_rollback(ctx, t):
    t0, t1 = A["neusai"] - 0.05, A["chatbot"] - 0.95
    v, dy, x0, y0, x1, y1 = panel(ctx, t, t0, t1, pick(540, 490))
    if v <= 0:
        return
    c = ctx.mid.c
    a = 255 * v
    ly = (y0 + y1) / 2 + dy - 20
    xs = [x0 + 150, (x0 + x1) / 2, x1 - 150]
    c.drawLine(xs[0], ly, xs[2], ly, stroke(WHITE, 120 * v, width=5))
    rb = clamp01((t - (A["quaytrolai"] - 0.1)) / 0.7)
    for i, x in enumerate(xs):
        bad = i == 2
        rc = CORAL if bad else MINT
        dot(c, x, ly, 24, rc if not (bad and rb > 0.5) else (140, 140, 140), a)
        draw_text(ctx.mid, ["v1", "v2", "v3"][i], font("black", 60), x, ly - 60, rgb=WHITE, a=a)
        if bad:
            icon(c, "cross", x, ly + 84, 52, CORAL, a, sw=7)
            draw_text(ctx.mid, "làm sai", font("semi", 44), x, ly + 160, rgb=CORAL, a=a)
    px = lerp(xs[2], xs[1], ease_in_out_cubic(rb))
    c.drawCircle(px, ly, 42, stroke(AMBER, 255 * v, width=6))
    c.drawCircle(px, ly, 56, fill(AMBER, 60 * v, blur=18))
    if rb > 0:
        c.drawLine(px, ly, xs[2], ly, stroke(AMBER, 90 * v * (1 - rb), width=12, blur=8))
    if rb >= 1:
        k2 = clamp01((t - (A["quaytrolai"] + 0.6)) / 0.35)
        icon(c, "check", xs[1], ly + 84, 56, MINT, a * k2, sw=7)
        draw_text(ctx.mid, "quay lại bản trước", font("bold", 40), xs[1], ly + 160, rgb=MINT, a=a * k2)


cue(A["quaytrolai"] - 0.1, "rewind", 0.7)
cue(A["quaytrolai"] + 0.6, "ding", 0.3, f=1318.5)


@ev(A["chatbot"] - 0.4, A["camera"] - 0.6)
def safe_compare(ctx, t):
    t0, t1 = A["chatbot"] - 0.2, A["camera"] - 0.7
    x, y, an = place(ctx, (0, -215, "center"), (W / 2, 262, "center"))
    chip(ctx.front, t, t0 - 0.25, t1, x, y, "Agent + Repo: quay lại được", "check", style="glow", size=pick(38, 40), accent=MINT, font_kind="bold", anchor=an)
    x, y, an = place(ctx, (0, -152, "center"), (W / 2, 372, "center"))
    r = chip(ctx.front, t, t0 + 0.05, t1, x, y, "Chatbot thông thường", "cross", style="dark", size=pick(38, 40), font_kind="semi", accent=CORAL, anchor=an)
    if r and t >= A["khongco"] - 0.05:
        x0, y0, x1, y1 = r
        strike(ctx.front, t, A["khongco"] - 0.05, x0 + 10, x1 - 10, (y0 + y1) / 2, rgb=CORAL, width=7, t1=t1)


cue(A["chatbot"] - 0.45, "pop", 0.45, f0=600, f1=1150)
cue(A["chatbot"] - 0.15, "pop", 0.4, f0=450, f1=800)
cue(A["khongco"] - 0.05, "swipe", 0.6)


# ============================================================================
# ANALOGY: surveillance camera
# ============================================================================
CCTV = (A["camera"] - 0.08, A["practical"] - 0.12)


@ev(CCTV[0], CCTV[1])
def cctv(ctx, t):
    t0, t1 = CCTV
    v = env(t, t0, t1, 0.08, 0.15)
    if v <= 0:
        return
    c = ctx.front.c
    mx, top, bot, L = pick(80, 70), pick(70, 240), pick(H - 70, H - 470), pick(130, 120)
    p = stroke(WHITE, 230 * v, width=6, cap="butt")
    for (x, y, dx, dy) in ((mx, top, 1, 1), (W - mx, top, -1, 1), (mx, bot, 1, -1), (W - mx, bot, -1, -1)):
        c.drawLine(x, y, x + dx * L, y, p)
        c.drawLine(x, y, x, y + dy * L, p)
    blink = 1.0 if int((t - t0) * 2.5) % 2 == 0 else 0.25
    c.drawCircle(mx + 55, top + 70, 15, fill((255, 50, 50), 255 * v * blink))
    draw_text(ctx.front, "REC", font("bold", 40), mx + 85, top + 84, rgb=WHITE, a=255 * v, align="left")
    tc = t - t0
    draw_text(ctx.front, f"00:01:{int(tc) + 34:02d}:{int((tc % 1) * 30):02d}", font("medium", 36), W - mx - 40, top + 84, rgb=WHITE, a=255 * v, align="right")
    draw_text(ctx.front, "CAM 01 · AGENT ĐANG LÀM VIỆC", font("semi", pick(34, 32)), mx + 40, top + 150, rgb=WHITE, a=230 * v, align="left", tracking=1.5,
              shadow=6, shadow_a=150)
    ctx.front.mark(0, top - 20, W, top + 190)
    ctx.front.mark(0, bot - 140, W, bot + 20)
    ctx.cctv = v


cue(CCTV[0], "beep", 0.5)
cue(CCTV[0] + 0.02, "shutter", 0.5)


# ============================================================================
# PRACTICAL
# ============================================================================
@ev(A["practical"] - 0.1, A["closing"] - 0.05)
def practical(ctx, t):
    if TK:
        chip(ctx.front, t, A["practical"] + 0.05, A["ketnoi1"] - 0.25, W / 2, 262, "Mẹo nhỏ", "spark", style="glow", size=46, accent=AMBER)
    t0, t1 = A["ketnoi1"] - 0.2, A["github"] - 0.45
    v, dy, x0, y0, x1, y1 = panel(ctx, t, t0, t1, 410, r=40)
    if v > 0:
        c = ctx.mid.c
        a = 255 * v
        my = (y0 + y1) / 2 + dy - 20
        lx, rx = x0 + 200, x1 - 200
        icon(c, "file", lx, my, 130, WHITE, a, sw=6)
        draw_text(ctx.mid, "Kết quả công việc", font("semi", 38), lx, my + 128, rgb=WHITE, a=a)
        arrow(c, lx + 110, my, rx - 110, clamp01((t - (A["ketqua"] - 0.2)) / 0.6), AMBER, a)
        kr = clamp01((t - (A["repo_p"] - 0.2)) / 0.4)
        c.drawCircle(rx, my, 86, fill(MINT, 50 * v * kr, blur=24))
        icon(c, "history", rx, my, 130 * (0.6 + 0.4 * spring(kr)), MINT, a * kr, sw=6)
        draw_text(ctx.mid, "Repo", font("xbold", 40), rx, my + 128, rgb=MINT, a=a * kr)
    gx, gy, an = place(ctx, (-170, -20, "right"), (W / 2, 262, "center"))
    chip(ctx.front, t, A["github"] - 0.08, A["closing"] - 0.12, gx, gy, "GitHub", "branch", style="glow", size=pick(56, 54), accent=WHITE, font_kind="bold", anchor=an)
    if t >= A["ketnoi2"] - 0.1:
        v2 = env(t, A["ketnoi2"] - 0.1, A["closing"] - 0.12, 0.001, 0.2)
        k = clamp01((t - (A["de"] - 0.15)) / 0.3)
        e = ease_out_back(k)
        c = ctx.front.c
        w_, h_ = 132, 70
        lw = text_width("Kết nối: dễ", font("bold", 48))
        if YT:
            x, y = gx - 25 - lw - 95 + w_ / 2, anc(ctx, 0, 62)[1]
        else:
            x, y = W / 2 - (w_ + 29 + lw) / 2 + w_ / 2, 372
        on_rgb = (lerp(90, MINT[0], k), lerp(90, MINT[1], k), lerp(90, MINT[2], k))
        c.drawRRect(rrect(x - w_ / 2, y - h_ / 2, x + w_ / 2, y + h_ / 2, h_ / 2), fill(on_rgb, 235 * v2))
        kx = lerp(x - w_ / 2 + h_ / 2, x + w_ / 2 - h_ / 2, e)
        c.drawCircle(kx, y, h_ / 2 - 7, fill(WHITE, 255 * v2))
        draw_text(ctx.front, "Kết nối: dễ", font("bold", 48), x + 95, y + 17, rgb=WHITE, a=255 * v2, align="left", shadow=8, shadow_a=170)
        ctx.front.mark(x - 90, y - 60, x + 360, y + 60)


cue(A["practical"] + 0.05, "pop", 0.45 if TK else 0.0, f0=520, f1=1000)
cue(A["repo_p"] - 0.2, "pop", 0.45, f0=600, f1=1150)
cue(A["github"] - 0.08, "pop", 0.55, f0=500, f1=1000)
cue(A["de"] - 0.15, "click", 0.7)


# ============================================================================
# CLOSING
# ============================================================================
@ev(A["closing"] - 0.05, A["banthan"] - 0.05)
def closing(ctx, t):
    depth_word(ctx, t, A["khongchi2"] - 0.1, A["tailieu3"] - 0.95, "KHÔNG CHỈ CODE", size=pick(250, 200), gradient=(WHITE, (210, 255, 240)), enter="rise", stagger=0.03)
    t_end = A["banthan"] - 0.15
    h = pick(590, 530)
    v_, dy, x0, y0, x1, y1 = panel(ctx, t, A["tailieu3"] - 0.85, t_end, h)
    bx, by = (x0 + x1) / 2, (y0 + y1) / 2 - 30
    o = h * 0.29
    items = [(A["tailieu3"] - 0.8, "Code", "code", MINT, (bx - 270, by - o)), (A["tailieu3"] - 0.1, "Tài liệu", "file", WHITE, (bx + 270, by - o)),
             (A["plan"] - 0.1, "Plan", "list", AMBER, (bx - 270, by + o)), (A["kehoach"] - 0.1, "Kế hoạch", "calendar", SKY, (bx + 270, by + o))]
    absorb = clamp01((t - (A["cungduoc"] - 0.05)) / 0.45)
    c = ctx.mid.c
    for (tt, lab, ic, rc, (x, y)) in items:
        if t < tt:
            continue
        e = ease_in_out_cubic(absorb)
        chip(ctx.mid, t, tt, t_end, lerp(x, bx, e), lerp(y, by, e), lab, ic, style="glow", size=48, accent=rc, alpha=1 - absorb * 0.9)
    if t >= A["cungduoc"] - 0.1:
        v = env(t, A["cungduoc"] - 0.1, t_end, 0.001, 0.2)
        k = clamp01((t - (A["cungduoc"] - 0.1)) / 0.5)
        r = 96 * (0.5 + 0.5 * spring(k, 6, 1.5))
        c.drawCircle(bx, by, r * 1.3, fill(MINT, 70 * v, blur=26))
        c.drawCircle(bx, by, r, fill(INK, 160 * v))
        c.drawCircle(bx, by, r, stroke(MINT, 255 * v, width=3))
        icon(c, "box", bx, by, r * 1.1, MINT, 255 * v, sw=6)
        draw_text(ctx.mid, "REPO", font("black", 44), bx, by + r + 56, rgb=MINT, a=255 * v, tracking=4)
        ctx.mid.mark(bx - 160, by - 160, bx + 160, by + 210)


cue(A["khongchi2"] - 0.1, "whoosh", 0.45, length=0.5, direction=1)
cue(A["tailieu3"] - 0.8, "pop", 0.4, f0=500, f1=950)
cue(A["tailieu3"] - 0.1, "pop", 0.4, f0=560, f1=1050)
cue(A["plan"] - 0.1, "pop", 0.4, f0=620, f1=1150)
cue(A["kehoach"] - 0.1, "pop", 0.4, f0=680, f1=1250)
cue(A["cungduoc"] - 0.1, "whoosh", 0.45, length=0.45, direction=1)
cue(A["cungduoc"] + 0.25, "ding", 0.35, f=1567.98)


@ev(A["banthan"] - 0.05, DUR + 1.2)
def finale(ctx, t):
    depth_word(ctx, t, A["rat_end"] - 0.12, DUR + 0.95, "RẤT AN TOÀN", size=pick(260, 210), gradient=(WHITE, (190, 255, 232)), enter="rise", stagger=0.035, sheen=0.55)
    x, y, an = place(ctx, (0, -165, "center"), (W / 2, 262, "center"))
    chip(ctx.front, t, A["banthan"] + 0.05, A["rat_end"] - 0.15, x, y, "Từ người làm coding", "code", style="glow", size=pick(44, 40), accent=AMBER, anchor=an)


cue(A["banthan"] + 0.05, "pop", 0.4, f0=480, f1=900)
cue(A["rat_end"] - 0.12, "whoosh", 0.5, length=0.55, direction=1)
cue(A["antoan_end"], "shimmer", 0.55)


@ev(DUR + 0.65, TOTAL)
def end_card(ctx, t):
    takeaway(ctx, t, DUR + 0.7, "Repo = folder", "có trí nhớ", "Lưu lại trước khi dùng AI agent")


cue(DUR + 0.72, "whoosh", 0.4, length=0.6, direction=-1)
cue(DUR + 1.25, "pop", 0.4, f0=500, f1=1000)
