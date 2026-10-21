# -*- coding: utf-8 -*-
"""把 luxe 所有页面里的墨绿色改成纯黑白"""
import os, glob, re

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"

# 颜色替换表
REPLACE = [
    # 变量（base.css 里已删，页面里的引用要换）
    ("var(--green-soft)", "var(--paper)"),
    ("var(--green-mid)", "var(--gray-7)"),
    ("var(--green)", "var(--ink)"),
    # 硬编码色
    ("#2e3b30", "#141414"),
    ("#3d4f40", "#6e6a63"),
    ("#edf0eb", "#f6f4ef"),
    # 图片上的深绿渐变 → 黑色渐变
    ("rgba(20,30,22,.72)", "rgba(0,0,0,.62)"),
    ("rgba(20,30,22,.68)", "rgba(0,0,0,.58)"),
    ("rgba(20,30,22,.55)", "rgba(0,0,0,.5)"),
    # 暖黄色告警 → 灰色
    ("#8a6420", "#6e6a63"),
    ("#fdf8ee", "#f6f4ef"),
    ("#e0c9a0", "#dedad3"),
    ("#6b5220", "#6e6a63"),
    ("#8a7240", "#a39e95"),
    # 状态色 → 灰
    ("#a8c0d8", "#dedad3"),
    ("#345f80", "#141414"),
    ("#f0f6fa", "#f6f4ef"),
    ("#a8c4ae", "#dedad3"),
    ("#a04545", "#a39e95"),
    ("#8a3c3c", "#6e6a63"),
]

total = 0
for p in glob.glob(os.path.join(PROTO, "*.html")):
    fn = os.path.basename(p)
    html = open(p, encoding="utf-8").read()
    orig = html
    n = 0
    for a, b in REPLACE:
        c = html.count(a)
        if c:
            html = html.replace(a, b)
            n += c
    if n:
        open(p, "w", encoding="utf-8").write(html)
        print(f"  {fn}: {n} 处")
        total += n

print(f"\n总计 {total} 处替换")

# 检查残留
print("\n=== 残留检查 ===")
bad = 0
for p in glob.glob(os.path.join(PROTO, "*.html")) + [os.path.join(PROTO, "base.css")]:
    html = open(p, encoding="utf-8").read()
    for kw in ["var(--green", "#2e3b30", "#3d4f40", "#edf0eb"]:
        if kw in html:
            print(f"  {os.path.basename(p)}: 还有 {kw}")
            bad += 1
if bad == 0:
    print("  ✅ 无残留")
