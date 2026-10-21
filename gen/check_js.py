# -*- coding: utf-8 -*-
"""验证交互 JS 注入情况"""
import glob, os

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"

print("=== 交互检查 ===\n")
ok = 0
no = 0

for p in sorted(glob.glob(os.path.join(PROTO, "*.html"))):
    fn = os.path.basename(p)
    if fn.startswith("_"):
        continue
    h = open(p, encoding="utf-8").read()

    if fn == "admin.html":
        has = "doLogin" in h
    else:
        has = ("TWL.addToCart" in h) or ("TWL.toast" in h) or ("Cart.get" in h)

    mark = "OK" if has else "无"
    if has:
        ok += 1
    else:
        no += 1
    print(f"  {fn:32} {mark}")

print(f"\n有交互: {ok}   无交互: {no}")
