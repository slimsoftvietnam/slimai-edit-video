"""Check that this machine can run the pipeline: python doctor.py"""
import importlib
import os
import shutil
import subprocess
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ok = True


def check(name, passed, detail=""):
    global ok
    ok &= bool(passed)
    print(f"{'OK  ' if passed else 'FAIL'} {name}{': ' + detail if detail else ''}")


check("ffmpeg", shutil.which("ffmpeg"))
check("ffprobe", shutil.which("ffprobe"))
if shutil.which("ffmpeg"):
    f = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    for flt in ("zscale", "lut3d", "atadenoise", "loudnorm", "ebur128", "afftdn"):
        check(f"ffmpeg filter {flt}", f" {flt} " in f)
    e = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    check("ffmpeg encoder libx264", "libx264" in e)
for mod, hint in (("numpy", ""), ("scipy", ""), ("cv2", "pip install opencv-python"), ("numba", ""), ("torch", ""),
                  ("whisper", "pip install openai-whisper"), ("skia", "pip install skia-python==87.9"),
                  ("PIL", "pip install pillow")):
    try:
        m = importlib.import_module(mod)
        check(mod, True, getattr(m, "__version__", ""))
    except Exception as ex:
        check(mod, False, f"{ex} {hint}")
try:
    import skia
    if not skia.__version__.startswith("87."):
        print(f"WARN skia-python {skia.__version__}: 144.x was ~100x slower on this PC, pin 87.9")
except Exception:
    pass
check("fonts", os.path.exists(os.path.join(SKILL_DIR, "assets", "fonts", "BeVietnamPro-Black.ttf")))
check("matting model", os.path.exists(os.path.join(SKILL_DIR, "assets", "rvm", "rvm_mobilenetv3_fp32.torchscript")))
print("ready" if ok else "fix the FAIL lines first")
sys.exit(0 if ok else 1)
