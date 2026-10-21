# -*- coding: utf-8 -*-
"""
SEO / GEO 验收检查
检查每个页面是否具备完整的 SEO 要素

【检查项】
1. title 唯一且长度合理
2. description 长度合理
3. canonical
4. OG 标签
5. Twitter Card
6. JSON-LD 结构化数据
7. robots 指令
8. h1 唯一
9. img 有 alt
10. 站点文件（robots.txt / sitemap.xml / llms.txt）
"""

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"

print("=" * 70)
print("  SEO / GEO 验收检查")
print("=" * 70)

issues = []
titles = []
descriptions = []

html_files = sorted(FRONTEND.glob("*.html"))

# ══════════════════════════════════════════════════════════
# 1. 逐页检查
# ══════════════════════════════════════════════════════════
print("\n【逐页检查】\n")
print(f"{'页面':<32} {'title':<6} {'desc':<6} {'canon':<6} {'OG':<5} {'LD':<5} {'robots':<7} {'h1':<4} {'alt'}")

for f in html_files:
    c = f.read_text(encoding="utf-8")
    name = f.name

    # title
    m = re.search(r"<title>([^<]+)</title>", c)
    title = m.group(1) if m else ""
    has_title = bool(title)
    if title:
        titles.append((name, title))

    # description
    m = re.search(r'<meta name="description" content="([^"]*)"', c)
    desc = m.group(1) if m else ""
    has_desc = bool(desc)
    if desc:
        descriptions.append((name, desc))

    # canonical
    has_canon = bool(re.search(r'<link rel="canonical"', c))

    # OG
    has_og = bool(re.search(r'<meta property="og:title"', c))

    # JSON-LD
    ld_count = len(re.findall(r'<script type="application/ld\+json">', c))
    has_ld = ld_count > 0

    # robots
    m = re.search(r'<meta name="robots" content="([^"]*)"', c)
    robots = m.group(1).split(",")[0].strip() if m else "无"

    # h1 数量
    h1_count = len(re.findall(r"<h1[\s>]", c))

    # img 无 alt 的数量
    imgs = re.findall(r"<img\b[^>]*>", c)
    no_alt = sum(1 for i in imgs if "alt=" not in i)

    def mark(b):
        return "✓" if b else "✗"

    print(
        f"{name:<32} "
        f"{mark(has_title):<6} "
        f"{mark(has_desc):<6} "
        f"{mark(has_canon):<6} "
        f"{mark(has_og):<5} "
        f"{ld_count:<5} "
        f"{robots:<7} "
        f"{h1_count:<4} "
        f"{mark(no_alt == 0)}"
    )

    # 记录问题
    if not has_title:
        issues.append(f"{name}: 缺 title")
    if not has_desc:
        issues.append(f"{name}: 缺 description")
    if not has_canon:
        issues.append(f"{name}: 缺 canonical")
    if not has_og:
        issues.append(f"{name}: 缺 OG")

    # 【JSON-LD 只要求可索引页面】
    # noindex 的页面搜索引擎不收录，加结构化数据没意义
    if not has_ld and robots != "noindex":
        issues.append(f"{name}: 缺 JSON-LD")

    if robots == "无":
        issues.append(f"{name}: 缺 robots 指令")
    if h1_count != 1:
        issues.append(f"{name}: h1 数量是 {h1_count}（应为 1）")
    if no_alt > 0:
        issues.append(f"{name}: {no_alt} 个 img 没有 alt")


# ══════════════════════════════════════════════════════════
# 2. title / description 唯一性
# ══════════════════════════════════════════════════════════
print("\n【title / description 唯一性】")

title_counter = Counter(t for _, t in titles)
dup_titles = {t: n for t, n in title_counter.items() if n > 1}
if dup_titles:
    for t, n in dup_titles.items():
        print(f"  ✗ title 重复 {n} 次: {t}")
        issues.append(f"title 重复: {t}")
else:
    print(f"  ✓ {len(titles)} 个 title 全部唯一")

desc_counter = Counter(d for _, d in descriptions)
dup_descs = {d: n for d, n in desc_counter.items() if n > 1}
if dup_descs:
    for d, n in dup_descs.items():
        print(f"  ✗ description 重复 {n} 次: {d[:40]}...")
        issues.append("description 重复")
else:
    print(f"  ✓ {len(descriptions)} 个 description 全部唯一")


