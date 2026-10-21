# -*- coding: utf-8 -*-
"""
图片压缩：PNG → WebP

【为什么】
原图 760KB - 1424KB，首屏加起来 3.6MB。
WebP 通常比 PNG 小 60-80%，首屏能压到 500KB 以内。

【怎么做】
1. 转 WebP（质量 82，肉眼几乎无差）
2. 保留原 PNG（作为 fallback / 设计源文件）
3. 改数据库 cover 字段和 HTML 引用
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMAGES = ROOT / "frontend" / "images"

try:
    from PIL import Image
except ImportError:
    print("需要 Pillow：pip install Pillow")
    sys.exit(1)

print("=" * 70)
print("  图片压缩 PNG → WebP")
print("=" * 70)
print()

total_before = 0
total_after = 0
converted = []

for png in sorted(IMAGES.glob("*.png")):
    webp = png.with_suffix(".webp")

    before_kb = png.stat().st_size / 1024
    total_before += before_kb

    # 已经转过就跳过
    if webp.exists() and webp.stat().st_mtime > png.stat().st_mtime:
        after_kb = webp.stat().st_size / 1024
        total_after += after_kb
        print(f"  - {png.name:<28} 已有 webp  {after_kb:>7.0f} KB")
        converted.append((png.name, after_kb))
        continue

    try:
        with Image.open(png) as im:
            # 转 RGB（WebP 不支持某些 PNG 模式）
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGBA")
            else:
                im = im.convert("RGB")

            # 限制最大边长 1600（够用，再大是浪费）
            max_side = 1600
            if max(im.size) > max_side:
                ratio = max_side / max(im.size)
                new_size = (int(im.size[0] * ratio), int(im.size[1] * ratio))
                im = im.resize(new_size, Image.LANCZOS)

            im.save(webp, "WEBP", quality=82, method=6)

        after_kb = webp.stat().st_size / 1024
        total_after += after_kb
        pct = (1 - after_kb / before_kb) * 100

        print(f"  ✓ {png.name:<28} {before_kb:>7.0f} KB → {after_kb:>6.0f} KB  (-{pct:.0f}%)")
        converted.append((png.name, after_kb))

    except Exception as e:
        print(f"  ✗ {png.name}: {e}")
        total_after += before_kb

print()
print(f"  合计：{total_before:.0f} KB → {total_after:.0f} KB")
print(f"  节省：{total_before - total_after:.0f} KB（{(1-total_after/total_before)*100:.0f}%）")


# ══════════════════════════════════════════════════════════
# 改 HTML 引用
# ══════════════════════════════════════════════════════════
print()
print("=" * 70)
print("  更新 HTML 引用")
print("=" * 70)
print()

FE = ROOT / "frontend"
n_files = 0

for f in sorted(FE.glob("*.html")):
    c = f.read_text(encoding="utf-8")
    original = c

    # /images/xxx.png → /images/xxx.webp
    import re
    c = re.sub(r'(/images/[a-z0-9_]+)\.png', r"\1.webp", c)

    if c != original:
        f.write_text(c, encoding="utf-8")
        n_files += 1

print(f"  ✓ {n_files} 个页面已改引用")

# ══════════════════════════════════════════════════════════
# 改数据库 cover
# ══════════════════════════════════════════════════════════
print()
print("=" * 70)
print("  更新数据库 cover 字段")
print("=" * 70)
print()

os.system(
    'set PGPASSWORD=770101&& '
    '"D:\\PostgreSQL\\bin\\psql.exe" -U postgres -d tiaowulan -c '
    '"UPDATE products SET cover = REPLACE(cover, \'.png\', \'.webp\') WHERE cover LIKE \'%.png\';"'
)
os.system(
    'set PGPASSWORD=770101&& '
    '"D:\\PostgreSQL\\bin\\psql.exe" -U postgres -d tiaowulan -c '
    '"UPDATE articles SET cover = REPLACE(cover, \'.png\', \'.webp\') WHERE cover LIKE \'%.png\';"'
)

# ══════════════════════════════════════════════════════════
# 改 SSR 渲染里的图标引用
# ══════════════════════════════════════════════════════════
print()
print("=" * 70)
print("  检查 SSR 渲染代码")
print("=" * 70)
print()

render_py = ROOT / "backend" / "app" / "web" / "render.py"
c = render_py.read_text(encoding="utf-8")

if ".png" in c and "/images/" in c:
    import re
    c2 = re.sub(r'(/images/[a-z0-9_]+)\.png', r"\1.webp", c)
    if c2 != c:
        render_py.write_text(c2, encoding="utf-8")
        print("  ✓ render.py 已更新")
    else:
        print("  - render.py 无需改")
else:
    print("  - render.py 没有硬编码图片路径")
