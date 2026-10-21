# -*- coding: utf-8 -*-
"""
去掉 Google Fonts 外链，改用系统字体

【为什么】
Google Fonts 要 2 个外部请求（CSS 92KB + woff2 103KB），
而且在国内访问不稳定，是 LCP 慢的主要原因之一。

【换成什么】
- Logo 的中文衬线：系统字体 Songti SC / SimSun / STSong
- 英文装饰字：Georgia（系统自带）
- 正文：system-ui（零加载）

【视觉影响】
系统宋体和 Noto Serif SC 有差异，但都在「细衬线」这个大类里。
省掉 200KB 和 2 个外部请求，值得。
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE = ROOT / "frontend"

print("=" * 70)
print("  字体优化：去掉 Google Fonts")
print("=" * 70)
print()

# ══════════════════════════════════════════════════════════
# 1. 删掉 Google Fonts 的 link 和 preconnect
# ══════════════════════════════════════════════════════════
n_link = 0
for f in sorted(FE.glob("*.html")):
    c = f.read_text(encoding="utf-8")
    original = c

    # preconnect
    c = re.sub(
        r'<link rel="preconnect" href="https://fonts\.googleapis\.com"[^>]*>\s*',
        "",
        c,
    )
    c = re.sub(
        r'<link rel="preconnect" href="https://fonts\.gstatic\.com"[^>]*>\s*',
        "",
        c,
    )

    # 字体 CSS
    c = re.sub(
        r'<link href="https://fonts\.googleapis\.com/css2\?[^"]*" rel="stylesheet">\s*',
        "",
        c,
    )
    c = re.sub(
        r'<link rel="stylesheet" href="https://fonts\.googleapis\.com/css2\?[^"]*">\s*',
        "",
        c,
    )

    if c != original:
        f.write_text(c, encoding="utf-8")
        n_link += 1

print(f"  删除 Google Fonts 引用：{n_link} 个页面")


# ══════════════════════════════════════════════════════════
# 2. 字体栈替换
# ══════════════════════════════════════════════════════════
print()
print("  替换字体栈：")

# 中文字体栈（Logo 用）
CN_SERIF = "'Songti SC','STSong','SimSun','Noto Serif CJK SC',serif"

# 英文衬线（装饰用）
EN_SERIF = "Georgia,'Times New Roman',serif"

# 系统无衬线（正文）
SANS = (
    "-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB',"
    "'Microsoft YaHei',system-ui,sans-serif"
)

REPLACEMENTS = [
    # Logo 的中文衬线
    (r"'Noto Serif SC',\s*serif", CN_SERIF),
    (r'"Noto Serif SC",\s*serif', CN_SERIF),
    (r"'Noto Serif SC'", CN_SERIF),
    (r'"Noto Serif SC"', CN_SERIF),

    # 英文装饰字
    (r"'Cormorant Garamond',\s*serif", EN_SERIF),
    (r'"Cormorant Garamond",\s*serif', EN_SERIF),
    (r"'Cormorant Garamond'", EN_SERIF),
    (r'"Cormorant Garamond"', EN_SERIF),

    # Inter（正文西文）
    (r"'Inter',\s*-apple-system", SANS),
    (r'"Inter",\s*-apple-system', SANS),
    (r"'Inter'", "system-ui"),
    (r'"Inter"', "system-ui"),
]

n_font = 0
for f in sorted(FE.glob("*.html")):
    c = f.read_text(encoding="utf-8")
    original = c

    for pat, rep in REPLACEMENTS:
        c = re.sub(pat, rep, c)

    if c != original:
        f.write_text(c, encoding="utf-8")
        n_font += 1

print(f"    {n_font} 个页面已替换")


# ══════════════════════════════════════════════════════════
# 3. 验证
# ══════════════════════════════════════════════════════════
print()
print("  验证：")

left = []
for f in sorted(FE.glob("*.html")):
    c = f.read_text(encoding="utf-8")
    if "fonts.googleapis" in c or "fonts.gstatic" in c:
        left.append(f.name)

if left:
    print(f"    ✗ 还有 {len(left)} 个页面引用 Google Fonts: {left[:5]}")
else:
    print("    ✓ 所有页面已无 Google Fonts")

# 检查字体栈
has_cn = 0
has_sans = 0
for f in sorted(FE.glob("*.html")):
    c = f.read_text(encoding="utf-8")
    if "Songti SC" in c or "SimSun" in c:
        has_cn += 1
    if "system-ui" in c or "PingFang" in c:
        has_sans += 1

print(f"    ✓ {has_cn} 个页面用系统中文衬线")
print(f"    ✓ {has_sans} 个页面用系统无衬线")

print()
print("=" * 70)
