# -*- coding: utf-8 -*-
"""
服务端渲染（SSR）

【为什么需要这个】
前端页面是纯静态 HTML + JS 动态渲染。
搜索引擎爬虫不执行 JS，所以看到的是空壳 —— 商品名、文章正文都读不到。

实测结果：
    商城        ✗ 读不到商品
    商品详情    ✗ 读不到商品
    花语列表    ✗ 读不到文章
    花语详情    ✗ 读不到正文

【解决思路】
后端给这几个页面加 SSR 路由：
    1. 读静态 HTML 模板
    2. 查数据库
    3. 把内容渲染成 HTML 片段，替换到容器里
    4. 返回完整 HTML

用户访问时：
    - 爬虫：直接读到完整内容 ✓
    - 浏览器：先看到 SSR 内容，JS 加载后接管交互 ✓

【为什么不用 Jinja2】
页面是已经写好的静态 HTML，只需要往几个容器里塞内容。
用字符串替换比引入模板引擎更简单，也不用改现有 HTML 结构。
"""

import html as html_lib
from decimal import Decimal
from pathlib import Path

from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.content import Article
from app.models.product import Product, ProductStatus

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent.parent / "frontend"


# ══════════════════════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════════════════════

def esc(s) -> str:
    """HTML 转义"""
    if s is None:
        return ""
    return html_lib.escape(str(s))


def money(v) -> str:
    """价格格式化：299.00 → 299，299.50 → 299.50"""
    if v is None:
        return "0"
    d = Decimal(str(v))
    if d == d.to_integral():
        return str(int(d))
    return f"{d:.2f}"


def read_template(name: str) -> str | None:
    """读前端模板文件"""
    p = FRONTEND_DIR / name
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8")


# ══════════════════════════════════════════════════════════
# 动态 meta 注入
#
# 【为什么需要】
# 花语详情页和商品页是同一个 HTML 模板，
# 如果不改 meta，所有文章/商品的 title 都是一样的 ——
# 搜索引擎会认为这些是重复内容，等于没收录。
#
# 【替换什么】
#   title / description / canonical / OG / Twitter / JSON-LD
# ══════════════════════════════════════════════════════════

SITE = "https://h5.tiaowulan.com"


def inject_meta(
    html: str,
    *,
    title: str,
    description: str,
    url: str,
    image: str = "",
    og_type: str = "article",
    jsonld: dict | None = None,
    keywords: str = "",
) -> str:
    """
    【干什么】把模板里的 meta 换成这篇文章/商品专属的。

    【怎么替换】
    用正则匹配现有的标签，整条换掉。
    这样不用管原来的内容是什么。
    """
    import json as _json
    import re as _re

    # ── title ──
    html = _re.sub(
        r"<title>[^<]*</title>",
        f"<title>{esc(title)}</title>",
        html,
        count=1,
    )

    # ── description ──
    html = _re.sub(
        r'<meta name="description" content="[^"]*">',
        f'<meta name="description" content="{esc(description)}">',
        html,
        count=1,
    )

    # ── keywords（有就换）──
    if keywords:
        html = _re.sub(
            r'<meta name="keywords" content="[^"]*">',
            f'<meta name="keywords" content="{esc(keywords)}">',
            html,
            count=1,
        )

    # ── canonical ──
    html = _re.sub(
        r'<link rel="canonical" href="[^"]*">',
        f'<link rel="canonical" href="{esc(url)}">',
        html,
        count=1,
    )

    # ── OG ──
    html = _re.sub(
        r'<meta property="og:type" content="[^"]*">',
        f'<meta property="og:type" content="{og_type}">',
        html,
        count=1,
    )
    html = _re.sub(
        r'<meta property="og:title" content="[^"]*">',
        f'<meta property="og:title" content="{esc(title)}">',
        html,
        count=1,
    )
    html = _re.sub(
        r'<meta property="og:description" content="[^"]*">',
        f'<meta property="og:description" content="{esc(description)}">',
        html,
        count=1,
    )
    html = _re.sub(
        r'<meta property="og:url" content="[^"]*">',
        f'<meta property="og:url" content="{esc(url)}">',
        html,
        count=1,
    )
    if image:
        html = _re.sub(
            r'<meta property="og:image" content="[^"]*">',
            f'<meta property="og:image" content="{esc(image)}">',
            html,
            count=1,
        )

    # ── Twitter ──
    html = _re.sub(
        r'<meta name="twitter:title" content="[^"]*">',
        f'<meta name="twitter:title" content="{esc(title)}">',
        html,
        count=1,
    )
    html = _re.sub(
        r'<meta name="twitter:description" content="[^"]*">',
        f'<meta name="twitter:description" content="{esc(description)}">',
        html,
        count=1,
    )

    # ── JSON-LD（替换 Article / Product 那个）──
    if jsonld:
        new_ld = (
            '<script type="application/ld+json">\n'
            + _json.dumps(jsonld, ensure_ascii=False, indent=2)
            + "\n</script>"
        )
        # 只换 @type 是 Article 或 Product 的
        def _replace_ld(m):
            block = m.group(0)
            inner = m.group(1)
            try:
                data = _json.loads(inner)
            except Exception:
                return block
            if data.get("@type") in ("Article", "Product"):
                return new_ld
            return block

        html = _re.sub(
            r'<script type="application/ld\+json">(.*?)</script>',
            _replace_ld,
            html,
            flags=_re.DOTALL,
        )

    return html



