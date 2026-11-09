"""Film look baked into a 3D LUT that runs directly on the camera signal (10-bit, float).

Chain: camera transfer (HLG / PQ / SDR) -> scene-linear -> filmic tone mapping with a soft highlight
shoulder (AgX-style, per channel in an inset gamut so saturated highlights roll off instead of
clipping) -> print look in OKLab (density, selective hue, split tone, print contrast) -> display.

Everything here is a pure colour transform, so one LUT handles it at 30+ fps in ffmpeg; the spatial
film effects (halation, grain, vignette) live in engine.py because they need neighbouring pixels.

    python film_look.py LOOK TRANSFER OUT.cube [--size 65]
"""
import argparse

import numpy as np

# ---------------------------------------------------------------------------- transfer functions
M_2020_709 = np.array([[1.660491, -0.587641, -0.072850],
                       [-0.124551, 1.132900, -0.008349],
                       [-0.018151, -0.100579, 1.118730]], np.float32)


def hlg_to_scene(e):
    a, b, c = 0.17883277, 0.28466892, 0.55991073
    e = np.clip(e, 0.0, 1.0)
    return np.where(e <= 0.5, e * e / 3.0, (np.exp((e - c) / a) + b) / 12.0)


def pq_to_nits(e):
    m1, m2, c1, c2, c3 = 0.1593017578125, 78.84375, 0.8359375, 18.8515625, 18.6875
    p = np.clip(e, 0.0, 1.0) ** (1.0 / m2)
    return 10000.0 * (np.maximum(p - c1, 0.0) / (c2 - c3 * p)) ** (1.0 / m1)


def decode(rgb, transfer):
    """camera signal -> scene-linear BT.709 primaries with 18 % grey at 0.18."""
    if transfer == "hlg":
        # BT.2408: 18 % grey sits at 38 % HLG signal
        lin = hlg_to_scene(rgb) * (0.18 / (0.38 * 0.38 / 3.0))
        return lin @ M_2020_709.T
    if transfer == "pq":
        # BT.2408: HDR reference white = 203 nits, 18 % grey ~ 26 nits
        lin = pq_to_nits(rgb) * (0.18 / 26.0)
        return lin @ M_2020_709.T
    # SDR Rec.709 file: undo the display encoding, then give highlights back the headroom the camera clipped away.
    # The tone map expects scene light well above 1.0; without this, SDR white lands at 70 % grey and the picture
    # looks murky. Shadows and mid-tones are barely touched, white ends up about 1.6 stops above its display value.
    x = np.clip(rgb, 0.0, 1.0)
    lin = np.where(x < 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)
    return lin * (1.12 + 2.0 * lin ** 2.5)


def encode_display(lin):
    """linear -> display signal; pure 2.2 is what phones and browsers actually show for BT.709."""
    return np.clip(lin, 0.0, 1.0) ** (1.0 / 2.2)


# ---------------------------------------------------------------------------- AgX-style tone map
AGX_IN = np.array([[0.842479062253094, 0.0784335999999992, 0.0792237451477643],
                   [0.0423282422610123, 0.878468636469772, 0.0791661274605434],
                   [0.0423756549057051, 0.0784336, 0.879142973793104]], np.float32)
AGX_OUT = np.array([[1.19687900512017, -0.0980208811401368, -0.0990297440797205],
                    [-0.0528968517574562, 1.15190312990417, -0.0989611768448433],
                    [-0.0529716355144438, -0.0980434501171241, 1.15107367264116]], np.float32)
EV_MIN, EV_MAX = -12.47393, 4.026069
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)


def agx_sigmoid(x):
    x2 = x * x
    x4 = x2 * x2
    return 15.5 * x4 * x2 - 40.14 * x4 * x + 31.96 * x4 - 6.868 * x2 * x + 0.4298 * x2 + 0.1191 * x - 0.00232


def tone_map(lin, slope, power, sat):
    v = np.maximum(lin @ AGX_IN.T, 1e-10)
    v = np.clip(np.log2(v), EV_MIN, EV_MAX)
    v = agx_sigmoid((v - EV_MIN) / (EV_MAX - EV_MIN))
    v = np.maximum(v * np.asarray(slope, np.float32), 0.0) ** np.asarray(power, np.float32)
    lum = (v @ LUMA)[..., None]
    v = lum + sat * (v - lum)
    v = v @ AGX_OUT.T
    return np.maximum(v, 0.0) ** 2.2


