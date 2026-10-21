# -*- coding: utf-8 -*-
"""
SEO 细节修复
1. Logo 的 h1 → div.logo（h1 应该给页面主标题）
2. 首页 Hero 的 h2 → h1
3. 加 <main> 语义标签
4. 同步改 CSS 选择器
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"

print("=" * 70)
print("  SEO 细节修复")
print("=" * 70)
print()

html_files = sorted(FRONTEND.glob("*.html"))

fixed_logo = 0
fixed_css = 0
fixed_main = 0
fixed_hero = 0

for f in html_files:
    c = f.read_text(encoding="utf-8")
    original = c

    # ────────────────────────────────────────────────────
    # 1. Logo 的 h1 → div.logo
    # ────────────────────────────────────────────────────
    old_logo_patterns = [
        # 带 <a> 包裹的
        ('<a href="index.html"><h1>跳舞兰</h1><span class="en">Tiao Wu Lan</span></a>',
         '<a href="index.html"><div class="logo">跳舞兰</div><span class="en">Tiao Wu Lan</span></a>'),
        # 多行的
        ('<a href="index.html">\n      <h1>跳舞兰</h1>\n      <span class="en">Tiao Wu Lan</span>\n    </a>',
         '<a href="index.html">\n      <div class="logo">跳舞兰</div>\n      <span class="en">Tiao Wu Lan</span>\n    </a>'),
    ]

    for old, new in old_logo_patterns:
        if old in c:
            c = c.replace(old, new)
            fixed_logo += 1
            break
    else:
        # 宽松匹配：任何 <h1>跳舞兰</h1>
        if "<h1>跳舞兰</h1>" in c:
            c = c.replace("<h1>跳舞兰</h1>", '<div class="logo">跳舞兰</div>')
            fixed_logo += 1

    # ────────────────────────────────────────────────────
    # 2. CSS 选择器同步改
    # ────────────────────────────────────────────────────
    css_replacements = [
        (".hd-brand h1{", ".hd-brand .logo{"),
        (".hd-brand h1 {", ".hd-brand .logo {"),
        (".hd-brand h1,", ".hd-brand .logo,"),
        (".brand h1{", ".brand .logo{"),
        (".brand h1 {", ".brand .logo {"),
    ]

    for old, new in css_replacements:
        if old in c:
            c = c.replace(old, new)
            fixed_css += 1

    # ────────────────────────────────────────────────────
    # 3. 首页 Hero 的 h2 → h1
    #
    # 【为什么】
    # Logo 改成 div 后，首页没有 h1 了。
    # Hero 的主标题应该承担 h1 的角色。
    # ────────────────────────────────────────────────────
    if f.name == "index.html":
        # 找 .hero 里的 h2
        if '<div class="hero">' in c:
            # 在 hero 区块内把第一个 h2 改成 h1
            hero_start = c.find('<div class="hero">')
            hero_end = c.find("</section>", hero_start)
            if hero_end == -1:
                hero_end = c.find('<div class="story', hero_start)

            if hero_start > 0 and hero_end > hero_start:
                hero_block = c[hero_start:hero_end]
                if "<h2>" in hero_block:
                    new_hero = hero_block.replace("<h2>", "<h1>", 1)
                    new_hero = new_hero.replace("</h2>", "</h1>", 1)
                    c = c[:hero_start] + new_hero + c[hero_end:]
                    fixed_hero += 1

    # ────────────────────────────────────────────────────
    # 4. 加 <main> 语义标签
    #
    # 【怎么加】
    # 在 </header> 之后插入 <main>，在 <footer 之前插入 </main>
    # ────────────────────────────────────────────────────
    if "<main>" not in c:
        # 找 </header>
        header_end = c.find("</header>")
        if header_end > 0:
            # 找 footer 开始（可能是 <footer 或 <footer class=）
            footer_start = c.find("<footer", header_end)
            if footer_start > 0:
                # 插入 <main> 和 </main>
                c = c[:header_end + len("</header>")] + "\n\n<main>" + \
                    c[header_end + len("</header>"):footer_start] + \
                    "\n</main>\n\n" + c[footer_start:]
                fixed_main += 1

    if c != original:
        f.write_text(c, encoding="utf-8")

print(f"  Logo h1 → div:     {fixed_logo} 个文件")
print(f"  CSS 选择器同步:    {fixed_css} 处")
print(f"  首页 Hero h2 → h1: {fixed_hero} 个")
print(f"  加 <main> 标签:    {fixed_main} 个")
print()

# ══════════════════════════════════════════════════════════
# 验证
# ══════════════════════════════════════════════════════════
print("【验证：每个页面的 h1 数量】")
print()

for f in html_files:
    c = f.read_text(encoding="utf-8")
    h1_count = len(re.findall(r"<h1[\s>]", c))
    mark = "✓" if h1_count == 1 else "✗"
    print(f"  {mark} {f.name:<32} h1: {h1_count}")

print()
print("=" * 70)
