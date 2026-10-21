# -*- coding: utf-8 -*-
"""把 v9 剩余页面复制到 v10，统一配色 + 内嵌图片"""
import os, base64, io, re, shutil
from PIL import Image

ASSETS = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\assets"
SRC = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\v9"
DST = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\v10"

# ---------- 1. 准备 base64 ----------
def data_uri(rel, width=800, quality=84):
    src = os.path.join(ASSETS, rel.replace("/", os.sep))
    im = Image.open(src).convert("RGB")
    w, h = im.size
    if w > width:
        im = im.resize((width, int(h * width / w)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

print("[1] 编码图片")
IMG = {
    "chenguang": data_uri("products/01_chenguang.png"),
    "xiaoman":   data_uri("products/02_xiaoman.png"),
    "wuye":      data_uri("products/03_wuye.png"),
    "muxing":    data_uri("products/04_muxing.png"),
    "xueluo":    data_uri("products/05_xueluo.png"),
    "shancha":   data_uri("products/06_shancha.png"),
    "hero":      data_uri("hero/hero_workshop.png", 1200, 82),
}
for k, v in IMG.items():
    print(f"  {k}: {len(v)/1024:.0f} KB")

# ---------- 2. 配色替换 ----------
PAIRS = [
    # 变量定义
    ("--white:#ffffff;--black:#121212;",
     "--bg:#FDFBF8;--white:#ffffff;--ink:#1A1512;--accent:#8B5E3C;--accent-deep:#6E4728;--accent-soft:#F5EDE4;"),
    ("--gray-6:#666666;--gray-9:#9e9e9e;--gray-c:#c4c4c4;",
     "--gray-6:#6B6259;--gray-9:#A69C92;--gray-c:#C9C0B6;"),
    ("--gray-e:#e9e9e9;--gray-f:#f6f6f4;",
     "--gray-e:#EBE6DF;--gray-f:#F7F2EC;"),
    # 使用
    ("background:var(--white);color:var(--black);", "background:var(--bg);color:var(--ink);"),
    ("var(--black)", "var(--ink)"),
    ("rgba(255,255,255,.96)", "rgba(253,251,248,.96)"),
    ("rgba(255,255,255,.98)", "rgba(253,251,248,.98)"),
    # 强调色
    (".filter.on{color:var(--ink);border-bottom-color:var(--ink);font-weight:500}",
     ".filter.on{color:var(--accent);border-bottom-color:var(--accent);font-weight:500}"),
    ("background:var(--ink);color:#fff;", "background:var(--accent);color:#fff;"),
    (".price{\n    font-size:13.5px;\n    font-weight:500;\n  }",
     ".price{\n    font-size:13.5px;\n    font-weight:500;\n    color:var(--accent);\n  }"),
]

def recolor(html):
    for a, b in PAIRS:
        html = html.replace(a, b)
    # 价格类统一加色（兜底）
    html = re.sub(r"(\.price\s*\{[^}]*?)(\})",
                  lambda m: m.group(1) + "\n    color:var(--accent);\n  " + m.group(2)
                  if "color:var(--accent)" not in m.group(1) else m.group(0), html)
    return html

# ---------- 3. 逐页处理 ----------
JOBS = [
    # (文件名, [(占位, 图片key), ...], 额外CSS)
    ("product.html", [
        ('<div class="main-image">\n  主图 · 1000 × 1000<br>\n  香槟玫瑰花束<br>\n  白底 · 正面 · 自然光\n</div>',
         '<div class="main-image"><img src="%%chenguang%%" alt="晨光序曲"></div>'),
    ], ".main-image img{width:100%;height:100%;object-fit:cover;display:block}"),

    ("checkout.html", [
        ('<div class="pic">800 × 1000<br>香槟玫瑰</div>',
         '<div class="pic"><img src="%%chenguang%%" alt="晨光序曲"></div>'),
    ], ".product .pic img{width:100%;height:100%;object-fit:cover;display:block}"),

    ("advisor.html", [
        ('<div class="pic">800 × 600<br>向日葵花束</div>',
         '<div class="pic"><img src="%%muxing%%" alt="木星"></div>'),
    ], ".card .pic img{width:100%;height:100%;object-fit:cover;display:block}"),

    ("orders.html", [
        ('<div class="pic">晨光序曲</div>', '<div class="pic"><img src="%%chenguang%%" alt=""></div>'),
        ('<div class="pic">小满</div>',     '<div class="pic"><img src="%%xiaoman%%" alt=""></div>'),
        ('<div class="pic">木星</div>',     '<div class="pic"><img src="%%muxing%%" alt=""></div>'),
    ], ".order .pic img{width:100%;height:100%;object-fit:cover;display:block}"),

    ("done.html", [], ""),   # 无图片
]

print("[2] 处理页面")
for fn, reps, css in JOBS:
    src = os.path.join(SRC, fn)
    dst = os.path.join(DST, fn)
    if not os.path.exists(src):
        print(f"  [skip] {fn} 源文件不存在"); continue
    html = open(src, encoding="utf-8").read()
    html = recolor(html)

    # 插入图片 CSS
    if css:
        html = html.replace("</style>", css + "\n</style>")

    # 替换占位
    for old, new in reps:
        for k, uri in IMG.items():
            new = new.replace(f"%%{k}%%", uri)
        if old in html:
            html = html.replace(old, new)
        else:
            print(f"  [warn] {fn}: 占位未命中")

    open(dst, "w", encoding="utf-8").write(html)
    print(f"  {fn}: {os.path.getsize(dst)/1024/1024:.2f} MB")

print("[done]")
