"""QR コードのフォント（OpenType/CFF）を作る。

1 マス = CELL 単位、1em = 29 マス。右下の白抜き部分には、元フォントの字形を縮めて描く。

- 日本語の字（常用漢字・JIS 第一水準・かな・ASCII）: BIZ UDゴシック
- 繁体字だけにある字（Big5 漢字・注音符號）: 台北黑體（Taipei Sans TC Beta、Source Han Sans の派生）

どちらの元フォントも SIL Open Font License 1.1 なので、作るフォントも同じライセンスになる。
"""

from functools import cache
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from qrfont.charset import load_charset, load_charset_jp
from qrfont.qr import SIZE, label_box, labeled_matrix

FAMILY = "QR Font"
STYLE = "Regular"
PS_NAME = "QRFont-Regular"
VERSION = "0.2.0"

CELL = 40
UPM = CELL * SIZE  # 1160
ASCENT = 1000
DESCENT = ASCENT - UPM  # -160

# 白抜き部分のうち字の em が占める割合（周りの黒マスと字の線がくっつかないように少し空ける）
LABEL_SCALE = 0.9

SOURCE_DIR = Path(__file__).resolve().parent.parent / "source"
SOURCES = {
    "jp": SOURCE_DIR / "BIZUDGothic-Regular.ttf",
    "tc": SOURCE_DIR / "TaipeiSansTCBeta-Regular.ttf",
}

OFL = "SIL Open Font License, Version 1.1"
COPYRIGHT = (
    "Copyright 2022 The BIZ UDGothic Project Authors "
    "(https://github.com/googlefonts/morisawa-biz-ud-gothic). "
    "Taipei Sans TC Beta by JT Foundry (bit.ly/jtfoundry) is a modified font of Source Han Sans. "
    "Source Han Sans: Copyright Adobe (http://www.adobe.com/), with Reserved Font Name 'Source'. "
    f"QR Font is a modified version of BIZ UDGothic and Taipei Sans TC Beta, licensed under the {OFL}."
)
OFL_DESCRIPTION = (
    f"This Font Software is licensed under the {OFL}. "
    "This license is available with a FAQ at: https://openfontlicense.org"
)


@cache
def _jp_chars():
    return frozenset(load_charset_jp())


def label_source(ch):
    """字 ch の右下の字形をどちらの元フォントから取るか。日本語の字は "jp"、それ以外は "tc"。"""
    return "jp" if ch in _jp_chars() else "tc"


def glyph_name(ch):
    code = ord(ch)
    return f"uni{code:04X}" if code <= 0xFFFF else f"u{code:05X}"


def _cell_y(row):
    """row 行目のマスの下端の y 座標。"""
    return ASCENT - (row + 1) * CELL


def _draw_modules(pen, matrix):
    """黒マスを、横に続く分をまとめた長方形で描く（輪郭が重ならないように）。"""
    for i, row in enumerate(matrix):
        j = 0
        while j < len(row):
            if not row[j]:
                j += 1
                continue
            start = j
            while j < len(row) and row[j]:
                j += 1
            x0, x1 = start * CELL, j * CELL
            y0 = _cell_y(i)
            y1 = y0 + CELL
            pen.moveTo((x0, y0))
            pen.lineTo((x0, y1))
            pen.lineTo((x1, y1))
            pen.lineTo((x1, y0))
            pen.closePath()


class _Source:
    def __init__(self, path):
        self.font = TTFont(path)
        self.cmap = self.font.getBestCmap()
        self.glyphs = self.font.getGlyphSet()
        self.upm = self.font["head"].unitsPerEm
        self.descender = self.font["OS/2"].sTypoDescender
        self.hmtx = self.font["hmtx"]

    def has(self, ch):
        return ord(ch) in self.cmap

    def draw(self, pen, ch):
        """字 ch を白抜き部分の中央に描く。"""
        name = self.cmap[ord(ch)]
        top, left, size = label_box()
        box = size * CELL
        em = box * LABEL_SCALE
        scale = em / self.upm
        advance = self.hmtx[name][0] * scale
        x = left * CELL + (box - advance) / 2
        y = _cell_y(top + size - 1) + (box - em) / 2 - self.descender * scale
        self.glyphs[name].draw(TransformPen(pen, (scale, 0, 0, scale, x, y)))


def build_glyph(ch, source):
    pen = T2CharStringPen(UPM, None)
    _draw_modules(pen, labeled_matrix(ch))
    source.draw(pen, ch)
    return pen.getCharString()


def build_font(out_path):
    sources = {key: _Source(path) for key, path in SOURCES.items()}
    chars = load_charset()
    missing = [ch for ch in chars if not sources[label_source(ch)].has(ch)]
    if missing:
        raise ValueError(f"元フォントに無い字: {''.join(missing)}")

    names = [".notdef", "space"] + [glyph_name(ch) for ch in chars]
    fb = FontBuilder(UPM, isTTF=False)
    fb.setupGlyphOrder(names)
    cmap = {0x20: "space"}
    cmap.update({ord(ch): glyph_name(ch) for ch in chars})
    fb.setupCharacterMap(cmap)

    empty = T2CharStringPen(UPM, None).getCharString()
    charstrings = {".notdef": empty, "space": T2CharStringPen(UPM, None).getCharString()}
    for ch in chars:
        charstrings[glyph_name(ch)] = build_glyph(ch, sources[label_source(ch)])

    fb.setupCFF(PS_NAME, {"FullName": f"{FAMILY} {STYLE}"}, charstrings, {})
    fb.setupHorizontalMetrics({n: (UPM, 0) for n in names})
    fb.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT)
    fb.setupNameTable(
        {
            "copyright": COPYRIGHT,
            "familyName": FAMILY,
            "styleName": STYLE,
            "uniqueFontIdentifier": f"{PS_NAME};{VERSION}",
            "fullName": f"{FAMILY} {STYLE}",
            "psName": PS_NAME,
            "version": f"Version {VERSION}",
            "licenseDescription": OFL_DESCRIPTION,
            "licenseInfoURL": "https://openfontlicense.org",
        }
    )
    fb.setupOS2(
        sTypoAscender=ASCENT,
        sTypoDescender=DESCENT,
        sTypoLineGap=0,
        usWinAscent=ASCENT,
        usWinDescent=-DESCENT,
        fsType=0,
        ulCodePageRange1=(1 << 0) | (1 << 17) | (1 << 20),  # Latin 1, JIS/Japan, Chinese: Traditional
    )
    fb.setupPost()
    fb.save(str(out_path))