# ══════════════════════════════════════════════════════════
# 商城页
# ══════════════════════════════════════════════════════════

def render_shop_card(p: Product) -> str:
    """渲染一个商品卡片（和前端 JS 的模板保持一致）"""
    cover = esc(p.cover or "")
    name = esc(p.name)
    price = money(p.price)

    orig = ""
    if p.original_price and Decimal(str(p.original_price)) > Decimal(str(p.price)):
        orig = f'<span class="was">¥{money(p.original_price)}</span>'

    return (
        f'<a href="product.html?id={esc(p.id)}" class="card">'
        f'<div class="pic"><img src="{cover}" alt="{name}" loading="lazy"></div>'
        f'<div class="info"><h3>{name}</h3>'
        f'<div class="price">¥{price}{orig}</div></div>'
        f"</a>"
    )


async def render_shop(db: AsyncSession) -> str | None:
    """商城页 SSR"""
    tpl = read_template("shop.html")
    if not tpl:
        return None

    result = await db.execute(
        select(Product)
        .where(Product.status == ProductStatus.ON.value)
        .order_by(Product.sort_order, Product.created_at)
    )
    products = result.scalars().all()

    cards = "".join(render_shop_card(p) for p in products)

    # 替换 grid 内容（保留 id 和 class，去掉「加载中」）
    tpl = tpl.replace(
        '<div class="grid" id="grid">',
        f'<div class="grid" id="grid">{cards}',
        1,
    )
    tpl = tpl.replace(
        '<span class="count" id="totalCount">加载中…</span>',
        f'<span class="count" id="totalCount">{len(products)} 件商品</span>',
        1,
    )
    return tpl


# ══════════════════════════════════════════════════════════
# 商品详情页
# ══════════════════════════════════════════════════════════

async def render_product(db: AsyncSession, product_id: str) -> str | None:
    """商品详情页 SSR"""
    tpl = read_template("product.html")
    if not tpl:
        return None

    result = await db.execute(select(Product).where(Product.id == product_id))
    p = result.scalar_one_or_none()

    if not p:
        # 商品不存在：给个友好的 404 内容
        tpl = tpl.replace(
            '<div class="loading" id="loading">加载中…</div>',
            '<div style="padding:120px 40px;text-align:center;color:#999">'
            '<div style="font-size:18px;margin-bottom:12px">这个花束不存在或已下架</div>'
            '<a href="shop.html" style="color:#1a1a1a;text-decoration:underline">看看其他花束 →</a>'
            "</div>",
            1,
        )
        return tpl

    # 花材清单
    flowers_html = ""
    if p.flowers:
        flowers_html = "".join(f"<li>{esc(f)}</li>" for f in p.flowers)

    content = f"""
<div class="pd-wrap">
  <div class="pd-pic">
    <img src="{esc(p.cover or '')}" alt="{esc(p.name)}">
  </div>
  <div class="pd-info">
    <div class="pd-crumb"><a href="index.html">首页</a> / <a href="shop.html">全部花束</a> / {esc(p.name)}</div>
    <h2>{esc(p.name)}</h2>
    <div class="pd-sub">{esc(p.subtitle or '')}</div>
    <div class="pd-price">¥{money(p.price)}</div>
    <div class="pd-meaning">{esc(p.meaning or '')}</div>
    <div class="pd-block">
      <h3>花材</h3>
      <ul class="pd-flowers">{flowers_html}</ul>
    </div>
    <div class="pd-block">
      <h3>配送</h3>
      <p>配送范围与时效以结算页为准。</p>
    </div>
  </div>
</div>
"""

    tpl = tpl.replace(
        '<div class="loading" id="loading">加载中…</div>',
        content,
        1,
    )

    # ── 动态 meta ──
    seo_title = f"{p.name} - {p.subtitle or '花束'} | 跳舞兰"
    seo_desc = (
        f"{p.name}：{p.subtitle or ''}。{p.meaning or ''} "
        f"¥{money(p.price)} 起。含花材清单与养护方法。"
    ).replace("  ", " ").strip()

    jsonld = {
        "@context": "https://schema.org",
        "@type": "Product",
        "@id": f"{SITE}/product.html?id={p.id}#product",
        "name": p.name,
        "description": p.meaning or p.subtitle or "",
        "image": f"{SITE}{p.cover}" if p.cover else "",
        "sku": p.id,
        "brand": {"@type": "Brand", "name": "跳舞兰"},
        "category": p.category,
        "offers": {
            "@type": "Offer",
            "price": str(Decimal(str(p.price))),
            "priceCurrency": "CNY",
            "availability": "https://schema.org/InStock",
            "url": f"{SITE}/product.html?id={p.id}",
            "seller": {"@id": f"{SITE}/#organization"},
        },
    }

    tpl = inject_meta(
        tpl,
        title=seo_title,
        description=seo_desc[:160],
        url=f"{SITE}/product.html?id={p.id}",
        image=f"{SITE}{p.cover}" if p.cover else "",
        og_type="product",
        jsonld=jsonld,
        keywords=f"{p.name},{p.category},鲜花,花束",
    )

    return tpl


