"""大きさ別の見本画像 docs/sample.png（日本語版）と docs/sample-tc.png（繁体字版）を作る。

    python scripts/render_sample.py
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from qrfont.font import JP, TC  # noqa: E402

SIZES = [58, 72, 87, 116]
SAMPLES = [
    (JP, "亜鬱曖驚あアA&", "sample.png"),
    (TC, "臺灣體鬱龘ㄅA&", "sample-tc.png"),
]

label = ImageFont.truetype(str(JP.source), 18)
for variant, text, filename in SAMPLES:
    font_path = ROOT / "fonts" / f"{variant.ps_name}.otf"
    width = 130 + len(text) * (max(SIZES) + 8)
    height = sum(s + 40 for s in SIZES) + 20
    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)
    y = 10
    for size in SIZES:
        font = ImageFont.truetype(str(font_path), size)
        draw.text((10, y + size // 2), f"{size}px", font=label, fill=0, anchor="lm")
        x = 130
        for ch in text:
            draw.text((x, y), ch, font=font, fill=0, anchor="la")
            x += size + 8
        y += size + 40
    out = ROOT / "docs" / filename
    out.parent.mkdir(exist_ok=True)
    img.save(out)
    print(out)
