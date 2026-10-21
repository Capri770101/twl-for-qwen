# -*- coding: utf-8 -*-
"""
轻量性能测评

Lighthouse 需要下载 CLI，这个脚本不依赖它，
直接测关键指标：

1. TTFB（首字节时间）
2. HTML 大小
3. 首屏资源数（CSS/JS/图片）
4. 阻塞渲染的资源
5. 图片是否压缩
6. 缓存头
"""

import re
import time
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000"
FE = Path(__file__).resolve().parent.parent / "frontend"

PAGES = [
    ("首页", "/"),
    ("商城", "/shop.html"),
    ("商品详情", "/product.html?id=TW-001"),
    ("花语列表", "/flower-language.html"),
    ("花语详情", "/flower-language-detail.html?slug=white-rose"),
]


def measure(path: str) -> dict:
    """测一个页面的性能指标"""
    url = f"{BASE}{path}"

    # TTFB + 总时间
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            ttfb = time.time() - t0
            body = r.read()
            total = time.time() - t0
            headers = dict(r.headers)
    except Exception as e:
        return {"error": str(e)}

    html = body.decode("utf-8", errors="replace")

    # 资源统计
    css_blocks = len(re.findall(r"<style", html))
    js_ext = len(re.findall(r'<script[^>]+src="', html))
    js_inline = len(re.findall(r"<script(?![^>]*src)[^>]*>", html))
    imgs = re.findall(r'<img[^>]+src="([^"]+)"', html)
    imgs_external = [i for i in imgs if not i.startswith("data:")]
    imgs_inline = len(imgs) - len(imgs_external)

    # 阻塞渲染的 JS（没有 defer/async）
    blocking_js = len(re.findall(r'<script(?![^>]*(?:defer|async))[^>]+src="', html))

    # 阻塞渲染的 CSS（外部）
    ext_css = len(re.findall(r'<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"', html))

    # 内联 CSS 大小
    inline_css_size = sum(len(m) for m in re.findall(r"<style[^>]*>(.*?)</style>", html, re.DOTALL))

    return {
        "ttfb": ttfb,
        "total": total,
        "size": len(body),
        "size_kb": len(body) / 1024,
        "css_blocks": css_blocks,
        "inline_css_kb": inline_css_size / 1024,
        "js_ext": js_ext,
        "js_inline": js_inline,
        "blocking_js": blocking_js,
        "ext_css": ext_css,
        "imgs_total": len(imgs),
        "imgs_external": len(imgs_external),
        "imgs_inline": imgs_inline,
        "cache": headers.get("Cache-Control", "无"),
        "gzip": headers.get("Content-Encoding", "无"),
    }


print("=" * 74)
print("  轻量性能测评")
print("=" * 74)
print()

results = {}

for name, path in PAGES:
    r = measure(path)
    results[name] = r

    if "error" in r:
        print(f"✗ {name}  失败: {r['error']}")
        continue

    print(f"【{name}】")
    print(f"  TTFB        {r['ttfb']*1000:>7.0f} ms   {'✓' if r['ttfb'] < 0.6 else '⚠ 目标 <600ms'}")
    print(f"  总耗时      {r['total']*1000:>7.0f} ms")
    print(f"  HTML 大小   {r['size_kb']:>7.1f} KB   {'✓' if r['size_kb'] < 1024 else '⚠ 目标 <1024KB'}")
    print(f"  内联 CSS    {r['inline_css_kb']:>7.1f} KB（{r['css_blocks']} 块）")
    print(f"  外部 CSS    {r['ext_css']:>7} 个   {'✓' if r['ext_css'] == 0 else '⚠ 阻塞渲染'}")
    print(f"  外部 JS     {r['js_ext']:>7} 个")
    print(f"  阻塞 JS     {r['blocking_js']:>7} 个   {'✓' if r['blocking_js'] == 0 else '⚠ 会阻塞'}")
    print(f"  图片        {r['imgs_total']:>7} 个（外链 {r['imgs_external']} / 内嵌 {r['imgs_inline']}）")
    print(f"  压缩        {r['gzip']:>7}")
    print(f"  缓存        {r['cache'][:40]}")
    print()


# ══════════════════════════════════════════════════════════
# 评分
# ══════════════════════════════════════════════════════════
print("=" * 74)
print("  评分")
print("=" * 74)
print()

# TTFB
ttfbs = [r["ttfb"] for r in results.values() if "ttfb" in r]
avg_ttfb = sum(ttfbs) / len(ttfbs) if ttfbs else 0
ttfb_score = 100 if avg_ttfb < 0.2 else (80 if avg_ttfb < 0.6 else 50)
print(f"  TTFB        {avg_ttfb*1000:>6.0f} ms  →  {ttfb_score} 分")

# 阻塞资源
total_blocking = sum(r.get("blocking_js", 0) + r.get("ext_css", 0) for r in results.values())
block_score = 100 if total_blocking == 0 else max(0, 100 - total_blocking * 10)
print(f"  阻塞资源    {total_blocking:>6} 个   →  {block_score} 分")

# 页面大小
sizes = [r["size_kb"] for r in results.values() if "size_kb" in r]
max_size = max(sizes) if sizes else 0
size_score = 100 if max_size < 500 else (80 if max_size < 1024 else 50)
print(f"  最大页面    {max_size:>6.0f} KB  →  {size_score} 分")

# 外部依赖
total_ext = sum(r.get("js_ext", 0) + r.get("ext_css", 0) for r in results.values())
ext_score = 100 if total_ext == 0 else max(0, 100 - total_ext * 5)
print(f"  外部依赖    {total_ext:>6} 个   →  {ext_score} 分")

overall = int((ttfb_score + block_score + size_score + ext_score) / 4)
print()
print(f"  综合        {overall} 分")
print()

# ══════════════════════════════════════════════════════════
# 建议
# ══════════════════════════════════════════════════════════
print("=" * 74)
print("  优化建议")
print("=" * 74)
print()

advice = []

if avg_ttfb >= 0.6:
    advice.append("TTFB 偏高：加 Redis 缓存页面数据，或用 Nginx 直接托管静态页")

if total_blocking > 0:
    advice.append(f"有 {total_blocking} 个阻塞渲染的资源：给 <script> 加 defer 属性")

if max_size > 1024:
    advice.append(f"最大页面 {max_size:.0f} KB 超过 1MB：首页的内嵌图片可以改成外链 + lazy load")

imgs_inline_total = sum(r.get("imgs_inline", 0) for r in results.values())
if imgs_inline_total > 0:
    advice.append(
        f"有 {imgs_inline_total} 张图片用 base64 内嵌在 HTML 里："
        "会撑大 HTML，建议改成外链 + WebP 格式"
    )

if not advice:
    advice.append("没有明显问题")

for i, a in enumerate(advice, 1):
    print(f"  {i}. {a}")

print()
