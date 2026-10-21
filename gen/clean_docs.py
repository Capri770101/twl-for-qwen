# -*- coding: utf-8 -*-
"""清理中间态 / 测试态文档，只留有效文档"""

import os
import shutil

DOCS = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\docs"

# 要删的（相对 docs 的路径）
TO_DELETE = [
    # 过程记录（整改已完成，内容已并入项目状态总结）
    "03-交付/生产级整改汇总.html",

    # 测试态文档（测试命令已并入项目状态总结）
    "03-交付/项目测试手册.html",

    # 过时的方案说明（说 16 个待对齐，实际已完成）
    "04-原型/前端方案总结.html",

    # 旧版本索引
    "04-原型/旧索引.html",

    # 已废弃的千问方案
    "99-归档/整体规划-千问接入与H5重构.md",
    "99-归档/需求确认清单-接千问与H5.md",
    "99-归档/接千问需要什么.md",
    "99-归档/建议-千问先行-给老板.md",
]

print("=== 删除中间态文档 ===\n")

for rel in TO_DELETE:
    path = os.path.join(DOCS, rel)
    if os.path.exists(path):
        size = round(os.path.getsize(path) / 1024)
        os.remove(path)
        print(f"  ✗ {rel:<42} {size}KB")
    else:
        print(f"  - {rel:<42} 不存在")

# 删空的 99-归档 目录
archive = os.path.join(DOCS, "99-归档")
if os.path.exists(archive) and not os.listdir(archive):
    os.rmdir(archive)
    print("\n  ✗ 删除空目录 99-归档/")

print("\n=== 保留的文档 ===\n")

total_kb = 0
for root, dirs, files in os.walk(DOCS):
    dirs.sort()
    for f in sorted(files):
        if not f.endswith((".md", ".html")):
            continue
        path = os.path.join(root, f)
        rel = os.path.relpath(path, DOCS)
        kb = round(os.path.getsize(path) / 1024)
        total_kb += kb
        print(f"  ✓ {rel:<42} {kb}KB")

print(f"\n共保留 {total_kb} KB")
