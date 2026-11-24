"""大きさ（1em の画素数）ごとに、全字が QR として読めるかを数える。

    python scripts/measure_min_size.py 58 72 87 116

描いた画像をなめらかに拡大してから OpenCV で読む（カメラで撮った状態に近づけるため）。
OpenCV の読み取り器は画像の大きさによって位置検出に失敗することがあるので、
拡大率 4・6・8 倍のどれかで読めれば「読めた」とする。
"""

import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from qrfont.charset import load_charset  # noqa: E402
from qrfont.font import PS_NAME  # noqa: E402
from qrfont.qr import decode_image  # noqa: E402
from qrfont.render import render_char  # noqa: E402

FONT = ROOT / "fonts" / f"{PS_NAME}.otf"


def readable(ch, px):
    img = np.array(render_char(FONT, ch, px, margin=8))
    for scale in (4, 6, 8):
        big = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        if decode_image(big) == ch:
            return True
    return False


chars = load_charset()
for arg in sys.argv[1:]:
    px = int(arg)
    failed = [ch for ch in chars if not readable(ch, px)]
    print(f"{px}px（1マス {px / 29:.2f}px）: {len(chars) - len(failed)}/{len(chars)} 字読めた {''.join(failed)}")