# ══════════════════════════════════════════════════════════
# 3. title / description 长度
# ══════════════════════════════════════════════════════════
print("\n【长度检查】")

long_titles = [(n, t, len(t)) for n, t in titles if len(t) > 30]
if long_titles:
    for n, t, l in long_titles:
        print(f"  ⚠ {n}: title {l} 字（建议 ≤30）")
else:
    print(f"  ✓ title 长度都在 30 字以内")

short_descs = [(n, len(d)) for n, d in descriptions if len(d) < 50]
long_descs = [(n, len(d)) for n, d in descriptions if len(d) > 160]

# 【只对可索引页面提要求】
# noindex 页面的 description 短一点没关系（反正不展示在搜索结果里）
if short_descs:
    for n, l in short_descs:
        c = (FRONTEND / n).read_text(encoding="utf-8")
        if "noindex" not in c:
            print(f"  ⚠ {n}: description {l} 字（建议 50-160）")
if long_descs:
    for n, l in long_descs:
        print(f"  ⚠ {n}: description {l} 字（建议 50-160）")
if not short_descs and not long_descs:
    print(f"  ✓ description 长度都在 50-160 字")


# ══════════════════════════════════════════════════════════
# 4. JSON-LD 有效性
# ══════════════════════════════════════════════════════════
print("\n【JSON-LD 结构】")

ld_types = Counter()
ld_errors = []

for f in html_files:
    c = f.read_text(encoding="utf-8")
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', c, re.DOTALL):
        try:
            data = json.loads(m.group(1))
            t = data.get("@type", "?")
            ld_types[t] += 1
        except json.JSONDecodeError as e:
            ld_errors.append(f"{f.name}: JSON 格式错误 {e}")

if ld_errors:
    for e in ld_errors:
        print(f"  ✗ {e}")
        issues.append(e)
else:
    print("  ✓ 所有 JSON-LD 格式正确")

print(f"\n  使用的 schema 类型：")
for t, n in ld_types.most_common():
    print(f"    {t:<20} {n} 处")


# ══════════════════════════════════════════════════════════
# 5. 站点文件
# ══════════════════════════════════════════════════════════
print("\n【站点文件】")

for fname in ["robots.txt", "sitemap.xml", "llms.txt"]:
    p = FRONTEND / fname
    if p.exists():
        size = p.stat().st_size
        print(f"  ✓ {fname:<16} {size} 字节")
    else:
        print(f"  ✗ {fname} 不存在")
        issues.append(f"{fname} 不存在")


# ══════════════════════════════════════════════════════════
# 6. sitemap 内容检查
# ══════════════════════════════════════════════════════════
print("\n【sitemap 内容】")

sitemap = (FRONTEND / "sitemap.xml").read_text(encoding="utf-8")
urls = re.findall(r"<loc>([^<]+)</loc>", sitemap)
print(f"  URL 总数: {len(urls)}")

# 检查是否有 noindex 页面混进来
noindex_pages = ["admin", "cart", "checkout", "pay", "order-", "address", "after-sale", "login", "search"]
bad_urls = [u for u in urls if any(p in u for p in noindex_pages)]
if bad_urls:
    for u in bad_urls:
        print(f"  ✗ sitemap 含 noindex 页面: {u}")
        issues.append(f"sitemap 含 {u}")
else:
    print("  ✓ 没有 noindex 页面混进 sitemap")


# ══════════════════════════════════════════════════════════
# 7. 语义化标签
# ══════════════════════════════════════════════════════════
print("\n【语义化标签】")

semantic_stats = Counter()
for f in html_files:
    c = f.read_text(encoding="utf-8")
    for tag in ["header", "nav", "main", "footer", "article", "section"]:
        if f"<{tag}" in c:
            semantic_stats[tag] += 1

for tag in ["header", "nav", "main", "footer", "article", "section"]:
    n = semantic_stats.get(tag, 0)
    mark = "✓" if n > 0 else "-"
    print(f"  {mark} <{tag}>  用在 {n} 个页面")


# ══════════════════════════════════════════════════════════
# 汇总
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 70)
if issues:
    print(f"  发现 {len(issues)} 个问题：")
    print("=" * 70)
    for i in issues:
        print(f"  • {i}")
else:
    print("  SEO / GEO 检查全部通过")
    print("=" * 70)
