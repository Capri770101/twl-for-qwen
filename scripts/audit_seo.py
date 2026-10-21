# -*- coding: utf-8 -*-
"""
SEO / GEO 综合测评

【测什么】
1. 爬虫可读性（crawlability）
2. meta 唯一性（title / description / canonical）
3. 结构化数据（JSON-LD 语义完整性）
4. 内容质量（字数、FAQ、关键词位置）
5. 站点文件（sitemap / llms.txt 是否包含所有内容）
6. 内链

【输出】
分项得分 + 总分 + 待修项
"""

import json
import re
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000"
ROOT = Path(__file__).resolve().parent.parent
FE = ROOT / "frontend"

scores = {}
issues = []


def fetch(path: str) -> str:
    try:
        with urllib.request.urlopen(f"{BASE}{path}", timeout=10) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"__ERR__{e}"


def line(title: str):
    print()
    print("─" * 66)
    print(f"  {title}")
    print("─" * 66)


# ══════════════════════════════════════════════════════════
# 1. 爬虫可读性
# ══════════════════════════════════════════════════════════
line("1. 爬虫可读性")

CRAWL_TESTS = [
    ("首页", "/", ["跳舞兰"]),
    ("商城", "/shop.html", ["晨光序曲"]),
    ("商品详情", "/product.html?id=TW-001", ["晨光序曲", "299"]),
    ("花语列表", "/flower-language.html", ["白玫瑰"]),
    ("花语详情", "/flower-language-detail.html?slug=white-rose", ["白玫瑰", "纯洁"]),
    ("关于", "/about.html", ["跳舞兰"]),
    ("FAQ", "/help-faq.html", ["登录"]),
]

crawl_ok = 0
for name, path, must in CRAWL_TESTS:
    html = fetch(path)
    body = re.sub(r"<script.*?</script>", "", html, flags=re.DOTALL)
    body = re.sub(r"<style.*?</style>", "", body, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", body)
    text = re.sub(r"\s+", " ", text)

    if all(k in text for k in must):
        crawl_ok += 1
        print(f"  ✓ {name}")
    else:
        print(f"  ✗ {name}（缺 {[k for k in must if k not in text]}）")
        issues.append(f"{name} 内容爬不到")

scores["爬虫可读性"] = (crawl_ok, len(CRAWL_TESTS))


# ══════════════════════════════════════════════════════════
# 2. meta 唯一性
# ══════════════════════════════════════════════════════════
line("2. meta 唯一性（动态页面必须每个都不同）")

# 文章详情
articles = ["white-rose", "sunflower", "gift-for-mom", "rose-care", "champagne-rose"]
titles = set()
descs = set()
canons = set()

for slug in articles:
    html = fetch(f"/flower-language-detail.html?slug={slug}")
    t = re.search(r"<title>([^<]+)</title>", html)
    d = re.search(r'<meta name="description" content="([^"]*)"', html)
    c = re.search(r'<link rel="canonical" href="([^"]+)"', html)

    if t:
        titles.add(t.group(1))
    if d:
        descs.add(d.group(1))
    if c:
        canons.add(c.group(1))

print(f"  {len(articles)} 篇文章：")
print(f"    title 唯一:      {len(titles)} / {len(articles)}")
print(f"    description 唯一: {len(descs)} / {len(articles)}")
print(f"    canonical 唯一:   {len(canons)} / {len(articles)}")

meta_score = min(len(titles), len(descs), len(canons))
scores["文章 meta 唯一"] = (meta_score, len(articles))

if meta_score < len(articles):
    issues.append("文章 meta 有重复")

# 商品详情
products = ["TW-001", "TW-002", "TW-003"]
ptitles = set()
pcanons = set()
for pid in products:
    html = fetch(f"/product.html?id={pid}")
    t = re.search(r"<title>([^<]+)</title>", html)
    c = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    if t:
        ptitles.add(t.group(1))
    if c:
        pcanons.add(c.group(1))

print(f"  {len(products)} 个商品：")
print(f"    title 唯一:    {len(ptitles)} / {len(products)}")
print(f"    canonical 唯一: {len(pcanons)} / {len(products)}")


# ══════════════════════════════════════════════════════════
# 3. 结构化数据
# ══════════════════════════════════════════════════════════
line("3. 结构化数据（JSON-LD）")

ld_types = {}
ld_errors = []

for slug in articles:
    html = fetch(f"/flower-language-detail.html?slug={slug}")
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL):
        try:
            data = json.loads(m.group(1))
            t = data.get("@type", "?")
            ld_types[t] = ld_types.get(t, 0) + 1

            # 语义完整性检查
            if t == "Article":
                for field in ["headline", "description", "url"]:
                    if not data.get(field):
                        ld_errors.append(f"{slug}: Article 缺 {field}")
            elif t == "FAQPage":
                if not data.get("mainEntity"):
                    ld_errors.append(f"{slug}: FAQPage 没有 mainEntity")

        except json.JSONDecodeError as e:
            ld_errors.append(f"{slug}: JSON 格式错误 {e}")

# 商品页
for pid in products:
    html = fetch(f"/product.html?id={pid}")
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL):
        try:
            data = json.loads(m.group(1))
            t = data.get("@type", "?")
            ld_types[t] = ld_types.get(t, 0) + 1

            if t == "Product":
                for field in ["name", "offers"]:
                    if not data.get(field):
                        ld_errors.append(f"{pid}: Product 缺 {field}")
                if data.get("offers") and not data["offers"].get("price"):
                    ld_errors.append(f"{pid}: Product offers 缺 price")
        except json.JSONDecodeError as e:
            ld_errors.append(f"{pid}: JSON 格式错误 {e}")

