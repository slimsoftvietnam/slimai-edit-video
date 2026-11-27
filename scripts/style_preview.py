"""Show the edit styles on a frame of the user's own video, before asking which one they want.

python style_preview.py PROJECT OUT.jpg [--t SECONDS] [--spk M]

Run it after find_faces.py and send it together with look_choices.jpg. One storyboard row per style, in the
order of the question (the default first): three vertical frames for the styles made for 9:16, four 16:9 frames for
the vlog style, which is a horizontal YouTube edit. They are drawn with the skill's own fonts and the person matte, so
text stands behind the speaker as it will in the edit. The colour is the camera's own.
A new style needs a row in STYLES and a frame function here, a row in the style table in SKILL.md, and its own
reference file.
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("project")
ap.add_argument("out")
ap.add_argument("--t", type=float, default=None, help="source second to show (default: 40 % into the video)")
ap.add_argument("--spk", default=None, help="speaker to frame (default: the first one in project.json)")
args = ap.parse_args()

proj = os.path.abspath(args.project)
cfg = json.load(open(os.path.join(proj, "project.json"), encoding="utf-8"))
if not cfg.get("speakers"):
    sys.exit("run find_faces.py first: the frames are composed around a speaker")
os.environ["EDIT_PROJECT"] = proj
os.environ["EDIT_FMT"] = "tiktok"
os.environ["EDIT_SS"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import skia  # noqa: E402
import torch  # noqa: E402

import engine as E  # noqa: E402
import film_look as F  # noqa: E402
from gfx import big_text, chip, icon, kicker  # noqa: E402
from imgio import imwrite  # noqa: E402

W, H = E.W, E.H
t_src = args.t if args.t is not None else cfg["duration"] * 0.4
E.use_take(t_src)
SPK = args.spk or next(iter(E.FACE))

# ----------------------------------------------------------------------------
# the frame in the camera's own colour, its person matte, and the 9:16 view the edit would use
# ----------------------------------------------------------------------------
ws = min(1.0, 1920 / max(E.SRC_W, E.SRC_H))           # work at HD at most
fw, fh = int(round(E.SRC_W * ws)) // 2 * 2, int(round(E.SRC_H * ws)) // 2 * 2
transfer = cfg["transfer"]
rin = "full" if cfg.get("color_range") == "pc" else "limited"
rgb = F.source_frame(cfg["source"], t_src, (fw, fh), transfer, rin, iphone=True)
frame = np.ascontiguousarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1])

model = torch.jit.load(os.path.join(os.path.dirname(HERE), "assets", "rvm", "rvm_mobilenetv3_fp32.torchscript")).eval()
small = cv2.cvtColor(cv2.resize(frame, (fw // 2, fh // 2), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
src = torch.from_numpy(small).permute(2, 0, 1).float().div_(255).unsqueeze_(0)
rec = [None] * 4
with torch.no_grad():
    for _ in range(7):      # let the recurrent state settle on a single frame
        fgr, pha, *rec = model(src, *rec, 0.45)
matte = cv2.resize((pha[0, 0].clamp(0, 1).numpy() * 255 + 0.5).astype(np.uint8), (fw, fh), interpolation=cv2.INTER_LINEAR)

cx, cy, z = E.shot_cam(f"{SPK}_med")
CAM = (cx, cy, z, W / 2, H / 2)
M = (np.vstack([E.view_matrix(CAM, (0, 0)), [0, 0, 1]]) @ np.diag([1 / ws, 1 / ws, 1.0]))[:2]
VIEW = cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
MVIEW = cv2.warpAffine(matte, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
HX, HY = E.src_to_screen(CAM, E.FACE[SPK][0], E.FACE[SPK][2])     # head top on screen
T = 9.0     # draw every animated component at rest


def layer():
    L = E.Layer()
    L.begin()
    return L


def behind(img, L):
    E.behind_premul(img, L.arr, MVIEW)


def over(img, L):
    E.over_premul(img, L.arr)


def depth(L, text, size, **kw):
    """a word behind the speaker's head, as depth_word places it on a medium 9:16 shot."""
    kind = kw.pop("kind", "black")
    f = E.font(kind, size)
    cap = f.getMetrics().fCapHeight or size * 0.7
    big_text(L, T, 0, 99, text, min(max(HX, W * 0.3), W * 0.7), HY + cap * 0.36, size=size, kind=kind, max_w=W - 140,
             enter="none", **kw)