# ---------------------------------------------------------------------------- OKLab
def to_oklab(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    l = np.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
    m = np.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    s = np.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def from_oklab(L, a, b):
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return np.stack([4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
                     -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
                     -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s], -1)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def hue_window(h, center, width):
    d = np.abs((h - center + 180.0) % 360.0 - 180.0)
    return np.exp(-0.5 * (d / width) ** 2)


def print_look(lin, p):
    L, a, b = to_oklab(np.maximum(lin, 0.0))
    C = np.hypot(a, b)
    h = np.degrees(np.arctan2(b, a)) % 360.0
    Ls, Cs, dh = np.ones_like(L), np.ones_like(L), np.zeros_like(L)
    # selective colour: (center hue, width, hue shift, chroma gain, lightness gain). Neutrals barely move.
    grey = smooth(0.006, 0.03, C)
    for (center, width, shift, cg, lg, *gate) in p["selective"]:
        w = hue_window(h, center, width) * grey
        if gate:
            # lightness gate: mixed edge pixels (skin next to grass, 4:2:0 chroma) can land on this hue
            # at mid lightness; without it they light up as a coloured fringe
            w = w * smooth(gate[0] - 0.05, gate[0] + 0.05, L)
        dh += shift * w
        Cs *= 1.0 + (cg - 1.0) * w
        Ls *= 1.0 + (lg - 1.0) * w
    h2 = np.radians(h + dh)
    C2 = C * Cs * p["chroma"]
    L2 = L * Ls
    # subtractive density: the more saturated a colour, the darker it prints (dye, not light)
    L2 = L2 * (1.0 - p["density"] * np.clip(C2 / 0.28, 0, 1))
    # print contrast around a pivot
    piv, con = p["contrast"]
    L2 = np.where(L2 < piv, piv * (np.maximum(L2, 0) / piv) ** con,
                  1 - (1 - piv) * (np.maximum(1 - L2, 0) / (1 - piv)) ** con)
    a2, b2 = C2 * np.cos(h2), C2 * np.sin(h2)
    # split tone, weighted by the final lightness
    sh, hl = 1 - smooth(0.12, 0.62, L2), smooth(0.48, 0.96, L2)
    a2 = a2 + sh * p["shadow"][0] + hl * p["high"][0]
    b2 = b2 + sh * p["shadow"][1] + hl * p["high"][1]
    # print black (density never reaches zero light) and paper white
    lo, hi = p["black"], p["white"]
    L2 = lo + L2 * (hi - lo)
    return from_oklab(L2, a2, b2)


# ---------------------------------------------------------------------------- looks
LOOKS = {
    # warm print stock: creamy skin, deep moss foliage, rich sunset, teal-leaning shadows
    "cine_warm": dict(ev=-0.20, slope=(1.015, 1.0, 0.975), power=(1.34, 1.34, 1.34), sat=1.30, chroma=1.0,
                  selective=[(118, 18, 7, 0.72, 0.86),    # grass/foliage: lime -> deep moss
                             (45, 14, 6, 1.12, 1.01),     # skin: warmer, livelier
                             (80, 10, -6, 1.70, 0.97, 0.80),    # sunset sky (bright pixels only)
                             (245, 30, -20, 1.0, 0.98)],  # blues lean teal
                  density=0.08, contrast=(0.60, 1.34), shadow=(-0.008, -0.010), high=(0.004, 0.018),
                  black=0.030, white=0.985),
    # stronger complementary split, cooler shadows, for dusk / urban / night footage
    "teal_orange": dict(ev=-0.25, slope=(1.02, 1.0, 0.985), power=(1.36, 1.36, 1.36), sat=1.30, chroma=1.0,
                        selective=[(118, 20, 20, 0.62, 0.84), (45, 14, 8, 1.22, 1.01), (80, 10, -10, 1.9, 0.96, 0.80),
                                   (245, 34, -34, 1.1, 0.97)],
                        density=0.10, contrast=(0.60, 1.38), shadow=(-0.014, -0.016), high=(0.005, 0.014),
                        black=0.030, white=0.985),
    # clean documentary: filmic highlights, almost no colour opinion
    "neutral": dict(ev=-0.05, slope=(1, 1, 1), power=(1.30, 1.30, 1.30), sat=1.25, chroma=1.0, selective=[],
                    density=0.04, contrast=(0.55, 1.12), shadow=(0, 0), high=(0, 0), black=0.03, white=0.99),
}


def apply_look(signal, look="cine_warm", transfer="hlg"):
    """signal: float array (..., 3), camera R'G'B' in [0,1]. Returns display R'G'B' in [0,1]."""
    p = LOOKS[look]
    lin = decode(signal.astype(np.float32), transfer) * 2.0 ** p["ev"]
    lin = tone_map(lin, p["slope"], p["power"], p["sat"])
    return encode_display(print_look(lin, p))


def write_cube(path, look="cine_warm", transfer="hlg", size=65):
    r = np.linspace(0, 1, size, dtype=np.float32)
    b, g, rr = np.meshgrid(r, r, r, indexing="ij")     # .cube order: R fastest, then G, then B
    out = apply_look(np.stack([rr, g, b], -1).reshape(-1, 3), look, transfer)
    with open(path, "w", newline="\n") as f:
        f.write(f'TITLE "{look}-{transfer}"\nLUT_3D_SIZE {size}\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n')
        np.savetxt(f, out, fmt="%.6f")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("look", choices=sorted(LOOKS))
    ap.add_argument("transfer", choices=["hlg", "pq", "sdr"])
    ap.add_argument("out")
    ap.add_argument("--size", type=int, default=65)
    args = ap.parse_args()
    write_cube(args.out, args.look, args.transfer, args.size)
    print("wrote", args.out)