# ══════════════════════════════════════════════════════════
# 花语列表页
# ══════════════════════════════════════════════════════════

def render_article_card(a: Article) -> str:
    """渲染一篇文章卡片"""
    cover = esc(a.cover or "")
    title = esc(a.title)
    meaning = esc(a.meaning or "")
    category = esc(a.category or "")

    return (
        f'<a href="flower-language-detail.html?slug={esc(a.slug)}" class="item" data-cat="{category}">'
        f'<div class="thumb"><img src="{cover}" alt="{title}" loading="lazy"></div>'
        f'<div class="txt"><h3>{title}</h3>'
        f'<div class="mean">{meaning}</div></div>'
        f"</a>"
    )


async def render_flower_list(db: AsyncSession) -> str | None:
    """花语列表页 SSR"""
    tpl = read_template("flower-language.html")
    if not tpl:
        return None

    result = await db.execute(
        select(Article)
        .where(Article.status == "published")
        .order_by(Article.sort_weight.desc(), Article.created_at.desc())
    )
    articles = result.scalars().all()

    cards = "".join(render_article_card(a) for a in articles)

    tpl = tpl.replace(
        '<div class="list" id="list">',
        f'<div class="list" id="list">{cards}',
        1,
    )
    tpl = tpl.replace(
        '<div class="count" id="count">加载中…</div>',
        f'<div class="count" id="count">{len(articles)} 篇</div>',
        1,
    )
    return tpl


# ══════════════════════════════════════════════════════════
# 花语详情页
# ══════════════════════════════════════════════════════════

def markdown_to_html(md: str) -> str:
    """
    【干什么】把 Markdown 转成 HTML

    【支持什么】
        ## 二级标题
        ### 三级标题
        **粗体**
        [文字](链接)
        段落
        无序列表（- 开头）
        表格（简单支持）

    【为什么不引 markdown 库】
    内容格式很固定，自己写够了，还能控制输出的语义化程度。
    """
    import re

    lines = md.split("\n")
    out = []
    in_list = False
    in_table = False

    for line in lines:
        s = line.rstrip()

        # 空行
        if not s:
            if in_list:
                out.append("</ul>")
                in_list = False
            if in_table:
                out.append("</tbody></table>")
                in_table = False
            continue

        # 表格
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            # 分隔行 |---|---|
            if all(re.match(r"^:?-+:?$", c) for c in cells if c):
                continue
            if not in_table:
                out.append('<table class="tbl"><tbody>')
                in_table = True
            row = "".join(f"<td>{_inline(c)}</td>" for c in cells)
            out.append(f"<tr>{row}</tr>")
            continue
        elif in_table:
            out.append("</tbody></table>")
            in_table = False

        # 标题
        if s.startswith("### "):
            out.append(f"<h3>{_inline(s[4:])}</h3>")
            continue
        if s.startswith("## "):
            out.append(f"<h2>{_inline(s[3:])}</h2>")
            continue
        if s.startswith("# "):
            out.append(f"<h2>{_inline(s[2:])}</h2>")
            continue

        # 列表
        if s.startswith("- "):
            if not in_list:
                out.append('<ul class="ul">')
                in_list = True
            out.append(f"<li>{_inline(s[2:])}</li>")
            continue
        elif in_list:
            out.append("</ul>")
            in_list = False

        # 段落
        out.append(f"<p>{_inline(s)}</p>")

    if in_list:
        out.append("</ul>")
    if in_table:
        out.append("</tbody></table>")

    return "\n".join(out)


