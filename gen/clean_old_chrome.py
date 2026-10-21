# -*- coding: utf-8 -*-
"""移除残留的旧 topbar / brand 块（支持嵌套 div）"""

import os, glob

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"


def remove_div_block(html: str, class_name: str) -> str:
    """移除指定 class 的 div 及其全部内容（正确处理嵌套）"""
    start_marker = f'<div class="{class_name}"'
    idx = html.find(start_marker)
    if idx < 0:
        return html

    depth = 0
    i = idx
    while i < len(html):
        if html.startswith("<div", i):
            depth += 1
            i += 4
        elif html.startswith("</div>", i):
            depth -= 1
            i += 6
            if depth == 0:
                # 找到匹配的结束标签，删除整块
                return html[:idx] + html[i:]
        else:
            i += 1
    return html


count = 0
for p in sorted(glob.glob(os.path.join(PROTO, "*.html"))):
    fn = os.path.basename(p)
    if fn.startswith("_") or fn == "admin.html":
        continue

    html = open(p, encoding="utf-8").read()
    orig = html

    # 移除旧的 topbar / brand / mainnav
    for cls in ["topbar", "brand", "mainnav"]:
        html = remove_div_block(html, cls)

    # 清理多余空行
    while "\n\n\n" in html:
        html = html.replace("\n\n\n", "\n\n")

    if html != orig:
        open(p, "w", encoding="utf-8").write(html)
        count += 1
        print(f"  {fn}")

print(f"\n清理 {count} 个页面")

# 再次检查
print("\n=== 复查 ===")
bad = 0
for p in sorted(glob.glob(os.path.join(PROTO, "*.html"))):
    fn = os.path.basename(p)
    if fn.startswith("_") or fn == "admin.html":
        continue
    h = open(p, encoding="utf-8").read()
    hd = h.count('<header class="site-header">')
    ft = h.count('<footer class="site-footer">')
    ot = h.count('<div class="topbar"')
    ob = h.count('<div class="brand"')
    issues = []
    if hd != 1:
        issues.append(f"header={hd}")
    if ft != 1:
        issues.append(f"footer={ft}")
    if ot:
        issues.append(f"topbar={ot}")
    if ob:
        issues.append(f"brand={ob}")
    if issues:
        print(f"  {fn:30} {' '.join(issues)}")
        bad += 1

if bad == 0:
    print("  全部正常")
