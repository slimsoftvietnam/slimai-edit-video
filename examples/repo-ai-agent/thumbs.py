"""YouTube thumbnails for this project. Run with: python thumbnail.py --project P [--outdir DIR]"""
from engine import AMBER, CORAL, MINT, WHITE, draw_text, font
from gfx import big_text
from thumbnail import cam_for, compose, pill


def thumb_question():
    """'AI AGENT' behind the speaker + 'đáng sợ?': the cold-open question."""
    def behind(L):
        big_text(L, 10, 0, 20, "AI AGENT", 930, 392, size=340, kind="black", max_w=1600, enter="none",
                 gradient=(WHITE, (255, 222, 182)), tracking=-0.025)

    def front(L):
        draw_text(L, "đáng sợ?", font("serif_ib", 250), 120, 860, rgb=CORAL, align="left", shadow=22,
                  shadow_a=240, glow=(255, 70, 50), glow_a=110, glow_blur=26)
        pill(L, 130, 980, "hay rất an toàn?", 46, MINT, "shield")

    return compose(4705, cam_for(1.15, 1250, 480, "M"), behind, front, keep_x0=560)


def thumb_repo():
    """'REPO' behind the speaker + 'folder có trí nhớ?': the definition angle."""
    def behind(L):
        big_text(L, 10, 0, 20, "REPO", 1180, 420, size=400, kind="black", max_w=1400, enter="none",
                 gradient=(WHITE, (205, 255, 238)), tracking=-0.03)

    def front(L):
        draw_text(L, "folder", font("black", 150), 110, 690, rgb=WHITE, align="left", shadow=22, shadow_a=240)
        draw_text(L, "có trí nhớ?", font("serif_ib", 170), 104, 870, rgb=AMBER, align="left", shadow=22,
                  shadow_a=240, glow=(255, 160, 50), glow_a=110, glow_blur=26)
        pill(L, 118, 990, "AI agent cần nó", 44, MINT, "robot")

    return compose(4700, cam_for(1.30, 1300, 500, "M"), behind, front, keep_x0=760)


THUMBS = {"YouTube_thumbnail_cinematic_A_dang_so.jpg": thumb_question, "YouTube_thumbnail_cinematic_B_repo.jpg": thumb_repo}
