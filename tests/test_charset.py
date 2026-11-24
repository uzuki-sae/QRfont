import unittest

from qrfont.charset import (
    BOPOMOFO,
    load_big5_hanzi,
    load_charset,
    load_charset_jp,
    load_charset_tc,
    load_jis_level1,
    load_joyo,
)


class TestJoyo(unittest.TestCase):
    def test_常用漢字は2136字(self):
        joyo = load_joyo()
        self.assertEqual(len(joyo), 2136)
        self.assertEqual(len(set(joyo)), 2136)

    def test_表の最初と最後の字(self):
        joyo = load_joyo()
        self.assertEqual(joyo[0], "亜")
        self.assertEqual(joyo[-1], "腕")

    def test_通用字体のまま入っている(self):
        joyo = load_joyo()
        for ch in "𠮟塡剝頰":
            self.assertIn(ch, joyo)


class TestJisLevel1(unittest.TestCase):
    def test_第一水準は2965字(self):
        level1 = load_jis_level1()
        self.assertEqual(len(level1), 2965)
        self.assertEqual(len(set(level1)), 2965)

    def test_最初は亜で最後は腕(self):
        level1 = load_jis_level1()
        self.assertEqual(level1[0], "亜")
        self.assertEqual(level1[-1], "腕")

    def test_第二水準の字は入らない(self):
        level1 = load_jis_level1()
        for ch in "弌丐":
            self.assertNotIn(ch, level1)


class TestCharsetJP(unittest.TestCase):
    def setUp(self):
        self.chars = load_charset_jp()

    def test_重複がない(self):
        self.assertEqual(len(self.chars), len(set(self.chars)))

    def test_ASCII印字可能文字をすべて含む(self):
        for code in range(0x21, 0x7F):
            self.assertIn(chr(code), self.chars)

    def test_空白はQRにしない(self):
        self.assertNotIn(" ", self.chars)

    def test_ひらがなとカタカナ(self):
        for ch in "ぁあゔゕゖゝゞァアヴヵヶヷヺ・ーヽヾ":
            self.assertIn(ch, self.chars)

    def test_許容字体として普及している字も含む(self):
        for ch in "叱填剥頬":
            self.assertIn(ch, self.chars)

    def test_常用漢字と第一水準をすべて含む(self):
        for ch in load_joyo() + load_jis_level1():
            self.assertIn(ch, self.chars)


class TestBig5(unittest.TestCase):
    def test_Big5の漢字は13051字(self):
        hanzi = load_big5_hanzi()
        self.assertEqual(len(hanzi), 13051)
        self.assertEqual(len(set(hanzi)), 13051)

    def test_常用字と次常用字の両方を含む(self):
        hanzi = load_big5_hanzi()
        for ch in "一籲乂龘臺灣體":
            self.assertIn(ch, hanzi)

    def test_かななど漢字以外は入らない(self):
        hanzi = load_big5_hanzi()
        for ch in "ゝあ々":
            self.assertNotIn(ch, hanzi)


class TestCharsetTC(unittest.TestCase):
    def setUp(self):
        self.chars = load_charset_tc()

    def test_重複がない(self):
        self.assertEqual(len(self.chars), len(set(self.chars)))

    def test_ASCIIと注音符號とBig5漢字(self):
        expected = [chr(c) for c in range(0x21, 0x7F)] + list(BOPOMOFO) + load_big5_hanzi()
        self.assertEqual(sorted(self.chars), sorted(expected))

    def test_注音符號と声調記号(self):
        self.assertEqual(len(BOPOMOFO), 42)
        for ch in "ㄅㄩ˙ˉˊˇˋ":
            self.assertIn(ch, self.chars)

    def test_空白とかなは入らない(self):
        for ch in " あア":
            self.assertNotIn(ch, self.chars)


class TestCharsetMerged(unittest.TestCase):
    def setUp(self):
        self.chars = load_charset()

    def test_日本語の字と繁体字の字を合わせたもの(self):
        self.assertEqual(set(self.chars), set(load_charset_jp()) | set(load_charset_tc()))
        self.assertEqual(len(self.chars), 13824)

    def test_重複がない(self):
        self.assertEqual(len(self.chars), len(set(self.chars)))

    def test_日本語の字が先に並ぶ(self):
        jp = load_charset_jp()
        self.assertEqual(self.chars[: len(jp)], jp)
