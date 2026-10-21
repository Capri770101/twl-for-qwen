# -*- coding: utf-8 -*-
"""把 aoyama 效果图里的图片路径替换成 base64，避免相对路径问题"""
import os, base64, io, re
from PIL import Image

ASSETS = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\assets"
PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\aoyama"

# 图片 -> (宽度, 质量)
SPEC = {
    "hero/hero_workshop.png":      (1400, 82),
    "products/00_white_rose.png":  (900, 84),
    "products/01_chenguang.png":   (900, 84),
    "products/02_xiaoman.png":     (900, 84),
    "products/03_wuye.png":        (900, 84),
    "products/04_muxing.png":      (900, 84),
    "products/05_xueluo.png":      (900, 84),
    "products/06_shancha.png":     (900, 84),
}

def to_data_uri(rel, width, quality):
    src = os.path.join(ASSETS, rel.replace("/", os.sep))
    if not os.path.exists(src):
        print(f"  [skip] {rel} 不存在")
        return None
    im = Image.open(src).convert("RGB")
    w, h = im.size
    if w > width:
        im = im.resize((width, int(h * width / w)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    data = buf.getvalue()
    print(f"  {rel}: {len(data)/1024:.0f} KB")
    return "data:image/jpeg;base64," + base64.b64encode(data).decode()

print("[1] 编码图片")
URIS = {}
for rel, (w, q) in SPEC.items():
    uri = to_data_uri(rel, w, q)
    if uri:
        URIS[rel] = uri

print("[2] 替换 HTML")
for fn in ["index.html", "shop.html", "admin.html"]:
    p = os.path.join(PROTO, fn)
    if not os.path.exists(p):
        continue
    html = open(p, encoding="utf-8").read()
    n = 0
    for rel, uri in URIS.items():
        # 匹配 ../assets/xxx 或 ../../assets/xxx
        for prefix in ["../../assets/", "../assets/"]:
            old = prefix + rel
            if old in html:
                cnt = html.count(old)
                html = html.replace(old, uri)
                n += cnt
    open(p, "w", encoding="utf-8").write(html)
    size = os.path.getsize(p) / 1024 / 1024
    print(f"  {fn}: 替换 {n} 处 -> {size:.2f} MB")

print("[done]")
