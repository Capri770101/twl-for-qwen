# -*- coding: utf-8 -*-
"""
爬虫可读性测评（crawlability）

【为什么这个最重要】
搜索引擎爬虫不执行 JS（或者执行能力很弱）。
如果页面内容是 JS 动态渲染的，爬虫看到的是空壳，SEO 就是废的。

【怎么测】
不带 JS 抓页面 HTML 源码，检查正文关键词是否在里面。

【输出】
每个页面：HTML 里有什么、缺什么
"""

import re
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000"

print("=" * 70)
print("  爬虫可读性测评（crawlability）")
print("=" * 70)
print()


def fetch(path: str) -> str:
    """抓页面源码（不执行 JS）"""
    try:
        with urllib.request.urlopen(f"{BASE}{path}", timeout=10) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"__ERROR__{e}"


def check_page(name: str, path: str, must_have: list[str]) -> dict:
    """
    【干什么】检查页面的可爬取性

    【must_have】
        必须出现在 HTML 源码里的关键词
    """
    html = fetch(path)

    if html.startswith("__ERROR__"):
        return {"name": name, "ok": False, "error": html[9:], "found": [], "missing": must_have}

    # 去掉 script/style，只留可见文本
    body = re.sub(r"<script.*?</script>", "", html, flags=re.DOTALL)
    body = re.sub(r"<style.*?</style>", "", body, flags=re.DOTALL)
    # 去标签
    text = re.sub(r"<[^>]+>", " ", body)
    text = re.sub(r"\s+", " ", text)

    found = [k for k in must_have if k in text]
    missing = [k for k in must_have if k not in text]

    return {
        "name": name,
        "ok": len(missing) == 0,
        "error": None,
        "found": found,
        "missing": missing,
        "text_len": len(text),
        "html_len": len(html),
    }


# ══════════════════════════════════════════════════════════
# 测试项
# ══════════════════════════════════════════════════════════
TESTS = [
    # 首页：品牌名、核心业务
    ("首页", "/", ["跳舞兰", "深圳", "花"]),

    # 商城：商品名必须在源码里
    ("商城", "/shop.html", ["晨光序曲", "小满", "¥"]),

    # 商品详情：商品名 + 价格 + 花材
    ("商品详情", "/product.html?id=TW-001", ["晨光序曲", "299", "香槟玫瑰"]),

    # 花语列表：文章标题必须在源码里
    ("花语列表", "/flower-language.html", ["香槟玫瑰", "白玫瑰", "向日葵"]),

    # 花语详情：正文必须在源码里
    ("花语详情", "/flower-language-detail.html?slug=white-rose", ["白玫瑰", "纯洁", "花语"]),

    # 关于：品牌叙事
    ("关于", "/about.html", ["跳舞兰", "深圳"]),

    # FAQ：问答内容
    ("FAQ", "/help-faq.html", ["多久", "登录"]),
]


results = []

for name, path, must in TESTS:
    r = check_page(name, path, must)
    results.append(r)

    if r["error"]:
        print(f"✗ {name:<12} 抓取失败: {r['error']}")
        continue

    if r["ok"]:
        print(f"✓ {name:<12} 全部命中（可见文本 {r['text_len']} 字）")
    else:
        print(f"✗ {name:<12} HTML {r['html_len']} 字节，可见文本 {r['text_len']} 字")
        print(f"    命中: {', '.join(r['found']) or '无'}")
        print(f"    缺失: {', '.join(r['missing'])}")


# ══════════════════════════════════════════════════════════
# 汇总
# ══════════════════════════════════════════════════════════
print()
print("=" * 70)

ok = sum(1 for r in results if r.get("ok"))
total = len(results)

print(f"  通过 {ok} / {total}")

if ok < total:
    print()
    print("  【问题】")
    print("  上面标 ✗ 的页面，关键内容不在 HTML 源码里。")
    print("  说明这些内容靠 JS 渲染，搜索引擎爬虫读不到。")
    print()
    print("  【怎么修】")
    print("  方案 A：后端渲染（FastAPI 返回渲染好的 HTML）")
    print("  方案 B：构建时预渲染（改完内容跑一次构建，生成静态 HTML）")
    print("  方案 C：关键内容内联到 HTML（首屏内容直出，交互部分才用 JS）")

print("=" * 70)
