# -*- coding: utf-8 -*-
"""修复文档移动后的相对链接"""

import os
import re

ROOT = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰"
DOCS = os.path.join(ROOT, "docs")

# 前端页面列表（用来识别需要改路径的链接）
PAGES = [
    "index", "shop", "product", "cart", "checkout", "pay", "order-success",
    "orders", "order-detail", "login", "address", "after-sale",
    "flower-language", "flower-language-detail", "about", "contact", "search",
    "help-delivery", "help-returns", "help-faq", "admin",
]

# 从 docs/04-原型/ 到 prototype/luxe/ 的相对路径
PROTO_PREFIX = "../../prototype/luxe/"


def fix_links(html_path, prefix):
    """把 href="xxx.html" 改成 href="prefix/xxx.html"（只改页面链接，不改外链）"""
    with open(html_path, encoding="utf-8") as f:
        html = f.read()

    original = html

    for p in PAGES:
        # 匹配 href="index.html" 或 href="index.html?a=b"
        # 不匹配已经带路径的（含 /）
        pattern = re.compile(
            r'href="(' + re.escape(p) + r'\.html(?:[?#][^"]*)?)"'
        )
        html = pattern.sub(lambda m: f'href="{prefix}{m.group(1)}"', html)

    if html != original:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        return True
    return False


print("=== 修复链接 ===\n")

# 04-原型 下的文件
proto_dir = os.path.join(DOCS, "04-原型")
for fn in os.listdir(proto_dir):
    if not fn.endswith(".html"):
        continue
    path = os.path.join(proto_dir, fn)
    if fix_links(path, PROTO_PREFIX):
        print(f"  ✓ {fn} 链接已改指向 {PROTO_PREFIX}")
    else:
        print(f"  - {fn} 无页面链接")

# 03-交付 下的文件（如果有页面链接）
deliver_dir = os.path.join(DOCS, "03-交付")
for fn in os.listdir(deliver_dir):
    if not fn.endswith(".html"):
        continue
    path = os.path.join(deliver_dir, fn)
    if fix_links(path, "../../prototype/luxe/"):
        print(f"  ✓ {fn} 链接已改")

print("\n完成")
