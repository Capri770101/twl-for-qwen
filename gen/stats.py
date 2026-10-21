# -*- coding: utf-8 -*-
"""统计前端页面现状"""
import os, glob

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"

pages = []
for p in sorted(glob.glob(os.path.join(PROTO, "*.html"))):
    fn = os.path.basename(p)
    if fn.startswith("_"):
        continue
    h = open(p, encoding="utf-8").read()
    size = os.path.getsize(p) / 1024
    lines = h.count("\n")
    pages.append({
        "name": fn,
        "kb": round(size),
        "lines": lines,
        "header": "site-header" in h or "hd-nav" in h,
        "footer": "site-footer" in h or "ft-row" in h,
        "img": "data:image" in h,
        "media": "@media" in h,
    })

print(f"总页面数: {len(pages)}")
print(f"总大小: {sum(p['kb'] for p in pages)} KB")
print(f"总行数: {sum(p['lines'] for p in pages)}")
print()
print(f"{'页面':34} {'大小':>7} {'行数':>6}  页眉 页脚 图片 响应")
print("-" * 70)
for p in pages:
    flags = [
        " ✓ " if p["header"] else " - ",
        " ✓ " if p["footer"] else " - ",
        " ✓ " if p["img"] else " - ",
        " ✓ " if p["media"] else " - ",
    ]
    print(f"{p['name']:34} {p['kb']:>5}KB {p['lines']:>6}  {''.join(flags)}")
