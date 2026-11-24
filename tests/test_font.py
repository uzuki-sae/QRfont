import tempfile
import unittest
from pathlib import Path

from fontTools.ttLib import TTFont

from qrfont.charset import load_charset, load_charset_jp
from qrfont.font import FAMILY, PS_NAME, UPM, build_font, label_source
from qrfont.render import decode_text, render_char


class TestLabelSource(unittest.TestCase):
    def test_日本語版にある字はBIZ_UDゴシック(self):
        for ch in "亜骨角者Aあ":
            self.assertEqual(label_source(ch), "jp")

    def test_繁体字だけの字は台北黑體(self):
        for ch in "臺灣體龘ㄅˊ":
            self.assertEqual(label_source(ch), "tc")


class TestFont(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.path = Path(cls.tmp.name) / f"{PS_NAME}.otf"
        build_font(cls.path)
        cls.font = TTFont(cls.path)
        cls.chars = load_charset()

    @classmethod
    def tearDownClass(cls):
        cls.font.close()
        cls.tmp.cleanup()

    def test_全字がcmapにある(self):
        cmap = self.font.getBestCmap()
        missing = [ch for ch in self.chars if ord(ch) not in cmap]
        self.assertEqual(missing, [])
        self.assertEqual(len(cmap), len(self.chars) + 1)  # 空白の分

    def test_空白は字幅だけの空グリフ(self):
        name = self.font.getBestCmap()[0x20]
        self.assertEqual(self.font["hmtx"][name][0], UPM)
        self.assertEqual(self.font["CFF "].cff[0].CharStrings[name].calcBounds(None), None)

    def test_字幅はすべて正方形(self):
        cmap = self.font.getBestCmap()
        widths = {self.font["hmtx"][cmap[ord(ch)]][0] for ch in self.chars}
        self.assertEqual(widths, {UPM})

    def test_フォント名(self):
        name = self.font["name"]
        self.assertEqual(name.getDebugName(1), FAMILY)
        self.assertEqual(name.getDebugName(6), PS_NAME)
        # Source Han Sans の予約フォント名 "Source" は派生フォントの名前に使えない
        self.assertNotIn("Source", FAMILY)
        self.assertNotIn("Source", PS_NAME)

    def test_両方の元フォントの著作権表示とOFL(self):
        name = self.font["name"]
        copyright_ = name.getDebugName(0)
        for word in ("BIZ UDGothic", "Taipei Sans TC", "Source Han Sans"):
            self.assertIn(word, copyright_)
        self.assertNotIn("IPA", copyright_)
        self.assertIn("SIL Open Font License", name.getDebugName(13))

    def test_右下に字が描かれている(self):
        for ch in "亜臺":
            img = render_char(self.path, ch, 290)
            cell = 290 // 29
            top = (29 - 4 - 6) * cell
            patch = img.crop((top, top, (29 - 4) * cell, (29 - 4) * cell))
            self.assertLess(patch.getextrema()[0], 128, ch)

    def test_全グリフが読み取れて元の字に戻る(self):
        failed = [ch for ch in self.chars if decode_text(render_char(self.path, ch, 116)) != ch]
        self.assertEqual(failed, [])
