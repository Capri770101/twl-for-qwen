# -*- coding: utf-8 -*-
"""把图片压缩并转 base64，替换 HTML 里的 img src"""
import os, base64, io, re
from PIL import Image

ASSETS = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\assets"
PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\v10"

# 图片 -> (目标宽度, 质量)
SPEC = {
    "hero/hero_workshop.png":      (1200, 82),
    "products/00_white_rose.png":  (800, 84),
    "products/01_chenguang.png":   (800, 84),
    "products/02_xiaoman.png":     (800, 84),
    "products/03_wuye.png":        (800, 84),
    "products/04_muxing.png":      (800, 84),
    "products/05_xueluo.png":      (800, 84),
    "products/06_shancha.png":     (800, 84),
}

def to_data_uri(rel, width, quality):
    src = os.path.join(ASSETS, rel.replace("/", os.sep))
    im = Image.open(src).convert("RGB")
    w, h = im.size
    if w > width:
        im = im.resize((width, int(h * width / w)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    data = buf.getvalue()
    b64 = base64.b64encode(data).decode()
    print(f"  {rel}: {len(data)/1024:.0f} KB -> base64 {len(b64)/1024:.0f} KB")
    return f"data:image/jpeg;base64,{b64}"

print("[1] 压缩并编码图片")
URIS = {}
for rel, (w, q) in SPEC.items():
    URIS[rel] = to_data_uri(rel, w, q)

print("[2] 替换 HTML")
files = ["index.html", "shop.html"]
for fn in files:
    p = os.path.join(PROTO, fn)
    if not os.path.exists(p): continue
    html = open(p, encoding="utf-8").read()
    n = 0
    for rel, uri in URIS.items():
        # 匹配 "../../assets/xxx" 或 "../assets/xxx"
        for prefix in ("../../assets/", "../assets/"):
            old = prefix + rel
            if old in html:
                html = html.replace(old, uri)
                n += html.count(uri) if False else 1
    open(p, "w", encoding="utf-8").write(html)
    size = os.path.getsize(p) / 1024 / 1024
    print(f"  {fn}: {size:.2f} MB")

print("[done]")