print("  schema 分布：")
for t, n in sorted(ld_types.items(), key=lambda x: -x[1]):
    print(f"    {t:<18} {n} 处")

if ld_errors:
    print(f"\n  ✗ {len(ld_errors)} 个语义问题：")
    for e in ld_errors[:5]:
        print(f"    {e}")
    issues.extend(ld_errors[:3])
    scores["结构化数据"] = (len(ld_types) - len(set(ld_errors)), len(ld_types))
else:
    print("\n  ✓ 语义完整性全部通过")
    scores["结构化数据"] = (len(ld_types), len(ld_types))


# ══════════════════════════════════════════════════════════
# 4. 内容质量
# ══════════════════════════════════════════════════════════
line("4. 内容质量")

content_dir = ROOT / "content"
md_files = [f for f in content_dir.rglob("*.md") if f.name not in ("README.md", "选题清单.md")]

print(f"  {'文件':<28} {'字数':>6} {'FAQ':>5} {'一句话答案':>10}")
print(f"  {'─'*28} {'─'*6} {'─'*5} {'─'*10}")

quality_ok = 0
for f in md_files:
    text = f.read_text(encoding="utf-8")

    # 字数（去 frontmatter）
    body = re.sub(r"^---.*?---", "", text, flags=re.DOTALL).strip()
    wc = len(re.sub(r"\s", "", body))

    # FAQ 数
    faq_count = len(re.findall(r"^### ", body, re.MULTILINE))

    # 一句话答案：正文第一段是否包含「是」或「：」
    first_para = body.split("\n\n")[0] if body else ""
    has_answer = ("是" in first_para) or ("：" in first_para) or ("**" in first_para)

    mark = "✓" if (wc >= 800 and faq_count >= 3 and has_answer) else "✗"
    if mark == "✓":
        quality_ok += 1

    print(f"  {mark} {f.name:<26} {wc:>6} {faq_count:>5} {'有' if has_answer else '无':>10}")

scores["内容质量"] = (quality_ok, len(md_files))

if quality_ok < len(md_files):
    issues.append(f"{len(md_files)-quality_ok} 篇内容未达标准")


# ══════════════════════════════════════════════════════════
# 5. 站点文件完整性
# ══════════════════════════════════════════════════════════
line("5. 站点文件完整性")

# sitemap 是否包含所有文章
sm = (FE / "sitemap.xml").read_text(encoding="utf-8")
sm_urls = re.findall(r"<loc>([^<]+)</loc>", sm)

missing_in_sitemap = []
for slug in articles:
    if not any(slug in u for u in sm_urls):
        missing_in_sitemap.append(slug)

for pid in products:
    if not any(pid in u for u in sm_urls):
        missing_in_sitemap.append(pid)

print(f"  sitemap.xml    {len(sm_urls)} 个 URL")

if missing_in_sitemap:
    print(f"  ✗ 缺 {len(missing_in_sitemap)} 个：{missing_in_sitemap[:5]}")
    issues.append("sitemap 缺内容")
    scores["sitemap"] = (len(sm_urls) - len(missing_in_sitemap), len(sm_urls))
else:
    print(f"  ✓ 所有文章和商品都在")
    scores["sitemap"] = (len(sm_urls), len(sm_urls))

# llms.txt
llms = (FE / "llms.txt").read_text(encoding="utf-8")
llms_missing = [slug for slug in articles if slug not in llms]
print(f"  llms.txt       {len(llms)} 字符")

if llms_missing:
    print(f"  ✗ 缺 {len(llms_missing)} 篇：{llms_missing}")
    issues.append("llms.txt 缺文章")
    scores["llms.txt"] = (len(articles) - len(llms_missing), len(articles))
else:
    print(f"  ✓ 所有文章都在")
    scores["llms.txt"] = (len(articles), len(articles))

# robots
rb = (FE / "robots.txt").read_text(encoding="utf-8")
has_sitemap = "Sitemap:" in rb
has_disallow = "Disallow:" in rb
print(f"  robots.txt     {len(rb)} 字符，{'有' if has_sitemap else '缺'} sitemap 指向，{'有' if has_disallow else '缺'} 禁止规则")


# ══════════════════════════════════════════════════════════
# 6. 内链
# ══════════════════════════════════════════════════════════
line("6. 内链")

internal_links = 0
for f in md_files:
    text = f.read_text(encoding="utf-8")
    body = re.sub(r"^---.*?---", "", text, flags=re.DOTALL)
    # Markdown 链接
    links = re.findall(r'\[([^\]]+)\]\(([^)]+\.html[^)]*)\)', body)
    if links:
        internal_links += len(links)
        print(f"  {f.name}: {len(links)} 个内链")
    else:
        print(f"  {f.name}: 0 个内链")

if internal_links == 0:
    issues.append("内容里没有内链到商品或其他文章")
    scores["内链"] = (0, len(md_files))
else:
    scores["内链"] = (min(internal_links, len(md_files)), len(md_files))


# ══════════════════════════════════════════════════════════
# 汇总
# ══════════════════════════════════════════════════════════
line("总评")

total_got = 0
total_max = 0

for k, (got, mx) in scores.items():
    pct = (got / mx * 100) if mx else 0
    bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
    print(f"  {k:<16} {bar} {got}/{mx}  {pct:.0f}%")
    total_got += got
    total_max += mx

overall = (total_got / total_max * 100) if total_max else 0

print()
print(f"  总分  {overall:.0f}%")

if issues:
    print()
    print("  待修：")
    for i in issues:
        print(f"    • {i}")
else:
    print()
    print("  ✓ 全部通过")

print()
print("═" * 66)
