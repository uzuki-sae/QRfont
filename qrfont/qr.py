"""1 字を記録した QR コードのマス目を作る・読む。

- UTF-8 のバイトモード、バージョン 1（21×21）、誤り訂正レベル H
- 余白 4 マスを含めて 29×29
- 右下の LABEL_CELLS×LABEL_CELLS マスを白抜きし、そこに字そのものを描く。
  6×6 にすると壊れる符号語は 6 個で、レベル H で直せる 8 個に 2 個の余裕が残る
"""

import cv2
import numpy as np
import qrcode
from qrcode.util import MODE_8BIT_BYTE, QRData

VERSION = 1
BORDER = 4
SIZE = 21 + BORDER * 2
LABEL_CELLS = 6


def qr_matrix(ch):
    """字 ch を記録した QR のマス目（True が黒）を SIZE×SIZE のリストで返す。"""
    qr = qrcode.QRCode(
        version=VERSION,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        border=BORDER,
    )
    qr.add_data(QRData(ch.encode("utf-8"), mode=MODE_8BIT_BYTE))
    qr.make(fit=False)
    return [list(row) for row in qr.get_matrix()]


def label_box():
    """字を描く白抜き部分の (上の行, 左の列, 一辺のマス数)。"""
    start = SIZE - BORDER - LABEL_CELLS
    return start, start, LABEL_CELLS


def labeled_matrix(ch):
    """右下を白抜きしたマス目。"""
    m = qr_matrix(ch)
    top, left, size = label_box()
    for i in range(top, top + size):
        for j in range(left, left + size):
            m[i][j] = False
    return m


_DETECTORS = (cv2.QRCodeDetector(), cv2.QRCodeDetectorAruco())


def decode_image(gray):
    """グレースケール画像（numpy 配列）から QR を読む。読めなければ空文字。

    OpenCV の 2 種類の読み取り器のどちらかで読めればよい（片方だけ位置検出に失敗することがある）。
    """
    for det in _DETECTORS:
        text, _, _ = det.detectAndDecode(gray)
        if text:
            return text
    return ""


def decode_matrix(m, cell=8):
    """マス目を 1 マス cell 画素の画像にして読む。"""
    arr = np.array(m, dtype=bool)
    img = np.where(arr, 0, 255).astype(np.uint8)
    img = np.kron(img, np.ones((cell, cell), dtype=np.uint8))
    return decode_image(img)
