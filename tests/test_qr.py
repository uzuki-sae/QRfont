import unittest

from qrfont.charset import load_charset
from qrfont.qr import BORDER, LABEL_CELLS, SIZE, decode_matrix, label_box, qr_matrix


class TestQrMatrix(unittest.TestCase):
    def test_29マス四方(self):
        m = qr_matrix("亜")
        self.assertEqual(SIZE, 29)
        self.assertEqual(len(m), SIZE)
        self.assertTrue(all(len(row) == SIZE for row in m))

    def test_余白4マスは白(self):
        m = qr_matrix("亜")
        for i in range(SIZE):
            for j in range(SIZE):
                if i < BORDER or j < BORDER or i >= SIZE - BORDER or j >= SIZE - BORDER:
                    self.assertFalse(m[i][j], (i, j))

    def test_数字もバイトモードで同じ大きさ(self):
        self.assertEqual(len(qr_matrix("1")), SIZE)

    def test_4バイトの字も入る(self):
        self.assertEqual(decode_matrix(qr_matrix("𠮟")), "𠮟")

    def test_全字が読み取れて元の字に戻る(self):
        failed = [ch for ch in load_charset() if decode_matrix(qr_matrix(ch)) != ch]
        self.assertEqual(failed, [])


class TestLabelBox(unittest.TestCase):
    def test_右下の余白の内側に接する(self):
        top, left, size = label_box()
        self.assertEqual(size, LABEL_CELLS)
        self.assertEqual(top + size, SIZE - BORDER)
        self.assertEqual(left + size, SIZE - BORDER)

    def test_白抜きした行列も全字読み取れる(self):
        top, left, size = label_box()
        failed = []
        for ch in load_charset():
            m = qr_matrix(ch)
            for i in range(top, top + size):
                for j in range(left, left + size):
                    m[i][j] = False
            if decode_matrix(m) != ch:
                failed.append(ch)
        self.assertEqual(failed, [])
