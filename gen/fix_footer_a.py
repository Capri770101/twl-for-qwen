# -*- coding: utf-8 -*-
"""把 index.html / shop.html 的深色页脚改成浅米色页脚"""
import os, re

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"

REPLACE = [
    # 页脚主容器
    ("footer{background:var(--ink);color:rgba(255,255,255,.75);padding:52px 0 0}",
     "footer{background:var(--paper);color:var(--gray-7);padding:52px 0 0;border-top:1px solid var(--gray-d)}"),
    ("footer{background:var(--ink);color:rgba(255,255,255,.75);padding:56px 0 0}",
     "footer{background:var(--paper);color:var(--gray-7);padding:56px 0 0;border-top:1px solid var(--gray-d)}"),

    # 品牌区分隔线
    ("border-right:1px solid rgba(255,255,255,.16);min-width:170px;",
     "border-right:1px solid var(--gray-d);min-width:170px;"),
    ("border-right:1px solid rgba(255,255,255,.16);min-width:180px;",
     "border-right:1px solid var(--gray-d);min-width:180px;"),

    # 品牌名
    ("letter-spacing:.4em;text-indent:.4em;color:#fff;line-height:1;margin-bottom:9px;",
     "letter-spacing:.4em;text-indent:.4em;color:var(--ink);line-height:1;margin-bottom:9px;"),
    ("letter-spacing:.42em;text-indent:.42em;color:#fff;line-height:1;margin-bottom:10px;",
     "letter-spacing:.42em;text-indent:.42em;color:var(--ink);line-height:1;margin-bottom:10px;"),

    # 英文名 / slogan
    ("color:rgba(255,255,255,.45);", "color:var(--gray-a);"),
    ("color:rgba(255,255,255,.55);letter-spacing:.04em;", "color:var(--gray-7);letter-spacing:.04em;"),
    ("color:rgba(255,255,255,.55)}", "color:var(--gray-7)}"),

    # 栏目标题
    ("color:rgba(255,255,255,.42);margin-bottom:14px;", "color:var(--gray-a);margin-bottom:14px;"),
    ("color:rgba(255,255,255,.42);margin-bottom:16px;", "color:var(--gray-a);margin-bottom:16px;"),

    # 栏目链接
    ("color:rgba(255,255,255,.78);white-space:nowrap;transition:color .2s;",
     "color:var(--gray-7);white-space:nowrap;transition:color .2s;"),
    (".foot-col a:hover{color:#fff}", ".foot-col a:hover{color:var(--ink)}"),

    # 底部分隔线
    ("border-top:1px solid rgba(255,255,255,.14);flex-wrap:wrap;",
     "border-top:1px solid var(--gray-d);flex-wrap:wrap;"),

    # 版权
    ("color:rgba(255,255,255,.4);line-height:1.8", "color:var(--gray-a);line-height:1.8"),
    ("color:rgba(255,255,255,.4)}\n  .social", "color:var(--gray-a)}\n  .social"),

    # 社交图标
    ("border:1px solid rgba(255,255,255,.24);border-radius:50%;",
     "border:1px solid var(--gray-d);border-radius:50%;"),
    ("color:rgba(255,255,255,.65);transition:all .25s;",
     "color:var(--gray-7);transition:all .25s;"),
    (".social a:hover{background:#fff;color:var(--ink);border-color:#fff}",
     ".social a:hover{background:var(--ink);color:#fff;border-color:var(--ink)}"),
]

for fn in ["index.html", "shop.html"]:
    p = os.path.join(PROTO, fn)
    html = open(p, encoding="utf-8").read()
    n = 0
    for a, b in REPLACE:
        c = html.count(a)
        if c:
            html = html.replace(a, b)
            n += c
    open(p, "w", encoding="utf-8").write(html)
    print(f"  {fn}: {n} 处")

print("\n=== 残留检查 ===")
for fn in ["index.html", "shop.html", "admin.html"]:
    p = os.path.join(PROTO, fn)
    html = open(p, encoding="utf-8").read()
    left = re.findall(r"rgba\(255,255,255,[\d.]+\)", html)
    if left:
        print(f"  {fn}: 还有 {len(left)} 处 rgba(255,255,255,...)")
    else:
        print(f"  {fn}: ✅")