def caption(L, words, key):
    """one caption line as the edit draws it, with the keyword styled."""
    items = [(w, E.font("serif_ib", 66 * 1.15) if w in key else E.font("bold", 66), E.AMBER if w in key else E.WHITE)
             for w in words.split()]
    sp = 66 * 0.27
    total = sum(E.text_width(w, f) for w, f, _ in items) + sp * (len(items) - 1)
    x = W / 2 - total / 2
    for w, f, c in items:
        tw = E.text_width(w, f)
        E.draw_text(L, w, f, x + tw / 2, 1352, rgb=c, shadow=9, shadow_a=200)
        x += tw + sp


def bars(L, hb=104):
    L.c.drawRect(skia.Rect.MakeLTRB(0, 0, W, hb), E.fill((0, 0, 0), 255))
    L.c.drawRect(skia.Rect.MakeLTRB(0, H - hb, W, H), E.fill((0, 0, 0), 255))
    L.mark(0, 0, W, H, pad=0)


def card_line(L, text, y, kind, size, rgb=E.WHITE, track=0.0, glow=None):
    E.draw_text(L, text, E.font(kind, size), W / 2, y, rgb=rgb, tracking=track * size, glow=glow, glow_a=110,
                glow_blur=26)


# ----------------------------------------------------------------------------
# style 1: the standard edit
# ----------------------------------------------------------------------------
def std_depth():
    img = VIEW.copy()
    b, f_ = layer(), layer()
    depth(b, "Ý CHÍNH", 250, gradient=(E.WHITE, (200, 255, 236)))
    behind(img, b)
    chip(f_, T, 0, 99, W / 2, 330, "motion graphic", "spark", style="glow", size=40, accent=E.MINT)
    caption(f_, "phụ đề hiện theo từng chữ", {"từng", "chữ"})
    over(img, f_)
    return img