def _inline(s: str) -> str:
    """行内格式：粗体、链接"""
    import re

    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


async def render_flower_detail(db: AsyncSession, slug: str) -> str | None:
    """花语详情页 SSR"""
    tpl = read_template("flower-language-detail.html")
    if not tpl:
        return None

    result = await db.execute(select(Article).where(Article.slug == slug))
    a = result.scalar_one_or_none()

    if not a:
        tpl = tpl.replace(
            '<div class="art-wrap" id="app">',
            '<div class="art-wrap" id="app"><div style="padding:120px 40px;text-align:center;color:#999">'
            '<div style="font-size:18px;margin-bottom:12px">这篇文章不存在</div>'
            '<a href="flower-language.html" style="color:#1a1a1a;text-decoration:underline">回到花语百科 →</a>'
            "</div>",
            1,
        )
        return tpl

    body_html = markdown_to_html(a.content or "")

    # FAQ
    faq_html = ""
    if a.faq:
        items = "".join(
            f'<div class="faq-item"><h3>{esc(f.get("question", ""))}</h3>'
            f'<div class="faq-a">{esc(f.get("answer", ""))}</div></div>'
            for f in a.faq
        )
        faq_html = f'<section class="faq-sec"><h2>常见问题</h2>{items}</section>'

    content = f"""
<article class="art">
  <div class="art-crumb"><a href="index.html">首页</a> / <a href="flower-language.html">花语百科</a> / {esc(a.title)}</div>
  <h1>{esc(a.title)}</h1>
  <div class="art-mean">{esc(a.meaning or '')}</div>
  <div class="art-body">
    {body_html}
  </div>
  {faq_html}
</article>
"""

    tpl = tpl.replace(
        '<div class="art-wrap" id="app">',
        f'<div class="art-wrap" id="app">{content}',
        1,
    )

    # ── 动态 meta ──
    seo_title = a.seo_title or f"{a.title} | 跳舞兰"
    seo_desc = a.seo_description or a.summary or (a.content or "")[:150]

    # 正文前 120 字做 description（去掉 Markdown 标记）
    import re as _re
    plain = _re.sub(r"[#*\[\]()>`|-]", "", a.content or "")
    plain = _re.sub(r"\s+", " ", plain).strip()
    if not a.seo_description and len(plain) > 50:
        seo_desc = plain[:150] + "…"

    jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "@id": f"{SITE}/flower-language-detail.html?slug={a.slug}#article",
        "headline": a.title,
        "description": seo_desc,
        "url": f"{SITE}/flower-language-detail.html?slug={a.slug}",
        "image": f"{SITE}{a.cover}" if a.cover else "",
        "author": {"@id": f"{SITE}/#organization"},
        "publisher": {"@id": f"{SITE}/#organization"},
        "isPartOf": {"@id": f"{SITE}/#website"},
        "inLanguage": "zh-CN",
        "articleSection": a.category or "",
        "keywords": ", ".join(a.tags) if a.tags else "",
    }

    tpl = inject_meta(
        tpl,
        title=seo_title,
        description=(seo_desc or "")[:160],
        url=f"{SITE}/flower-language-detail.html?slug={a.slug}",
        image=f"{SITE}{a.cover}" if a.cover else "",
        og_type="article",
        jsonld=jsonld,
        keywords=", ".join(a.tags) if a.tags else "",
    )

    # ── FAQ 结构化数据 ──
    if a.faq:
        faq_ld = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": f.get("question", ""),
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": f.get("answer", ""),
                    },
                }
                for f in a.faq
            ],
        }
        import json as _json
        faq_block = (
            '<script type="application/ld+json">\n'
            + _json.dumps(faq_ld, ensure_ascii=False, indent=2)
            + "\n</script>\n</head>"
        )
        tpl = tpl.replace("</head>", faq_block, 1)

    return tpl
