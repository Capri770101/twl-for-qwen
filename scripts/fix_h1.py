# -*- coding: utf-8 -*-
"""修剩下的 h1 问题"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE = ROOT / "frontend"

print("=== 修 h1 ===\n")

# ────────────────────────────────────────────────────
# 1. index.html：Hero 的 h2 → h1
# ────────────────────────────────────────────────────
p = FE / "index.html"
c = p.read_text(encoding="utf-8")

# 找 hero 区块
m = re.search(r'(<section class="hero">.*?)(<h2>)(.*?)(</h2>)', c, re.DOTALL)
if m:
    old = m.group(0)
    new = old.replace("<h2>", "<h1>", 1).replace("</h2>", "</h1>", 1)
    c = c.replace(old, new, 1)

    # CSS 同步
    c = c.replace(".hero h2{", ".hero h1{")
    c = c.replace(".hero h2 {", ".hero h1 {")
    c = c.replace("@media (min-width:1024px){\n  .hero h2{", "@media (min-width:1024px){\n  .hero h1{")

    p.write_text(c, encoding="utf-8")
    print("  ✓ index.html: Hero h2 → h1")
else:
    print("  ⚠ index.html: 没匹配到 hero 的 h2")


# ────────────────────────────────────────────────────
# 2. admin.html：给页面标题加 h1
# ────────────────────────────────────────────────────
p = FE / "admin.html"
c = p.read_text(encoding="utf-8")

if "<h1" not in c:
    # 页头的 h2 → h1（第一个页面标题）
    old = '<div class="page-title">\n          <div>\n            <h2>数据看板</h2>'
    new = '<div class="page-title">\n          <div>\n            <h1>数据看板</h1>'

    if old in c:
        c = c.replace(old, new, 1)
        # 对应的闭合标签
        c = c.replace("<h2>数据看板</h2>", "<h1>数据看板</h1>", 1)
        # CSS
        c = c.replace(".page-title h2{", ".page-title h1{")
        c = c.replace(".page-title h2 {", ".page-title h1 {")
        p.write_text(c, encoding="utf-8")
        print("  ✓ admin.html: 页面标题 h2 → h1")
    else:
        # 宽松匹配
        c2 = re.sub(r'<h2>数据看板</h2>', '<h1>数据看板</h1>', c, count=1)
        if c2 != c:
            c2 = c2.replace(".page-title h2{", ".page-title h1{")
            p.write_text(c2, encoding="utf-8")
            print("  ✓ admin.html: 用正则修的")
        else:
            print("  ⚠ admin.html: 没找到数据看板标题")


# ────────────────────────────────────────────────────
# 3. 验证
# ────────────────────────────────────────────────────
print()
print("【验证 h1 数量】")
print()

ok = 0
for f in sorted(FE.glob("*.html")):
    c = f.read_text(encoding="utf-8")
    n = len(re.findall(r"<h1[\s>]", c))
    mark = "✓" if n == 1 else "✗"
    if n == 1:
        ok += 1
    print(f"  {mark} {f.name:<32} {n}")

print()
print(f"  {ok} / 21 个页面有且仅有 1 个 h1")
