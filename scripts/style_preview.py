"""Show the edit styles on a frame of the user's own video, before asking which one they want.

python style_preview.py PROJECT OUT.jpg [--t SECONDS] [--spk M]

Run it after find_faces.py and send it together with look_choices.jpg. One storyboard row per style, in the
order of the question (the default first), three vertical frames each. They are drawn with the skill's own fonts
and the person matte, so text stands behind the speaker as it will in the edit. The colour is the camera's own.
A new style needs a row in STYLES and a frame function here, a row in the style table in SKILL.md, and its own
reference file.
"""
import argparse
import json
import os
import subprocess
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
matrix = "2020_ncl" if transfer in ("hlg", "pq") else "709"
rin = "full" if cfg.get("color_range") == "pc" else "limited"
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t_src:.2f}", "-i", cfg["source"], "-frames:v", "1", "-vf",
                      f"zscale=w={fw}:h={fh}:filter=lanczos:min={matrix}:rin={rin}:r=full,format=gbrpf32le",
                      "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
planes = np.frombuffer(raw, np.float32).reshape(3, fh, fw)
rgb = F.apply_look(np.stack([planes[2], planes[0], planes[1]], -1).reshape(-1, 3), "iphone", transfer).reshape(fh, fw, 3)
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
    img = VIEW.copy()
    b, f_ = layer(), layer()
    b.c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), E.fill((0, 0, 0), 100))          # the room dimmed, not the people
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 104), skia.Point(0, 600)],
                                               [skia.Color4f(0, 0, 0, 0.62), skia.Color4f(0, 0, 0, 0)]))
    b.c.drawRect(skia.Rect.MakeLTRB(0, 0, W, 600), p)
    b.mark(0, 0, W, H, pad=0)
    depth(b, "QUAY LẠI", 270, kind="serif_ib", rgb=E.CORAL, tracking=0.0, glow=(255, 90, 70))
    behind(img, b)
    c = f_.c
    f = E.font("bold", 40)
    E.draw_text(f_, "BƯỚC 03", f, W / 2 + 28, 320, rgb=E.CORAL, tracking=0.24 * 40, shadow=8, shadow_a=170)
    c.drawCircle(W / 2 + 28 - E.text_width("BƯỚC 03", f, 0.24 * 40) / 2 - 40, 306, 17, E.stroke(E.CORAL, 235, width=3))
    x0 = W / 2 - (8 * 86 + 7 * 12) / 2
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
    E.draw_text(L, "TÊN VIDEO", E.font("black", 170), W / 2, 1000, tracking=0.02 * 170, gradient=(E.WHITE, (186, 198, 214)),
                glow=(255, 236, 200), glow_a=60, glow_blur=30)
    L.c.drawLine(W / 2 - 170, 880, W / 2 + 170, 880, E.stroke(E.AMBER, 180, width=2))
    E.draw_text(L, "Twist ở cuối, rồi tên phim.", E.font("serif_i", 50), W / 2, 1098, rgb=E.AMBER)
    over(img, L)
    return img


STYLES = [  # (label, one line for the sheet, frames) in the order of the question: the default first
    ("1 · Tiêu chuẩn (mặc định)", "Nhịp nhanh, chữ đứng sau người nói, sơ đồ, phụ đề từng chữ, nhạc nền nhẹ",
     (std_depth, std_diagram, std_end)),
    ("2 · Trailer phim", "Màn đen chèn chữ, trống dồn, im lặng trước khi lật bài, twist ở cuối · 45-60 giây",
     (tr_montage, tr_card, tr_title)),
]

# ----------------------------------------------------------------------------
# sheet: a label band and three frames per style
# ----------------------------------------------------------------------------
PW, PH, M_, GAP, BAND = 360, 640, 24, 16, 96
SW = M_ * 2 + 3 * PW + 2 * GAP
SH = M_ + len(STYLES) * (BAND + PH + M_)
sheet = np.full((SH, SW, 3), 18, np.uint8)
y = M_
for label, line, frames in STYLES:
    for k, fn in enumerate(frames):
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
