"""Pieces of the Playwright episode drawn from ui.py: the HTML of a sign-in form, and a mock sign-in page inside a
browser window. Plain generic shapes: an illustration, not a screenshot of a real product."""
from vlog import *

FORM_CODE = [
    [("<form>", C_TAG)],
    [("  <input ", C_TAG), ("name", C_ATTR), ("=", C_DIM), ('"username"', C_STR), (">", C_TAG)],
    [("  <input ", C_TAG), ("name", C_ATTR), ("=", C_DIM), ('"password"', C_STR), (">", C_TAG)],
    [("  <button ", C_TAG), ("id", C_ATTR), ("=", C_DIM), ('"login"', C_STR), (">", C_TAG), ("Đăng nhập", C_TXT), ("</button>", C_TAG)],
    [("</form>", C_TAG)],
]


def login_page(L, a, t, url_k=1.0, user_k=0.0, pass_k=0.0, press=0.0, done=0.0, focus=None, wv=640, hv=560,
               url="app.phanmem.vn/login", show_page=1.0, hot_btn=0.0):
    """the mock sign-in page inside a browser window, in a local frame of wv x hv (use inside `with scaled`)."""
    page = U.window(L, (0, 0, wv, hv), a, url=url, url_k=url_k, t=t, typing=url_k < 1, r=26, bar=72)
    if show_page <= 0:
        return page
    pa = a * show_page
    c = L.c
    px0, py0, px1, py1 = page
    U.text(c, "Đăng nhập", font("xbold", 42), px0 + 56, py0 + 78, U.INK, pa)
    U.field(L, px0 + 56, py0 + 140, wv - 112, 66, "username", "huongdinh", user_k, pa, t=t, focus=focus == "user", size=32)
    U.field(L, px0 + 56, py0 + 262, wv - 112, 66, "password", "xxxxxxxx", pass_k, pa, t=t, focus=focus == "pass", password=True,
            size=32)
    if hot_btn > 0:
        c.drawRRect(rrect(px0 + 44, py0 + 356, px1 - 44, py0 + 446, 26), stroke(AMBER, 255 * hot_btn * pa / 255, width=5))
    U.button(L, px0 + 56, py0 + 368, wv - 112, 66, "Đăng nhập", pa, press=press, done=done, size=32)
    return page
