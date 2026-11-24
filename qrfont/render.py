"""作ったフォントで字を描き、QR として読めるか確かめる。"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from qrfont.qr import decode_image


def render_char(font_path, ch, px, margin=0):
    """font_path のフォントで字 ch を 1em = px 画素で描いたグレースケール画像。"""
    font = ImageFont.truetype(str(font_path), px)
    img = Image.new("L", (px + margin * 2, px + margin * 2), 255)
    ImageDraw.Draw(img).text((margin, margin + font.getmetrics()[0]), ch, font=font, fill=0, anchor="ls")
    return img


def decode_text(img):
    return decode_image(np.array(img))
