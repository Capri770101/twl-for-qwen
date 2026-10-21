# -*- coding: utf-8 -*-
"""把 admin.html 的深色侧栏改成白底细边框"""
import os

F = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe\admin.html"

REPLACE = [
    # 侧栏主容器：深色 → 白底 + 右边框
    ("    background:var(--ink);\n    color:#fff;",
     "    background:#fff;\n    color:var(--ink);\n    border-right:1px solid var(--gray-d);"),

    # 品牌区分隔线
    ("border-bottom:1px solid rgba(255,255,255,.12);",
     "border-bottom:1px solid var(--gray-e);"),

    # 品牌名 / 英文名
    ("letter-spacing:.32em;text-indent:.32em;line-height:1;",
     "letter-spacing:.32em;text-indent:.32em;line-height:1;color:var(--ink);"),
    ("color:rgba(255,255,255,.42);",
     "color:var(--gray-a);"),

    # 分组标题
    ("color:rgba(255,255,255,.32);font-weight:400;",
     "color:var(--gray-a);font-weight:400;"),

    # 导航项
    ("color:rgba(255,255,255,.6);",
     "color:var(--gray-7);"),
    (".side-nav a:hover{color:#fff;background:rgba(255,255,255,.05)}",
     ".side-nav a:hover{color:var(--ink);background:var(--paper)}"),
    ("color:#fff;background:rgba(255,255,255,.08);\n    border-left-color:#fff;",
     "color:var(--ink);background:var(--paper);\n    border-left-color:var(--ink);"),

    # 徽章
    ("background:rgba(255,255,255,.16);border-radius:2px;",
     "background:var(--gray-e);color:var(--gray-7);border-radius:2px;"),

    # 底部
    ("border-top:1px solid rgba(255,255,255,.12);\n    font-size:9.5px;color:rgba(255,255,255,.35);line-height:2;",
     "border-top:1px solid var(--gray-e);\n    font-size:9.5px;color:var(--gray-a);line-height:2;"),
    (".side-foot a{color:rgba(255,255,255,.55)}",
     ".side-foot a{color:var(--gray-7)}"),
    (".side-foot a:hover{color:#fff}",
     ".side-foot a:hover{color:var(--ink)}"),

    # 滚动条
    (".sidebar::-webkit-scrollbar-thumb{background:rgba(255,255,255,.2)}",
     ".sidebar::-webkit-scrollbar-thumb{background:var(--gray-d)}"),

    # 头像
    ("background:var(--paper);color:var(--ink);",
     "background:var(--paper);color:var(--ink);"),
]

html = open(F, encoding="utf-8").read()
n = 0
for a, b in REPLACE:
    c = html.count(a)
    if c and a != b:
        html = html.replace(a, b)
        n += c
        print(f"  {c} 处: {a[:40]}...")

open(F, "w", encoding="utf-8").write(html)
print(f"\n共替换 {n} 处")

# 残留检查
print("\n=== 检查残留的白色文字 ===")
import re
leftovers = re.findall(r"rgba\(255,255,255,[\d.]+\)", html)
if leftovers:
    print(f"  还有 {len(leftovers)} 处: {set(leftovers)}")
else:
    print("  无残留")
