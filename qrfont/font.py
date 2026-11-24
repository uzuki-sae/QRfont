"""QR コードのフォント（OpenType/CFF）を作る。

1 マス = CELL 単位、1em = 29 マス。右下の白抜き部分には、
IPAexゴシックの字形を縮めて描く（このためフォント全体が IPA フォントライセンスの派生プログラムになる）。
"""

import os
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from qrfont.charset import load_charset
from qrfont.qr import SIZE, label_box, labeled_matrix

FAMILY = "QR Font"
STYLE = "Regular"
PS_NAME = "QRFont-Regular"
VERSION = "0.1.0"

CELL = 40
UPM = CELL * SIZE  # 1160
ASCENT = 1000
DESCENT = ASCENT - UPM  # -160

# 白抜き部分のうち字の em が占める割合（周りの黒マスと字の線がくっつかないように少し空ける）
LABEL_SCALE = 0.9

# IPAexゴシック Ver.004.01（ipaexg00401.zip の ipaexg.ttf）を置く。環境変数 QRFONT_SOURCE で上書きできる
SOURCE_FONT = Path(
    os.environ.get("QRFONT_SOURCE", Path(__file__).resolve().parent.parent / "source" / "ipaexg.ttf")
)


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


def build_font(out_path, source_path=SOURCE_FONT):
    source = _Source(source_path)
    chars = load_charset()
    missing = [ch for ch in chars if not source.has(ch)]
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
        charstrings[glyph_name(ch)] = build_glyph(ch, source)

    fb.setupCFF(PS_NAME, {"FullName": f"{FAMILY} {STYLE}"}, charstrings, {})
    fb.setupHorizontalMetrics({n: (UPM, 0) for n in names})
    fb.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT)
    fb.setupNameTable(
        {
            "copyright": (
                "Copyright(c) Information-technology Promotion Agency, Japan (IPA), 2003-2012. "
                "This font is a Derived Program of IPAex Gothic and is distributed under "
                "the IPA Font License Agreement v1.0."
            ),
            "familyName": FAMILY,
            "styleName": STYLE,
            "uniqueFontIdentifier": f"{PS_NAME};{VERSION}",
            "fullName": f"{FAMILY} {STYLE}",
            "psName": PS_NAME,
            "version": f"Version {VERSION}",
            "licenseDescription": "IPA Font License Agreement v1.0",
            "licenseInfoURL": "https://moji.or.jp/ipafont/license/",
        }
    )
    fb.setupOS2(
        sTypoAscender=ASCENT,
        sTypoDescender=DESCENT,
        sTypoLineGap=0,
        usWinAscent=ASCENT,
        usWinDescent=-DESCENT,
        fsType=0,
        ulCodePageRange1=(1 << 0) | (1 << 17),  # Latin 1, JIS/Japan
    )
    fb.setupPost()
    fb.save(str(out_path))
