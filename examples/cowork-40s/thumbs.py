"""YouTube thumbnail for the test clip. Frame 690 is inside the master (clip 22.66-27.7 s)."""
from engine import AMBER, MINT, WHITE, draw_text, font
from gfx import big_text
from thumbnail import cam_for, compose, pill


def thumb():
    def behind(L):
        big_text(L, 10, 0, 20, "REPO?", 1150, 420, size=380, kind="black", max_w=1400, enter="none",
                 gradient=(WHITE, (205, 255, 238)), tracking=-0.03)

    def front(L):
        draw_text(L, "Cowork", font("black", 150), 110, 700, rgb=WHITE, align="left", shadow=22, shadow_a=240)
        draw_text(L, "có không?", font("serif_ib", 170), 104, 880, rgb=AMBER, align="left", shadow=22, shadow_a=240,
                  glow=(255, 160, 50), glow_a=110, glow_blur=26)
        pill(L, 118, 990, "folder hay repo", 44, MINT, "branch")

    return compose(690, cam_for(1.2, 1300, 500, "M"), behind, front, keep_x0=760)


THUMBS = {"Cowork_co_repo_thumbnail.jpg": thumb}
