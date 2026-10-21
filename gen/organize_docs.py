# -*- coding: utf-8 -*-
"""整理项目文档：全部归入 docs/ 目录"""

import os
import shutil

ROOT = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰"
DOCS = os.path.join(ROOT, "docs")

# 目录结构
DIRS = {
    "req": os.path.join(DOCS, "01-需求"),
    "tech": os.path.join(DOCS, "02-技术"),
    "deliver": os.path.join(DOCS, "03-交付"),
    "proto": os.path.join(DOCS, "04-原型"),
    "archive": os.path.join(DOCS, "99-归档"),
}

for d in DIRS.values():
    os.makedirs(d, exist_ok=True)

print("=== 目录已创建 ===\n")

# 文件移动映射：(源, 目标目录, 新文件名)
MOVES = [
    # 需求
    (os.path.join(ROOT, "任务书.md"), DIRS["req"], "任务书.md"),
    (os.path.join(ROOT, "前端协作协议.md"), DIRS["req"], "前端协作协议.md"),

    # 技术
    (os.path.join(ROOT, "工程书.md"), DIRS["tech"], "工程书.md"),
    (os.path.join(ROOT, "前端开发方案.md"), DIRS["tech"], "前端开发方案.md"),

    # 交付
    (os.path.join(ROOT, "项目状态总结.html"), DIRS["deliver"], "项目状态总结.html"),
    (os.path.join(ROOT, "生产级整改汇总.html"), DIRS["deliver"], "生产级整改汇总.html"),
    (os.path.join(ROOT, "项目测试手册.html"), DIRS["deliver"], "项目测试手册.html"),

    # 原型
    (os.path.join(ROOT, "prototype", "luxe", "_list.html"), DIRS["proto"], "页面清单.html"),
    (os.path.join(ROOT, "prototype", "luxe", "_summary.html"), DIRS["proto"], "前端方案总结.html"),
    (os.path.join(ROOT, "prototype", "luxe", "_index.html"), DIRS["proto"], "旧索引.html"),

    # 归档（千问相关的已废弃文档）
    (os.path.join(ROOT, "建议-千问先行-给老板.md"), DIRS["archive"], "建议-千问先行-给老板.md"),
    (os.path.join(ROOT, "接千问需要什么.md"), DIRS["archive"], "接千问需要什么.md"),
    (os.path.join(ROOT, "需求确认清单-接千问与H5.md"), DIRS["archive"], "需求确认清单-接千问与H5.md"),
    (os.path.join(ROOT, "整体规划-千问接入与H5重构.md"), DIRS["archive"], "整体规划-千问接入与H5重构.md"),

    # 上下文（放 docs 根）
    (os.path.join(ROOT, "工作上下文.md"), DOCS, "工作上下文.md"),
]

moved = []
for src, dst_dir, name in MOVES:
    if not os.path.exists(src):
        print(f"  [跳过] {os.path.basename(src)} 不存在")
        continue

    dst = os.path.join(dst_dir, name)
    shutil.move(src, dst)
    moved.append(name)
    print(f"  ✓ {os.path.basename(src):<32} → {os.path.relpath(dst, ROOT)}")

print(f"\n共移动 {len(moved)} 个文件")

# 删除 prototype/luxe 下的 _preview.html（iframe 版，已被页面清单替代）
preview = os.path.join(ROOT, "prototype", "luxe", "_preview.html")
if os.path.exists(preview):
    os.remove(preview)
    print("  ✓ 删除 _preview.html（已由页面清单替代）")
