"""大きさ別の見本画像 docs/sample.png を作る。  python scripts/render_sample.py"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from qrfont.font import PS_NAME, SOURCE_FONT  # noqa: E402

FONT = ROOT / "fonts" / f"{PS_NAME}.otf"
TEXT = "亜鬱曖驚あアA&"
SIZES = [58, 72, 87, 116]

label = ImageFont.truetype(str(SOURCE_FONT), 18)
width = 130 + len(TEXT) * (max(SIZES) + 8)
height = sum(s + 40 for s in SIZES) + 20
img = Image.new("L", (width, height), 255)
draw = ImageDraw.Draw(img)
y = 10
for size in SIZES:
    font = ImageFont.truetype(str(FONT), size)
    draw.text((10, y + size // 2), f"{size}px", font=label, fill=0, anchor="lm")
    x = 130
    for ch in TEXT:
        draw.text((x, y), ch, font=font, fill=0, anchor="la")
        x += size + 8
    y += size + 40
out = ROOT / "docs" / "sample.png"
out.parent.mkdir(exist_ok=True)
img.save(out)
print(out)
