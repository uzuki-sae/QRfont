"""QR コードのフォント（OpenType/CFF）を作る。

1 マス = CELL 単位、1em = 29 マス。右下の白抜き部分には、元フォントの字形を縮めて描く。

- 日本語版 QR Font: 元フォントは BIZ UDゴシック
- 繁体字版 QR Font TC: 元フォントは台北黑體（Taipei Sans TC Beta、Source Han Sans の派生）

どちらの元フォントも SIL Open Font License 1.1 なので、作るフォントも同じライセンスになる。
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from qrfont.charset import load_charset, load_charset_tc
from qrfont.qr import SIZE, label_box, labeled_matrix

STYLE = "Regular"
VERSION = "0.2.0"

CELL = 40
UPM = CELL * SIZE  # 1160
ASCENT = 1000
DESCENT = ASCENT - UPM  # -160

# 白抜き部分のうち字の em が占める割合（周りの黒マスと字の線がくっつかないように少し空ける）
LABEL_SCALE = 0.9

SOURCE_DIR = Path(__file__).resolve().parent.parent / "source"

OFL = "SIL Open Font License, Version 1.1"
OFL_DESCRIPTION = (
    f"This Font Software is licensed under the {OFL}. "
    "This license is available with a FAQ at: https://openfontlicense.org"
)


@dataclass(frozen=True)
class Variant:
    family: str
    ps_name: str
    source: Path  # 右下の字形を借りる元フォント
    charset: Callable[[], list]
    copyright: str
    codepages: int  # OS/2 ulCodePageRange1


JP = Variant(
    family="QR Font",
    ps_name="QRFont-Regular",
    source=SOURCE_DIR / "BIZUDGothic-Regular.ttf",
    charset=load_charset,
    copyright=(
        "Copyright 2022 The BIZ UDGothic Project Authors "
        "(https://github.com/googlefonts/morisawa-biz-ud-gothic). "
        f"QR Font is a modified version of BIZ UDGothic, licensed under the {OFL}."
    ),
    codepages=(1 << 0) | (1 << 17),  # Latin 1, JIS/Japan
)

TC = Variant(
    family="QR Font TC",
    ps_name="QRFontTC-Regular",
    source=SOURCE_DIR / "TaipeiSansTCBeta-Regular.ttf",
    charset=load_charset_tc,
    copyright=(
        "Taipei Sans TC Beta by JT Foundry (bit.ly/jtfoundry) is a modified font of Source Han Sans. "
        "Source Han Sans: Copyright Adobe (http://www.adobe.com/), with Reserved Font Name 'Source'. "
        f"QR Font TC is a modified version of Taipei Sans TC Beta, licensed under the {OFL}."
    ),
    codepages=(1 << 0) | (1 << 20),  # Latin 1, Chinese: Traditional
)

VARIANTS = {"jp": JP, "tc": TC}


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


def build_font(out_path, variant=JP):
    source = _Source(variant.source)
    chars = variant.charset()
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

    family, ps_name = variant.family, variant.ps_name
    fb.setupCFF(ps_name, {"FullName": f"{family} {STYLE}"}, charstrings, {})
    fb.setupHorizontalMetrics({n: (UPM, 0) for n in names})
    fb.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT)
    fb.setupNameTable(
        {
            "copyright": variant.copyright,
            "familyName": family,
            "styleName": STYLE,
            "uniqueFontIdentifier": f"{ps_name};{VERSION}",
            "fullName": f"{family} {STYLE}",
            "psName": ps_name,
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
        ulCodePageRange1=variant.codepages,
    )
    fb.setupPost()
    fb.save(str(out_path))
