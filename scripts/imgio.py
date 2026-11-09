"""cv2.imread / imwrite for any path. On Windows OpenCV cannot open paths with characters outside the system
code page (Vietnamese folder names, for example), and imwrite then fails without raising."""
import os

import cv2
import numpy as np


def imread(path, flags=cv2.IMREAD_COLOR):
    return cv2.imdecode(np.fromfile(path, np.uint8), flags)


def imwrite(path, img, params=()):
    ok, buf = cv2.imencode(os.path.splitext(path)[1], img, list(params))
    if not ok:
        raise OSError(f"could not encode {path}")
    buf.tofile(path)
