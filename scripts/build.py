"""フォントを fonts/ に書き出す。

    python scripts/build.py          # 日本語版と繁体字版の両方
    python scripts/build.py tc       # 繁体字版だけ（jp / tc）
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from qrfont.font import VARIANTS, build_font  # noqa: E402

keys = sys.argv[1:] or list(VARIANTS)
(ROOT / "fonts").mkdir(exist_ok=True)
for key in keys:
    variant = VARIANTS[key]
    out = ROOT / "fonts" / f"{variant.ps_name}.otf"
    build_font(out, variant)
    print(out)
