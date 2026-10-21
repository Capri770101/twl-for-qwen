# -*- coding: utf-8 -*-
"""把 base.css 内联到每个 HTML 里，彻底摆脱外部依赖"""
import os, glob

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"

css_path = os.path.join(PROTO, "base.css")
base_css = open(css_path, encoding="utf-8").read()

# 把 <link ... base.css> 替换成 <style>...</style>
LINK_VARIANTS = [
    '<link rel="stylesheet" href="base.css">',
    "<link rel='stylesheet' href='base.css'>",
    '<link rel="stylesheet" href="./base.css">',
]

done = 0
for p in glob.glob(os.path.join(PROTO, "*.html")):
    fn = os.path.basename(p)
    html = open(p, encoding="utf-8").read()

    replaced = False
    for link in LINK_VARIANTS:
        if link in html:
            html = html.replace(link, "<style>\n" + base_css + "\n</style>")
            replaced = True
            break

    if replaced:
        open(p, "w", encoding="utf-8").write(html)
        size = os.path.getsize(p) / 1024 / 1024
        print(f"  {fn}: CSS 已内联 ({size:.2f} MB)")
        done += 1

print(f"\n共处理 {done} 个文件")

# 检查是否还有外部引用
print("\n=== 残留外部依赖检查 ===")
bad = 0
for p in glob.glob(os.path.join(PROTO, "*.html")):
    html = open(p, encoding="utf-8").read()
    if 'href="base.css"' in html:
        print(f"  {os.path.basename(p)}: 还有 base.css 引用")
        bad += 1
if bad == 0:
    print("  所有页面已自包含")
