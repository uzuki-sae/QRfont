"""フォントに入れる字の一覧。"""

from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

# 常用漢字表の通用字体（𠮟・塡・剝・頰）に対して、情報機器で広く使われている字体
TOLERATED = "叱填剥頬"


def load_joyo():
    """常用漢字表（平成22年内閣告示第2号）の 2,136 字を表の順に返す。"""
    return (DATA / "joyo.txt").read_text(encoding="utf-8").split()


def load_jis_level1():
    """JIS X 0208 の第一水準漢字（16区〜47区）を区点順に返す。"""
    chars = []
    for row in range(16, 48):
        for cell in range(1, 95):
            try:
                chars.append(bytes([0xA0 + row, 0xA0 + cell]).decode("euc_jp"))
            except UnicodeDecodeError:
                pass
    return chars


def _range(first, last):
    return [chr(c) for c in range(ord(first), ord(last) + 1)]


def load_charset_jp():
    """日本語の字の一覧（空白を除く）。ASCII・かな・漢字の順。"""
    ascii_chars = [chr(c) for c in range(0x21, 0x7F)]
    hiragana = _range("ぁ", "ゖ") + ["ゝ", "ゞ"]
    katakana = _range("ァ", "ヺ") + ["・", "ー", "ヽ", "ヾ"]
    kanji = sorted(set(load_joyo()) | set(load_jis_level1()) | set(TOLERATED))
    return ascii_chars + hiragana + katakana + kanji


# 注音符號（ㄅ〜ㄩ）と声調記号（˙ˉˊˇˋ）
BOPOMOFO = "".join(chr(c) for c in range(0x3105, 0x312A)) + "˙ˉˊˇˋ"


def load_big5_hanzi():
    """Big5 の漢字（常用字 A440〜C67E と次常用字 C940〜F9D5、計 13,051 字）を符号順に返す。

    Python の big5 には C6A1 以降に ETEN のかな・記号も入っているので、CJK 統合漢字だけを取る。
    """
    chars = []
    for lead in range(0xA4, 0xFA):
        for trail in list(range(0x40, 0x7F)) + list(range(0xA1, 0xFF)):
            try:
                ch = bytes([lead, trail]).decode("big5")
            except UnicodeDecodeError:
                continue
            if "一" <= ch <= "鿿":
                chars.append(ch)
    return chars


def load_charset_tc():
    """繁体字の字の一覧（空白を除く）。ASCII・注音符號・漢字の順。"""
    ascii_chars = [chr(c) for c in range(0x21, 0x7F)]
    return ascii_chars + list(BOPOMOFO) + load_big5_hanzi()


def load_charset():
    """QR にする字の一覧（空白を除く）。日本語の字のあとに、繁体字だけにある字を並べる。"""
    jp = load_charset_jp()
    seen = set(jp)
    return jp + [ch for ch in load_charset_tc() if ch not in seen]