def std_diagram():
    stage = cv2.GaussianBlur(cv2.resize(VIEW, (W // 8, H // 8), interpolation=cv2.INTER_AREA), (0, 0), 3)
    img = (cv2.resize(stage, (W, H), interpolation=cv2.INTER_LINEAR) * 0.5).astype(np.uint8)
    x0, y0, x1, y1 = 60, 250, 1020, 800
    E.glass(img, x0, y0, x1, y1, r=44, sigma=18, alpha=1.0, tint_a=0.38, bright=0.92)
    cx0, cy0, cx1, cy1 = 125, 823, 955, 1290        # the speaker shrinks into this card: the whole two-shot
    s = min((cx1 - cx0) / fw, (cy1 - cy0) / fh)
    card = cv2.resize(frame, (int(fw * s), int(fh * s)), interpolation=cv2.INTER_AREA)
    ox, oy = int((cx0 + cx1 - card.shape[1]) / 2), int((cy0 + cy1 - card.shape[0]) / 2)
    img[oy:oy + card.shape[0], ox:ox + card.shape[1]] = card
    L = layer()
    c = L.c
    c.drawRRect(E.rrect(ox, oy, ox + card.shape[1], oy + card.shape[0], 28), E.stroke(E.WHITE, 64, width=2))
    kicker(L, T, 0, 99, "SƠ ĐỒ GIẢI THÍCH", W / 2, 330, size=30, rgb=E.AMBER)
    for bx, label, rgb, ic in ((300, "Cách cũ", E.CORAL, "clock"), (780, "Cách mới", E.MINT, "spark")):
        c.drawRRect(E.rrect(bx - 190, 420, bx + 190, 690, 30), E.fill(E.INK, 150))
        c.drawRRect(E.rrect(bx - 190, 420, bx + 190, 690, 30), E.stroke(rgb, 220, width=3))
        icon(c, ic, bx, 510, 90, rgb, 255, sw=5)
        E.draw_text(L, label, E.font("bold", 48), bx, 640, rgb=E.WHITE)
    c.drawLine(510, 555, 570, 555, E.stroke(E.WHITE, 220, width=5))
    c.drawLine(570, 555, 552, 540, E.stroke(E.WHITE, 220, width=5))
    c.drawLine(570, 555, 552, 570, E.stroke(E.WHITE, 220, width=5))
    L.mark(0, 0, W, H, pad=0)
    caption(L, "người nói thu vào khung", {"thu", "vào", "khung"})
    over(img, L)
    return img


def std_end():
    bl = cv2.resize(cv2.GaussianBlur(cv2.resize(VIEW, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 3.1),
                    (W, H), interpolation=cv2.INTER_LINEAR)
    img = (bl * 0.55).astype(np.uint8)
    L = layer()
    E.draw_text(L, "Một câu", E.font("black", 92), W / 2, 760, shadow=14, shadow_a=170)
    E.draw_text(L, "đáng nhớ", E.font("serif_ib", 120), W / 2, 900, rgb=E.AMBER, shadow=14, shadow_a=170,
                glow=(255, 170, 60), glow_a=120)
    chip(L, T, 0, 99, W / 2, 1070, "điều cần làm tiếp", "check", style="glow", size=40, accent=E.MINT)
    over(img, L)
    return img


# ----------------------------------------------------------------------------
# style 2: the film trailer (references/trailer.md)
# ----------------------------------------------------------------------------
def tr_montage():
    img = VIEW.copy()                     # the picture stays as shot: no darkened sky or room (references/trailer.md)
    b, f_ = layer(), layer()
    depth(b, "QUAY LẠI", 270, kind="serif_ib", rgb=E.CORAL, tracking=0.0, glow=(255, 90, 70))
    behind(img, b)
    c = f_.c
    f = E.font("bold", 40)
    x0 = W / 2 - (8 * 86 + 7 * 12) / 2
    c.drawRRect(E.rrect(x0 - 34, 262, W - x0 + 34, 384, 30), E.fill(E.INK, 165))     # the counter on its own plate
    E.draw_text(f_, "BƯỚC 03", f, W / 2 + 28, 320, rgb=E.CORAL, tracking=0.24 * 40)
    c.drawCircle(W / 2 + 28 - E.text_width("BƯỚC 03", f, 0.24 * 40) / 2 - 40, 306, 17, E.stroke(E.CORAL, 235, width=3))
    for i in range(8):
        xa = x0 + i * 98
        c.drawRRect(E.rrect(xa, 350, xa + 86, 362, 6), E.fill(E.CORAL if i < 3 else E.WHITE, 240 if i < 3 else 70))
    caption(f_, "mỗi nhát cắt một tiếng trống", {"tiếng", "trống"})
    bars(f_)
    over(img, f_)
    return img


def tr_card():
    img = np.zeros((H, W, 3), np.uint8)
    L = layer()
    card_line(L, "MỌI NGƯỜI ĐỀU NGHĨ", 878, "bold", 40, E.AMBER, 0.34)
    card_line(L, "RẤT KHÓ", 1012, "black", 124, track=0.03)
    card_line(L, "cho đến khi…", 1140, "serif_ib", 112, E.GOLD, glow=(255, 170, 60))
    over(img, L)
    return img


def tr_title():
    img = np.zeros((H, W, 3), np.uint8)
    L = layer()
    ft = E.font("black", 170)
    E.draw_text(L, "TÊN VIDEO", ft, W / 2, 860, tracking=0.02 * 170, gradient=(E.WHITE, (186, 198, 214)),
                glow=(255, 236, 200), glow_a=60, glow_blur=30)
    ly = 860 - E.ink_top(ft, "TÊN VIDEO") - 22        # above the Ê's mark, as trailer.title_card places it
    L.c.drawLine(W / 2 - 170, ly, W / 2 + 170, ly, E.stroke(E.AMBER, 180, width=2))
    E.draw_text(L, "Twist ở cuối, rồi tên phim.", E.font("serif_i", 50), W / 2, 958, rgb=E.AMBER)
    E.draw_text(L, "Rồi một câu mời follow", E.font("bold", 54), W / 2, 1180)
    E.draw_text(L, "hài mà trúng ý chính.", E.font("serif_ib", 60), W / 2, 1266, rgb=E.AMBER, glow=(255, 170, 60),
                glow_a=110, glow_blur=26)
    over(img, L)
    return img


# ----------------------------------------------------------------------------
# style 3: the chill vlog, cut on the music's beat (references/vlog.md): 16:9 frames on a canvas of their own
# ----------------------------------------------------------------------------
LW, LH = 1920, 1080
lsc = max(LW / fw, LH / fh)                       # the source frame, cover-fitted to 16:9
LM = np.array([[lsc, 0, (LW - fw * lsc) / 2], [0, lsc, (LH - fh * lsc) / 2]], np.float64)
LVIEW = cv2.warpAffine(frame, LM, (LW, LH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
LMATTE = cv2.warpAffine(matte, LM, (LW, LH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
LHX = E.FACE[SPK][0] * ws * lsc + LM[0, 2]       # the speaker's face x and head top on the 16:9 frame
LHY = E.FACE[SPK][2] * ws * lsc + LM[1, 2]
CREAM, PAPERC, INKB = (255, 244, 224), (252, 244, 228), (38, 32, 26)


class LCanvas:
    """a 16:9 transparent layer shaped like engine.Layer for draw_text, big_text and chip."""
    def __init__(self):
        self.arr = np.zeros((LH, LW, 4), np.uint8)
        self.surf = skia.Surface(self.arr, skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType)
        self.c = self.surf.getCanvas()

    def mark(self, *a, **k):
        pass


def lshade(L, y0, y1, a0, a1):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)],
                                               [E.col((10, 12, 10), a0), E.col((10, 12, 10), a1)]))
    L.c.drawRect(skia.Rect.MakeLTRB(0, y0, LW, y1), p)


def lcaption(L, words, key):
    items = [(w, E.font("serif_ib", 58 * 1.15) if w in key else E.font("bold", 58), E.AMBER if w in key else E.WHITE)
             for w in words.split()]
    sp = 58 * 0.27
    total = sum(E.text_width(w, f) for w, f, _ in items) + sp * (len(items) - 1)
    x = LW / 2 - total / 2
    for w, f, c in items:
        tw = E.text_width(w, f)
        E.draw_text(L, w, f, x + tw / 2, 968, rgb=c, shadow=8, shadow_a=200)
        x += tw + sp


def lplate(L, cx, cy, w, h, num, title, sub, accent):
    c = L.c
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    c.drawRRect(E.rrect(x0, y0 + 10, x1, y1 + 10, 26), E.fill((0, 0, 0), 70, blur=18))
    c.drawRRect(E.rrect(x0, y0, x1, y1, 26), E.fill(E.INK, 168))
    c.drawRRect(E.rrect(x0, y0, x1, y1, 26), E.stroke(E.WHITE, 52, width=1.6))
    E.draw_text(L, num, E.font("black", 72), x0 + 34, cy + 25, rgb=accent, align="left")
    tx = x0 + 34 + E.text_width(num, E.font("black", 72)) + 26
    E.draw_text(L, title, E.font("bold", 44), tx, cy - 8, align="left")
    E.draw_text(L, sub, E.font("medium", 30), tx, cy + 38, rgb=(222, 222, 212), align="left")


def vl_open():
    """the opening: a moment of the shoot, the episode's question in a title block over the trees"""
    img = LVIEW.copy()
    L = LCanvas()
    lshade(L, 0, 620, 150, 0)
    xr = 1812 if LHX < LW * 0.55 else 108
    al = "right" if xr > LW / 2 else "left"
    E.draw_text(L, "tập mới · chủ đề", E.font("bold", 36), xr, 122, rgb=E.AMBER, align=al, tracking=7.0, shadow=10,
                shadow_a=180)
    E.draw_text(L, "mở bằng một cảnh", E.font("xbold", 100), xr, 232, align=al, shadow=16, shadow_a=90)
    E.draw_text(L, "của buổi quay", E.font("xbold", 100), xr, 336, align=al, shadow=16, shadow_a=90)
    E.draw_text(L, "và câu hỏi của tập", E.font("serif_ib", 104), xr, 452, rgb=E.AMBER, align=al, shadow=16,
                shadow_a=90, glow=(255, 170, 60), glow_a=90)
    E.over_premul(img, L.arr)
    return img


def vl_card():
    """a chapter card on B-roll: two beats, then the chapter starts on the downbeat"""
    img = LVIEW.copy()
    L = LCanvas()
    lshade(L, 0, 600, 150, 0)
    lshade(L, 700, LH, 0, 110)
    E.draw_text(L, "02 / 05", E.font("bold", 40), LW / 2, 196, rgb=E.AMBER, tracking=8.0, shadow=10, shadow_a=170)
    L.c.drawLine(LW / 2 - 150, 226, LW / 2 + 150, 226, E.stroke(E.AMBER, 230, width=3))
    E.draw_text(L, "mỗi chương một thẻ", E.font("serif_ib", 128), LW / 2, 372, rgb=CREAM, shadow=16, shadow_a=90)
    E.over_premul(img, L.arr)
    return img


def vl_beat():
    """ideas in plates above the heads, each popping on a beat; every cut on the beat grid"""
    img = LVIEW.copy()
    L = LCanvas()
    lplate(L, 680, 212, 540, 156, "1", "ý thứ nhất", "hiện đúng phách nhạc", E.MINT)
    lplate(L, 1250, 212, 560, 156, "2", "ý thứ hai", "phách sau, không vội", E.SKY)
    c = L.c
    x0, x1, y = 420, 1500, 790
    c.drawRRect(E.rrect(x0 - 40, y - 46, x1 + 40, y + 40, 24), E.fill(E.INK, 150))
    for i in range(17):
        x = x0 + (x1 - x0) * i / 16
        big = i % 4 == 0
        c.drawLine(x, y - (18 if big else 9), x, y + (18 if big else 9),
                   E.stroke(E.WHITE, 230 if big else 120, width=3 if big else 2))
    for i in (4, 7, 12):
        x = x0 + (x1 - x0) * i / 16
        pth = skia.Path()
        pth.moveTo(x, y - 34)
        pth.lineTo(x + 13, y - 21)
        pth.lineTo(x, y - 8)
        pth.lineTo(x - 13, y - 21)
        pth.close()
        c.drawPath(pth, E.fill(E.AMBER, 255))
    E.draw_text(L, "nhát cắt", E.font("semi", 26), x0 + (x1 - x0) * 4 / 16, y + 36, rgb=E.AMBER)
    lcaption(L, "mỗi nhát cắt rơi đúng phách", {"đúng", "phách"})
    E.over_premul(img, L.arr)
    return img


def vl_paper():
    """the word behind the speaker, and a page of the travel journal for a definition"""
    img = LVIEW.copy()
    b = LCanvas()
    f = E.font("serif_ib", 250)
    cap = f.getMetrics().fCapHeight or 175
    big_text(b, T, 0, 99, "ý chính", min(max(LHX, 420), LW - 420), LHY + cap * 0.40, size=250, kind="serif_ib",
             rgb=E.AMBER, max_w=900, enter="none", glow=(255, 170, 60), tracking=0.0)
    E.behind_premul(img, b.arr, LMATTE)
    L = LCanvas()
    cx, cy, wd, hd = (1380 if LHX < LW / 2 else 540), 200, 720, 210
    c = L.c
    c.save()
    c.rotate(-2.0, cx, cy)
    c.drawRRect(E.rrect(cx - wd / 2 + 4, cy - hd / 2 + 16, cx + wd / 2 - 4, cy + hd / 2 + 18, 10), E.fill((0, 0, 0), 95, blur=22))
    c.drawRRect(E.rrect(cx - wd / 2, cy - hd / 2, cx + wd / 2, cy + hd / 2, 10), E.fill(PAPERC, 250))
    c.drawRect(skia.Rect.MakeLTRB(cx - 75, cy - hd / 2 - 17, cx + 75, cy - hd / 2 + 21), E.fill(E.AMBER, 150))
    E.draw_text(L, "từ khóa", E.font("serif_b", 74), cx - wd / 2 + 44, cy - 12, rgb=INKB, align="left")
    E.draw_text(L, "giải thích như trang sổ tay", E.font("serif_i", 44), cx - wd / 2 + 44, cy + 62, rgb=(176, 92, 30),
                align="left")
    c.restore()
    lcaption(L, "chữ đứng sau người nói", {"sau", "người"})
    E.over_premul(img, L.arr)
    return img


# ----------------------------------------------------------------------------
# style 4: motion viral, TikTok (references/motion.md). Drawn here without story.py: no timeline exists yet.
# ----------------------------------------------------------------------------
import ui as U  # noqa: E402  (mock software pieces: the cursor)

BLUE1, BLUE2, YEL, NAVYD = (34, 70, 214), (22, 50, 186), (255, 226, 60), (10, 22, 90)


def sunburst(img, cx, cy, rays=14, c1=BLUE1, c2=BLUE2):
    """a flat sunburst over the whole frame, in two blues"""
    L = layer()
    L.c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), E.fill(c2, 255))
    R = 3000
    for i in range(rays):
        a0 = 2 * np.pi * i / rays
        a1 = a0 + np.pi / rays
        pth = skia.Path()
        pth.moveTo(cx, cy)
        pth.lineTo(cx + R * np.cos(a0), cy + R * np.sin(a0))
        pth.lineTo(cx + R * np.cos(a1), cy + R * np.sin(a1))
        pth.close()
        L.c.drawPath(pth, E.fill(c1, 255))
    L.mark(0, 0, W, H, pad=0)
    over(img, L)


def extruded(L, text, size, y, rgb, depth=16, kind="black"):
    """3D title letters: a solid navy side, then the face"""
    f = E.font(kind, size)
    for k in range(depth, 0, -2):
        E.draw_text(L, text, f, W / 2 + k * 0.55, y + k * 0.75, rgb=NAVYD)
    E.draw_text(L, text, f, W / 2, y, rgb=rgb)


def mo_sticker():
    """frame 0: the speaker cut out like a sticker on a sunburst, the topic as a 3D title, the motif on screen"""
    img = np.zeros_like(VIEW)
    sunburst(img, W / 2, H * 0.56)
    m = MVIEW.astype(np.float32) / 255.0
    ring = cv2.dilate((MVIEW > 110).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (27, 27))).astype(np.float32)
    sh = cv2.GaussianBlur(np.roll(np.roll(ring, 16, 0), 10, 1), (0, 0), 7) * 0.4
    img = (img * (1 - sh[..., None])).astype(np.uint8)
    img = (img * (1 - ring[..., None]) + 255 * ring[..., None]).astype(np.uint8)
    img = (img * (1 - m[..., None]) + VIEW * m[..., None]).astype(np.uint8)
    L = layer()
    g = skia.Paint(AntiAlias=True)                   # a navy floor: the chair legs and the ground fade away
    g.setShader(skia.GradientShader.MakeLinear([skia.Point(0, H * 0.78), skia.Point(0, H)],
                                               [E.col(NAVYD, 0), E.col(NAVYD, 245)]))
    L.c.drawRect(skia.Rect.MakeLTRB(0, H * 0.78, W, H), g)
    extruded(L, "CHỦ ĐỀ", 190, 470, YEL)
    extruded(L, "NÓI RÕ TRONG", 104, 600, E.WHITE, depth=12)
    extruded(L, "2 GIÂY ĐẦU", 150, 760, YEL)
    U.Cursor([(0.0, 850, 612)], scale=5.0, t_in=0.0, t_out=1.0).draw(L, 0.5)
    over(img, L)
    return img


def mo_mask():
    """the reveal: black, and the key word's letters are windows onto the speaker; then a fly-through"""
    img = np.zeros_like(VIEW)
    L = layer()
    f = E.font("black", 300)
    for txt, y in (("TỪ", 820), ("KHÓA", 1110)):
        E.draw_text(L, txt, E.font("black", 300 if txt == "TỪ" else 250), W / 2, y, rgb=(255, 255, 255))
    a = L.arr[..., 3:4].astype(np.float32) / 255.0
    img = (VIEW * a).astype(np.uint8)
    L2 = layer()
    E.draw_text(L2, "CHỮ KHOÉT LỖ", E.font("bold", 40), W / 2, 520, rgb=E.AMBER, tracking=0.3 * 40)
    E.draw_text(L2, "máy quay bay xuyên qua một chữ", E.font("serif_i", 46), W / 2, 1290, rgb=E.WHITE)
    over(img, L2)
    return img


def mo_stack():
    """captions as magazine stacks: small white lead-in, the key word huge behind the head, small words after"""
    img = VIEW.copy()
    b, f_ = layer(), layer()
    key = E.font("black", 196)
    tw = E.text_width("từ khóa", key)
    x0 = max(70, min(W - 70 - tw, HX - tw / 2))
    yk = HY + 60
    for k in range(10, 0, -2):
        E.draw_text(b, "từ khóa", key, x0 + tw / 2 + k * 0.4, yk + k * 0.6, rgb=(8, 12, 26))
    E.draw_text(b, "từ khóa", key, x0 + tw / 2, yk, rgb=(40, 230, 228))
    behind(img, b)
    sm = E.font("black", 62)
    E.draw_text(f_, "câu nói có", sm, x0 + 8, yk - 190, rgb=E.WHITE, align="left", shadow=10, shadow_a=220)
    E.draw_text(f_, "xếp tầng", sm, x0 + tw - 8, yk + 76, rgb=E.WHITE, align="right", shadow=10, shadow_a=220)
    c = f_.c
    n, gap, x1, x2, yb = 6, 10, 70, 1010, 258
    wseg = (x2 - x1 - gap * (n - 1)) / n
    for i in range(n):
        xa = x1 + i * (wseg + gap)
        c.drawRRect(E.rrect(xa, yb, xa + wseg, yb + 9, 4.5), E.fill((40, 230, 228) if i < 2 else E.WHITE, 255 if i < 2 else 90))
    f_.mark(0, 0, W, H, pad=0)
    over(img, f_)
    return img


STYLES = [  # (label, one line for the sheet, frames) in the order of the question: the default first
    ("1 · Tiêu chuẩn (mặc định)", "Nhịp nhanh, chữ đứng sau người nói, sơ đồ, phụ đề từng chữ, nhạc nền nhẹ",
     (std_depth, std_diagram, std_end)),
    ("2 · Trailer phim", "Màn đen chèn chữ, trống dồn, im lặng trước khi lật bài, twist ở cuối · 45-90 giây",
     (tr_montage, tr_card, tr_title)),
    ("3 · Vlog chill (khớp nhạc)",
     "Nhịp chậm kiểu vlog du lịch, cắt và chữ đúng phách nhạc, thẻ chương · bản ngang YouTube",
     (vl_open, vl_card, vl_beat, vl_paper)),
    ("4 · Motion viral (TikTok)",
     "2 giây đầu rõ chủ đề, hình ảnh xuyên suốt, chữ khoét lỗ, phụ đề màu xếp tầng · 60-95 giây",
     (mo_sticker, mo_mask, mo_stack)),
]

# ----------------------------------------------------------------------------
# sheet: a label band and three frames per style
# ----------------------------------------------------------------------------
PW, PH, M_, GAP, BAND = 360, 640, 24, 16, 96
SW = M_ * 2 + 3 * PW + 2 * GAP
SH = M_ + len(STYLES) * (BAND + PH + M_)
sheet = np.full((SH, SW, 3), 18, np.uint8)
y = M_
TW = (SW - 2 * M_ - GAP) // 2                    # a 16:9 style: four frames in two rows
TH = TW * 9 // 16
for label, line, frames in STYLES:
    for k, fn in enumerate(frames):
        if len(frames) == 4:
            x, yy = M_ + (k % 2) * (TW + GAP), y + BAND + (k // 2) * (TH + GAP)
            sheet[yy:yy + TH, x:x + TW] = cv2.resize(fn(), (TW, TH), interpolation=cv2.INTER_AREA)
        else:
            x = M_ + k * (PW + GAP)
            sheet[y + BAND:y + BAND + PH, x:x + PW] = cv2.resize(fn(), (PW, PH), interpolation=cv2.INTER_AREA)
    y += BAND + PH + M_


class Canvas:
    """a skia canvas over the sheet, shaped like engine.Layer for draw_text."""
    def __init__(self, w, h):
        self.arr = np.zeros((h, w, 4), np.uint8)
        self.surf = skia.Surface(self.arr, skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType)
        self.c = self.surf.getCanvas()

    def mark(self, *a, **k):
        pass


cv_ = Canvas(SW, SH)
y = M_
for k, (label, line, _f) in enumerate(STYLES):
    E.draw_text(cv_, label, E.font("bold", 34), M_, y + 40, rgb=E.AMBER if k == 0 else E.WHITE, align="left")
    E.draw_text(cv_, line, E.font("regular", 24), M_, y + 78, rgb=(200, 200, 200), align="left")
    y += BAND + PH + M_
E.over_premul(sheet, cv_.arr)
imwrite(os.path.abspath(args.out), sheet, [1, 92])     # cv2.IMWRITE_JPEG_QUALITY = 1
print("wrote", os.path.abspath(args.out), f"(frame at {t_src:.1f} s, speaker {SPK})")
