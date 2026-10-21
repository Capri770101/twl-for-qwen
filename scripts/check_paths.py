# -*- coding: utf-8 -*-
"""
路径可移植性验证
模拟项目换位置，检查所有路径还能不能正常工作
"""

import os
import re
import sys
from pathlib import Path

# 项目根目录：脚本在 scripts/ 下，往上一级就是根
R = Path(__file__).resolve().parent.parent

print("=" * 70)
print("  路径可移植性验证")
print("=" * 70)

issues = []

# ══════════════════════════════════════════════════════════
# 1. 检查所有代码文件里的硬编码绝对路径
# ══════════════════════════════════════════════════════════
print("\n【1. 代码文件里的绝对路径】")

EXTS = {".py", ".html", ".js", ".bat", ".ps1", ".ini", ".toml"}

# 匹配盘符路径（用于检测，不是代码里的真实路径）
ABS_PATH_RE = re.compile(r'[A-Z]:[\\\\/]')
SKIP = {".venv", ".git", "node_modules", "__pycache__"}

for f in R.rglob("*"):
    if not f.is_file():
        continue
    if any(s in f.parts for s in SKIP):
        continue
    if f.suffix not in EXTS:
        continue

    try:
        content = f.read_text(encoding="utf-8")
    except Exception:
        continue

    # 排除注释里的示例路径（以 # 或 // 开头）
    for i, line in enumerate(content.split("\n"), 1):
        stripped = line.strip()

        # 跳过纯注释行
        if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
            continue

        # 找 D:\ 或 D:/ 或 DeepSeek-Harness
        if ABS_PATH_RE.search(line):
            rel = f.relative_to(R)
            issues.append(f"{rel}:{i}  {stripped[:80]}")

if issues:
    for i in issues:
        print(f"  ✗ {i}")
else:
    print("  ✓ 无硬编码绝对路径")


# ══════════════════════════════════════════════════════════
# 2. 检查 Python 文件是否用 __file__ 算路径
# ══════════════════════════════════════════════════════════
print("\n【2. Python 文件的路径写法】")

py_files = [
    R / "backend" / "app" / "main.py",
    R / "scripts" / "embed_luxe.py",
    R / "backend" / "tests" / "test_core_logic.py",
]

for f in py_files:
    if not f.exists():
        print(f"  - {f.relative_to(R)} 不存在")
        continue

    content = f.read_text(encoding="utf-8")

    if "__file__" in content:
        print(f"  ✓ {f.relative_to(R)} 用 __file__ 计算路径")
    else:
        print(f"  ⚠ {f.relative_to(R)} 没用 __file__")


# ══════════════════════════════════════════════════════════
# 3. 检查前端页面的资源引用
# ══════════════════════════════════════════════════════════
print("\n【3. 前端资源引用】")

frontend = R / "frontend"
html_files = sorted(frontend.glob("*.html"))

bad_js = []
bad_css = []
good = 0

for f in html_files:
    content = f.read_text(encoding="utf-8")

    # api.js 应该是 js/api.js
    if 'src="api.js"' in content:
        bad_js.append(f.name)
    elif 'src="js/api.js"' in content:
        good += 1

    # base.css 应该是 css/base.css
    if 'href="base.css"' in content:
        bad_css.append(f.name)

print(f"  ✓ {good} 个页面用 js/api.js")

if bad_js:
    print(f"  ✗ 还有 {len(bad_js)} 个页面用旧路径 api.js: {bad_js}")
else:
    print("  ✓ 无旧路径")

if bad_css:
    print(f"  ✗ 还有 {len(bad_css)} 个页面用 base.css: {bad_css}")


# ══════════════════════════════════════════════════════════
# 4. 检查页面之间的链接
# ══════════════════════════════════════════════════════════
print("\n【4. 页面之间的链接】")

broken = []
for f in html_files:
    content = f.read_text(encoding="utf-8")

    # 找 href="xxx.html"
    for m in re.finditer(r'href="([a-z-]+\.html)(?:\?[^"]*)?"', content):
        target = m.group(1)
        if not (frontend / target).exists():
            broken.append(f"{f.name} → {target}")

if broken:
    for b in broken[:10]:
        print(f"  ✗ {b}")
else:
    print(f"  ✓ {len(html_files)} 个页面的内部链接全部有效")


# ══════════════════════════════════════════════════════════
# 5. 检查 docs 里的链接
# ══════════════════════════════════════════════════════════
print("\n【5. docs 里的链接】")

docs = R / "docs"
broken_docs = []

for f in docs.rglob("*.html"):
    content = f.read_text(encoding="utf-8")

    for m in re.finditer(r'href="([^"#][^"]*\.html)(?:\?[^"]*)?"', content):
        target = m.group(1)
        # 跳过外链
        if target.startswith("http"):
            continue
        # 相对路径解析
        resolved = (f.parent / target).resolve()
        if not resolved.exists():
            broken_docs.append(f"{f.relative_to(docs)} → {target}")

if broken_docs:
    for b in broken_docs[:10]:
        print(f"  ✗ {b}")
else:
    print("  ✓ docs 里的链接全部有效")


# ══════════════════════════════════════════════════════════
# 6. 检查启动脚本
# ══════════════════════════════════════════════════════════
print("\n【6. 启动脚本】")

start_ps1 = R / "scripts" / "start.ps1"
if start_ps1.exists():
    content = start_ps1.read_text(encoding="utf-8")
    if "$PSScriptRoot" in content:
        print("  ✓ start.ps1 用 $PSScriptRoot")
    else:
        print("  ⚠ start.ps1 没用 $PSScriptRoot")

start_bat = R / "启动.bat"
if start_bat.exists():
    content = start_bat.read_text(encoding="utf-8", errors="ignore")
    if "%~dp0" in content:
        print("  ✓ 启动.bat 用 %~dp0")
    else:
        print("  ⚠ 启动.bat 没用 %~dp0")


# ══════════════════════════════════════════════════════════
# 汇总
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 70)
if issues:
    print(f"  发现 {len(issues)} 处硬编码路径，需要修复")
else:
    print("  路径可移植性验证通过")
print("=" * 70)
