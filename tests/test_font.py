import tempfile
import unittest
from pathlib import Path

from fontTools.ttLib import TTFont

from qrfont.font import JP, TC, UPM, build_font
from qrfont.render import decode_text, render_char


class _FontTests:
    """日本語版・繁体字版に共通のテスト。VARIANT を決めたサブクラスで動かす。"""

    VARIANT = None
    SAMPLE = None  # 右下に字が描かれているかを見る字

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.path = Path(cls.tmp.name) / f"{cls.VARIANT.ps_name}.otf"
        build_font(cls.path, cls.VARIANT)
        cls.font = TTFont(cls.path)
        cls.chars = cls.VARIANT.charset()

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

    def test_フォント名とライセンス(self):
        name = self.font["name"]
        self.assertEqual(name.getDebugName(1), self.VARIANT.family)
        self.assertEqual(name.getDebugName(6), self.VARIANT.ps_name)
        self.assertIn("SIL Open Font License", name.getDebugName(13))
        self.assertNotIn("IPA", name.getDebugName(0))

    def test_右下に字が描かれている(self):
        img = render_char(self.path, self.SAMPLE, 290)
        cell = 290 // 29
        top = (29 - 4 - 6) * cell
        patch = img.crop((top, top, (29 - 4) * cell, (29 - 4) * cell))
        self.assertLess(patch.getextrema()[0], 128)

    def test_全グリフが読み取れて元の字に戻る(self):
        failed = [ch for ch in self.chars if decode_text(render_char(self.path, ch, 116)) != ch]
        self.assertEqual(failed, [])


class TestFontJP(_FontTests, unittest.TestCase):
    VARIANT = JP
    SAMPLE = "亜"

    def test_日本語版の名前(self):
        self.assertEqual(JP.family, "QR Font")
        self.assertIn("BIZ UDGothic", self.font["name"].getDebugName(0))


class TestFontTC(_FontTests, unittest.TestCase):
    VARIANT = TC
    SAMPLE = "體"

    def test_繁体字版の名前(self):
        self.assertEqual(TC.family, "QR Font TC")
        copyright_ = self.font["name"].getDebugName(0)
        self.assertIn("Taipei Sans TC", copyright_)
        self.assertIn("Source Han Sans", copyright_)

    def test_繁体字版の名前に予約フォント名を使わない(self):
        # Source Han Sans の予約フォント名 "Source" は派生フォントの名前に使えない
        self.assertNotIn("Source", TC.family)
        self.assertNotIn("Source", TC.ps_name)
