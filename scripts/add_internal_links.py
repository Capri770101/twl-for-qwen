# -*- coding: utf-8 -*-
"""
给内容文章加内链

【为什么需要】
SEO 要求内容之间有链接关系，形成闭环。
没有内链 = 孤岛页面，搜索引擎给的分很低。

【怎么加】
在每篇文章末尾加一个「你可能还想知道」区块，
链接到相关文章和列表页。

【为什么不放在正文里】
正文里的链接需要上下文自然，硬插会读起来别扭。
末尾的「延伸阅读」是标准做法，读者也习惯。
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"

# ══════════════════════════════════════════════════════════
# 每篇文章链接到谁
# ══════════════════════════════════════════════════════════
LINKS = {
    "花语/white-rose.md": [
        ("香槟玫瑰的花语是什么？适合送什么人", "/flower-language-detail.html?slug=champagne-rose"),
        ("送妈妈什么花合适？6 种花和它们的意思", "/flower-language-detail.html?slug=gift-for-mom"),
        ("全部花语百科", "/flower-language.html"),
    ],
    "花语/champagne-rose.md": [
        ("白玫瑰的花语是什么？和红玫瑰有什么区别", "/flower-language-detail.html?slug=white-rose"),
        ("玫瑰怎么养能开更久？7 个具体做法", "/flower-language-detail.html?slug=rose-care"),
        ("全部花语百科", "/flower-language.html"),
    ],
    "花语/sunflower.md": [
        ("送妈妈什么花合适？6 种花和它们的意思", "/flower-language-detail.html?slug=gift-for-mom"),
        ("玫瑰怎么养能开更久？7 个具体做法", "/flower-language-detail.html?slug=rose-care"),
        ("全部花语百科", "/flower-language.html"),
    ],
    "场景/gift-for-mom.md": [
        ("白玫瑰的花语是什么？和红玫瑰有什么区别", "/flower-language-detail.html?slug=white-rose"),
        ("香槟玫瑰的花语是什么？适合送什么人", "/flower-language-detail.html?slug=champagne-rose"),
        ("向日葵的花语是什么？适合送什么人", "/flower-language-detail.html?slug=sunflower"),
        ("全部花束", "/shop.html"),
    ],
    "养护/rose-care.md": [
        ("白玫瑰的花语是什么？和红玫瑰有什么区别", "/flower-language-detail.html?slug=white-rose"),
        ("香槟玫瑰的花语是什么？适合送什么人", "/flower-language-detail.html?slug=champagne-rose"),
        ("全部花束", "/shop.html"),
    ],
}

MARKER = "## 你可能还想知道"


print("=" * 66)
print("  给文章加内链")
print("=" * 66)
print()

for rel, links in LINKS.items():
    p = CONTENT / rel
    if not p.exists():
        print(f"  ✗ {rel} 不存在")
        continue

    text = p.read_text(encoding="utf-8")

    # 先删掉旧的「你可能还想知道」区块
    text = re.sub(
        r"\n## 你可能还想知道\n.*$",
        "",
        text,
        flags=re.DOTALL,
    )

    # 追加新区块
    block = f"\n{MARKER}\n\n"
    for title, url in links:
        block += f"- [{title}]({url})\n"

    text = text.rstrip() + "\n" + block

    p.write_text(text, encoding="utf-8")
    print(f"  ✓ {rel}（{len(links)} 个内链）")

print()
print("=" * 66)
