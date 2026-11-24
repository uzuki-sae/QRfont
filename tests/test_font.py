import tempfile
import unittest
from pathlib import Path

from fontTools.ttLib import TTFont

from qrfont.charset import load_charset
from qrfont.font import FAMILY, PS_NAME, UPM, build_font
from qrfont.render import decode_text, render_char


class TestFont(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.path = Path(cls.tmp.name) / f"{PS_NAME}.otf"
        build_font(cls.path)
        cls.font = TTFont(cls.path)

    @classmethod
    def tearDownClass(cls):
        cls.font.close()
        cls.tmp.cleanup()

    def test_全字がcmapにある(self):
        cmap = self.font.getBestCmap()
        missing = [ch for ch in load_charset() if ord(ch) not in cmap]
        self.assertEqual(missing, [])

    def test_空白は字幅だけの空グリフ(self):
        cmap = self.font.getBestCmap()
        name = cmap[0x20]
        self.assertEqual(self.font["hmtx"][name][0], UPM)
        self.assertEqual(self.font["CFF "].cff[0].CharStrings[name].calcBounds(None), None)

    def test_字幅はすべて正方形(self):
        cmap = self.font.getBestCmap()
        widths = {self.font["hmtx"][cmap[ord(ch)]][0] for ch in load_charset()}
        self.assertEqual(widths, {UPM})

    def test_フォント名(self):
        name = self.font["name"]
        self.assertEqual(name.getDebugName(1), FAMILY)
        self.assertEqual(name.getDebugName(6), PS_NAME)
        self.assertNotIn("IPA", FAMILY)
        self.assertNotIn("IPA", PS_NAME)

    def test_右下に字が描かれている(self):
        img = render_char(self.path, "亜", 290)
        cell = 290 // 29
        # 右下の白抜き部分に黒い画素がある（字の線）
        top = (29 - 4 - 6) * cell
        patch = img.crop((top, top, (29 - 4) * cell, (29 - 4) * cell))
        self.assertLess(patch.getextrema()[0], 128)

    def test_全グリフが読み取れて元の字に戻る(self):
        failed = [ch for ch in load_charset() if decode_text(render_char(self.path, ch, 116)) != ch]
        self.assertEqual(failed, [])
