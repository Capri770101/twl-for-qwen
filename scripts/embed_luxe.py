# -*- coding: utf-8 -*-
"""把 luxe 效果图的 __IMG_XXX__ 占位替换成 base64"""
import os, base64, io
from PIL import Image

ASSETS = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\assets"
PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"

SPEC = {
    "__IMG_HERO__": ("hero/hero_workshop.png", 1400, 82),
    "__IMG_P0__":   ("products/00_white_rose.png", 900, 84),
    "__IMG_P1__":   ("products/01_chenguang.png", 900, 84),
    "__IMG_P2__":   ("products/02_xiaoman.png", 900, 84),
    "__IMG_P3__":   ("products/03_wuye.png", 900, 84),
    "__IMG_P4__":   ("products/04_muxing.png", 900, 84),
    "__IMG_P5__":   ("products/05_xueluo.png", 900, 84),
    "__IMG_P6__":   ("products/06_shancha.png", 900, 84),
}

def to_uri(rel, w, q):
    src = os.path.join(ASSETS, rel.replace("/", os.sep))
    if not os.path.exists(src):
        return None
    im = Image.open(src).convert("RGB")
    W, H = im.size
    if W > w:
        im = im.resize((w, int(H * w / W)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

print("[1] 编码")
URIS = {}
for k, (rel, w, q) in SPEC.items():
    uri = to_uri(rel, w, q)
    if uri:
        URIS[k] = uri
        print(f"  {k} <- {rel} ({len(uri)/1024:.0f} KB)")

print("[2] 替换")
import glob
for p in glob.glob(os.path.join(PROTO, "*.html")):
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
