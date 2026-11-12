"""YouTube thumbnails for the 16:9 trailer. Run: python thumbnail.py --project P --outdir EP_DIR --prefix YT_NAME

A: him explaining, "AGENT" behind him and "làm thay bạn?": what an agent is.
B: her at the hook, "Bạn đang làm thay AI?": the twist as a question, in words that no title uses.
Both frames are inside the master, in the camera's own colour.
"""
from engine import AMBER, CORAL, MINT, SKY, WHITE, draw_text, font
from gfx import big_text
from thumbnail import cam_for, compose, pill


def thumb_agent():
    def behind(L):
        big_text(L, 10, 0, 20, "AGENT", 1300, 400, size=360, kind="black", max_w=1150, enter="none",
                 gradient=(WHITE, (200, 255, 236)), tracking=-0.03)

    def front(L):
        draw_text(L, "làm thay", font("black", 150), 110, 690, rgb=WHITE, align="left", shadow=22, shadow_a=240)
        draw_text(L, "bạn?", font("serif_ib", 200), 104, 880, rgb=AMBER, align="left", shadow=22, shadow_a=240,
                  glow=(255, 160, 50), glow_a=110, glow_blur=26)
        pill(L, 118, 990, "không chỉ hỏi đáp", 44, MINT, "robot")

    return compose(4995, cam_for(2.1, 1250, 500, "M"), behind, front, keep_x0=880)    # framed so she is out of shot


def thumb_twist():
    def front(L):
        draw_text(L, "Bạn đang làm", font("black", 130), 100, 640, rgb=WHITE, align="left", shadow=22, shadow_a=240)
        draw_text(L, "thay AI?", font("serif_ib", 210), 94, 850, rgb=CORAL, align="left", shadow=22, shadow_a=240,
                  glow=(255, 70, 50), glow_a=110, glow_blur=26)
        pill(L, 108, 975, "hỏi, copy, sửa, gửi…", 44, SKY, "chat")

    return compose(120, cam_for(2.0, 1300, 470, "W"), lambda L: None, front, keep_x0=700)


THUMBS = {"thumbnail_A.jpg": thumb_agent, "thumbnail_B.jpg": thumb_twist}
