# -*- coding: utf-8 -*-
"""
图片内嵌工具
把 HTML 里的 __IMG_xxx__ 占位符替换成 base64

【路径说明】
用 __file__ 动态计算，不写死绝对路径。
项目换位置也能跑。
"""

import base64
import os
from pathlib import Path

# 脚本在 scripts/ 下，往上两级是项目根
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 前端目录
PROTO = PROJECT_ROOT / "frontend"

# 素材目录
ASSETS = PROJECT_ROOT / "assets"

for p in glob.glob(os.path.join(str(PROTO), "*.html")):
    fn = os.path.basename(p)
    html = open(p, encoding="utf-8").read()
    if "__IMG_" not in html:
        continue
    n = 0
    for k, uri in URIS.items():
        c = html.count(k)
        if c:
            html = html.replace(k, uri)
            n += c
    open(p, "w", encoding="utf-8").write(html)
    print(f"  {fn}: {n} 处 -> {os.path.getsize(p)/1024/1024:.2f} MB")

print("[done]")
