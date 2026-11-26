"""YouTube thumbnails for the Playwright episode (warm film look, from the master).
Run with: python thumbnail.py --project P --outdir EP_DIR --prefix NAME

Two angles, neither repeats a title: A = her doubt as a picture ("AI tự bấm chuột?"), B = his answer as a riddle
("không nhìn mà bấm đúng?"). Each is one person, cropped out of the two-shot: she sits on the right of A, he on the
left of B, the words on the open side over the trees.
"""
from engine import AMBER, CORAL, MINT, WHITE, draw_text, font
from gfx import big_text
from thumbnail import cam_for, compose, pill

F_HER = 11106      # 370.2 s: she faces the camera, both hands up (the call to action)
F_HIM = 4158       # 138.6 s: his hand raised, explaining ("nó không chụp ảnh màn hình…")


def thumb_question():
    def behind(L):
        big_text(L, 10, 0, 20, "AI", 300, 400, size=440, kind="black", max_w=620, enter="none",
                 gradient=(WHITE, (255, 226, 190)), tracking=-0.02)

    def front(L):
        draw_text(L, "tự bấm", font("black", 190), 96, 640, rgb=WHITE, align="left", shadow=24, shadow_a=240)
        draw_text(L, "chuột?", font("serif_ib", 250), 90, 866, rgb=AMBER, align="left", shadow=24, shadow_a=240,
                  glow=(255, 160, 50), glow_a=110, glow_blur=26)
        pill(L, 104, 986, "không ai cầm chuột cả", 46, MINT, "spark")

    return compose(F_HER, cam_for(2.15, 1370, 430, "W"), behind, front, keep_x0=700)


def thumb_riddle():
    def behind(L):
        pass

    def front(L):
        x = 1840
        draw_text(L, "không nhìn", font("black", 170), x, 330, rgb=WHITE, align="right", shadow=24, shadow_a=240)
        draw_text(L, "mà bấm", font("black", 170), x, 520, rgb=WHITE, align="right", shadow=24, shadow_a=240)
        draw_text(L, "đúng?", font("serif_ib", 270), x + 6, 770, rgb=AMBER, align="right", shadow=24, shadow_a=240,
                  glow=(255, 160, 50), glow_a=110, glow_blur=26)
        f = font("bold", 46)
        from engine import text_width
        w = text_width("AI đọc cái gì trên trang web?", f) + 46 * 1.6 + 46 * 1.55
        pill(L, x - w, 936, "AI đọc cái gì trên trang web?", 46, MINT, "code")

    return compose(F_HIM, cam_for(2.2, 520, 440, "M"), behind, front, keep_x0=0)


THUMBS = {"thumbnail_A.jpg": thumb_question, "thumbnail_B.jpg": thumb_riddle}
