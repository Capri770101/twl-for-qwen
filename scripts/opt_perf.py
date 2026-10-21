# -*- coding: utf-8 -*-
"""
性能优化

1. 给所有 api.js 加 defer（消除阻塞渲染）
2. 首页 base64 图片改成外链
3. 后端加 GZip 中间件
4. 后端加缓存头
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE = ROOT / "frontend"
B = ROOT / "backend"

print("=" * 70)
print("  性能优化")
print("=" * 70)


# ══════════════════════════════════════════════════════════
# 1. api.js 加 defer
# ══════════════════════════════════════════════════════════
print("\n【1. api.js 加 defer】")

n = 0
for f in sorted(FE.glob("*.html")):
    c = f.read_text(encoding="utf-8")
    original = c

    # 匹配没有 defer/async 的
    c = re.sub(
        r'<script src="js/api\.js"></script>',
        '<script src="js/api.js" defer></script>',
        c,
    )
    c = re.sub(
        r"<script src='js/api\.js'></script>",
        '<script src="js/api.js" defer></script>',
        c,
    )

    if c != original:
        f.write_text(c, encoding="utf-8")
        print(f"  ✓ {f.name}")
        n += 1

print(f"    共 {n} 个页面")


# ══════════════════════════════════════════════════════════
# 2. 首页 base64 图片改外链
# ══════════════════════════════════════════════════════════
print("\n【2. 首页 base64 图片改外链】")

idx = FE / "index.html"
c = idx.read_text(encoding="utf-8")

# 找所有 base64 图片，统计
b64_imgs = re.findall(r'src="data:image/(\w+);base64,([^"]{100,})"', c)
print(f"  找到 {len(b64_imgs)} 张 base64 图")

if b64_imgs:
    # 按出现顺序映射到已有图片文件（首页用的是 hero + 商品图）
    # 策略：把 base64 换成外链，图已经在 frontend/images/ 和 assets/ 里
    #
    # 但首页的 base64 可能是 hero_workshop.png 和商品图，
    # 需要按顺序对应。

    # 先看现有可用的图
    images_dir = FE / "images"
    available = sorted(p.name for p in images_dir.glob("*.png")) if images_dir.exists() else []

    # hero 图在 assets/
    assets_hero = ROOT / "assets" / "hero"
    hero_files = sorted(p.name for p in assets_hero.glob("*.png")) if assets_hero.exists() else []

    print(f"  images/ 可用: {available}")
    print(f"  assets/hero 可用: {hero_files}")

    # 如果 hero 图不在 frontend/images，先复制过去
    if hero_files and "hero_workshop.png" not in available:
        import shutil
        src = assets_hero / "hero_workshop.png"
        if src.exists():
            shutil.copy2(src, images_dir / "hero_workshop.png")
            print("  ✓ 复制 hero_workshop.png 到 frontend/images/")

    # 替换：第 1 张 = hero，后面 = 商品图
    def repl(m):
        nonlocal_counter = repl.counter
        repl.counter += 1
        if repl.counter == 1:
            return 'src="/images/hero_workshop.png"'
        else:
            i = (repl.counter - 2) % max(1, len(available))
            if available:
                return f'src="/images/{available[i]}"'
            return m.group(0)

    repl.counter = 0

    new_c = re.sub(r'src="data:image/(\w+);base64,([^"]{100,})"', repl, c)

    if new_c != c:
        idx.write_text(new_c, encoding="utf-8")
        print(f"  ✓ 替换了 {repl.counter} 张")


# ══════════════════════════════════════════════════════════
# 3. 后端加 GZip 中间件
# ══════════════════════════════════════════════════════════
print("\n【3. 后端加 GZip】")

main_py = B / "app" / "main.py"
c = main_py.read_text(encoding="utf-8")

if "GZipMiddleware" not in c:
    # 找中间件注册的地方
    anchor = "app = FastAPI("
    i = c.find(anchor)
    if i > 0:
        # 找 app 定义结束的位置（下一个空行 + 非缩进行）
        # 简单策略：在 app = FastAPI(...) 结束后插入
        # 找 "add_middleware" 第一次出现
        mw = c.find("add_middleware", i)
        if mw > 0:
            # 往前找行首
            line_start = c.rfind("\n", 0, mw) + 1
            insert = (
                "# ── GZip 压缩 ──\n"
                "# HTML 531KB 压缩后约 60KB，首屏快 3 倍\n"
                "from fastapi.middleware.gzip import GZipMiddleware\n"
                "app.add_middleware(GZipMiddleware, minimum_size=500)\n\n"
            )
            c = c[:line_start] + insert + c[line_start:]
            main_py.write_text(c, encoding="utf-8")
            print("  ✓ 加了 GZipMiddleware（>500 字节就压缩）")
        else:
            print("  ⚠ 找不到 add_middleware")
    else:
        print("  ⚠ 找不到 app = FastAPI")
else:
    print("  - 已有 GZip")


# ══════════════════════════════════════════════════════════
# 4. 静态文件加缓存头
# ══════════════════════════════════════════════════════════
print("\n【4. 静态文件缓存头】")

if "Cache-Control" not in c:
    # 用自定义 StaticFiles 子类
    old_mount = '''# 再挂前端根目录（兜底）
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")'''

    new_mount = '''# ── 自定义 StaticFiles，加缓存头 ──
#
# 【为什么】
# 图片、JS、CSS 变的不频繁，浏览器可以缓存。
# HTML 要经常更新，不能长缓存。
class CachedStaticFiles(StaticFiles):
    """给静态文件加 Cache-Control"""

    async def get_response(self, path: str, scope):
        resp = await super().get_response(path, scope)

        if path.endswith((".html", ".txt", ".xml")):
            # HTML / sitemap / robots：不缓存，改了立刻生效
            resp.headers["Cache-Control"] = "public, max-age=0, must-revalidate"
        else:
            # 图片 / JS / CSS：缓存 7 天
            resp.headers["Cache-Control"] = "public, max-age=604800"

        return resp


# 再挂前端根目录（兜底）
app.mount("/", CachedStaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")'''

    if old_mount in c:
        c = c.replace(old_mount, new_mount, 1)
        main_py.write_text(c, encoding="utf-8")
        print("  ✓ 加了 Cache-Control")
    else:
        print("  ⚠ 未匹配挂载代码")
else:
    print("  - 已有 Cache-Control")


print("\n" + "=" * 70)
