# -*- coding: utf-8 -*-
"""修正 HTML 里的资源路径（api.js 移到 js/ 之后）"""

import os
import re

R = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰"
FE = os.path.join(R, "frontend")

print("=== 修正资源路径 ===\n")

changed = 0

for f in sorted(os.listdir(FE)):
    if not f.endswith(".html"):
        continue

    path = os.path.join(FE, f)
    with open(path, encoding="utf-8") as fh:
        html = fh.read()

    original = html

    # src="api.js" → src="js/api.js"
    html = html.replace('src="api.js"', 'src="js/api.js"')

    # link rel="stylesheet" href="base.css" → href="css/base.css"
    html = html.replace('href="base.css"', 'href="css/base.css"')

    # 图片路径 /images/xx.png 保持不变（由后端 /images 静态提供？不，现在图片在 frontend/images/）
    # 因为前端根目录是 frontend/，所以 /images/xx.png 会映射到 frontend/images/xx.png
    # 不需要改

    if html != original:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)
        print(f"  ✓ {f}")
        changed += 1

print(f"\n修改了 {changed} 个文件")

# 检查还剩哪些引用 api.js（不带 js/）
print("\n=== 检查残留 ===")
for f in sorted(os.listdir(FE)):
    if not f.endswith(".html"):
        continue
    path = os.path.join(FE, f)
    with open(path, encoding="utf-8") as fh:
        html = fh.read()
    if 'src="api.js"' in html:
        print(f"  ⚠ {f} 还有 src=\"api.js\"")

print("  检查完成")
