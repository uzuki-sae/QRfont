"""フォントを fonts/ に書き出す。  python scripts/build.py"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from qrfont.font import PS_NAME, build_font  # noqa: E402

out = ROOT / "fonts" / f"{PS_NAME}.otf"
out.parent.mkdir(exist_ok=True)
build_font(out)
print(out)
