# -*- coding: utf-8 -*-
"""
批量注入 SEO / GEO 元信息
给每个页面加：meta / canonical / OG / Twitter Card / JSON-LD

【怎么用】
    cd scripts
    python apply_seo.py

【改什么】
编辑 seo_config.py 里的配置，然后重跑这个脚本。

【注意】
重复跑不会重复插入（会先删掉旧的 SEO 块）。
"""

import json
import os
import re
from pathlib import Path

from seo_config import (
    BRAND, BRAND_EN, BRAND_FULL, CITY, COUNTRY, EMAIL, HOURS,
    OG_IMAGE, PAGES, PHONE, PROVINCE, SITE, SLOGAN,
)

# 脚本在 scripts/ 下，上一级是项目根
ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"


# ══════════════════════════════════════════════════════════
# JSON-LD 生成
# ══════════════════════════════════════════════════════════

def schema_florist() -> dict:
    """首页：花店 + 本地商家"""
    return {
        "@context": "https://schema.org",
        "@type": "Florist",
        "@id": f"{SITE}/#florist",
        "name": BRAND,
        "alternateName": BRAND_EN,
        "legalName": BRAND_FULL,
        "url": SITE,
        "logo": f"{SITE}/images/01_chenguang.png",
        "image": OG_IMAGE,
        "description": "深圳的花艺团队。当日现做花束，深圳同城 2 小时达，全国 200+ 城市次日达。",
        "telephone": PHONE,
        "email": EMAIL,
        "priceRange": "¥199-¥999",
        "currenciesAccepted": "CNY",
        "paymentAccepted": "微信支付, 支付宝, 银行卡",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": CITY,
            "addressRegion": PROVINCE,
            "addressCountry": COUNTRY,
        },
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": "22.5431",
            "longitude": "114.0579",
        },
        "openingHoursSpecification": {
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "opens": "09:00",
            "closes": "21:00",
        },
        "areaServed": [
            {"@type": "City", "name": "深圳市"},
            {"@type": "Country", "name": "中国"},
        ],
        "sameAs": [],
    }


def schema_website() -> dict:
    """首页：网站"""
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "@id": f"{SITE}/#website",
        "url": SITE,
        "name": BRAND,
        "description": "深圳的花艺团队。当日现做花束，深圳同城 2 小时达。",
        "publisher": {"@id": f"{SITE}/#florist"},
        "inLanguage": "zh-CN",
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": f"{SITE}/search.html?q={{search_term_string}}",
            },
            "query-input": "required name=search_term_string",
        },
    }


def schema_organization() -> dict:
    """组织"""
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": f"{SITE}/#organization",
        "name": BRAND_FULL,
        "alternateName": BRAND,
        "url": SITE,
        "logo": f"{SITE}/images/01_chenguang.png",
        "email": EMAIL,
        "telephone": PHONE,
        "foundingLocation": {"@type": "Place", "name": CITY},
        "slogan": SLOGAN,
    }


def schema_breadcrumb(page: str, name: str, parent: list | None = None) -> dict:
    """面包屑"""
    items = [
        {"@type": "ListItem", "position": 1, "name": "首页", "item": f"{SITE}/"},
    ]
    pos = 2

    if parent:
        for p_name, p_url in parent:
            items.append({
                "@type": "ListItem",
                "position": pos,
                "name": p_name,
                "item": p_url,
            })
            pos += 1

    items.append({
        "@type": "ListItem",
        "position": pos,
        "name": name,
        "item": f"{SITE}{page}",
    })

    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }


def schema_collection(name: str, desc: str, page: str) -> dict:
    """集合页（商城、花语列表）"""
    return {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "@id": f"{SITE}{page}#page",
        "name": name,
        "description": desc,
        "url": f"{SITE}{page}",
        "isPartOf": {"@id": f"{SITE}/#website"},
        "inLanguage": "zh-CN",
    }


def schema_webpage(name: str, desc: str, page: str) -> dict:
    """普通网页（帮助页）"""
    return {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "@id": f"{SITE}{page}#page",
        "name": name,
        "description": desc,
        "url": f"{SITE}{page}",
        "isPartOf": {"@id": f"{SITE}/#website"},
        "inLanguage": "zh-CN",
    }


def schema_faq(entity: list[dict]) -> dict:
    """FAQ 页"""
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q["q"],
                "acceptedAnswer": {"@type": "Answer", "text": q["a"]},
            }
            for q in entity
        ],
    }


def schema_article(name: str, desc: str, page: str) -> dict:
    """文章页"""
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "@id": f"{SITE}{page}#article",
        "headline": name,
        "description": desc,
        "url": f"{SITE}{page}",
        "author": {"@id": f"{SITE}/#organization"},
        "publisher": {"@id": f"{SITE}/#organization"},
        "isPartOf": {"@id": f"{SITE}/#website"},
        "inLanguage": "zh-CN",
    }


def schema_product() -> dict:
    """商品页（基础版，具体商品由 JS 动态注入）"""
    return {
        "@context": "https://schema.org",
        "@type": "Product",
        "@id": f"{SITE}/product.html#product",
        "name": "跳舞兰花束",
        "description": "当日现做花束，含花材清单与养护方法。深圳同城 2 小时达。",
        "image": OG_IMAGE,
        "brand": {"@type": "Brand", "name": BRAND},
        "offers": {
            "@type": "Offer",
            "priceCurrency": "CNY",
            "availability": "https://schema.org/InStock",
            "url": f"{SITE}/product.html",
            "seller": {"@id": f"{SITE}/#organization"},
        },
    }


def schema_about() -> dict:
    """关于页"""
    return {
        "@context": "https://schema.org",
        "@type": "AboutPage",
        "@id": f"{SITE}/about.html#page",
        "name": f"关于{BRAND}",
        "description": "跳舞兰是深圳市跳舞兰科技有限公司旗下的花艺品牌。",
        "url": f"{SITE}/about.html",
        "mainEntity": {"@id": f"{SITE}/#organization"},
        "isPartOf": {"@id": f"{SITE}/#website"},
        "inLanguage": "zh-CN",
    }


def schema_contact() -> dict:
    """联系页"""
    return {
        "@context": "https://schema.org",
        "@type": "ContactPage",
        "@id": f"{SITE}/contact.html#page",
        "name": f"联系{BRAND}",
        "description": "跳舞兰联系方式与咨询入口。",
        "url": f"{SITE}/contact.html",
        "mainEntity": {"@id": f"{SITE}/#florist"},
        "isPartOf": {"@id": f"{SITE}/#website"},
        "inLanguage": "zh-CN",
    }


def schema_localbusiness() -> dict:
    """联系页的本地商家"""
    return {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "@id": f"{SITE}/#localbusiness",
        "name": BRAND,
        "legalName": BRAND_FULL,
        "url": SITE,
        "telephone": PHONE,
        "email": EMAIL,
        "image": OG_IMAGE,
        "address": {
            "@type": "PostalAddress",
            "addressLocality": CITY,
            "addressRegion": PROVINCE,
            "addressCountry": COUNTRY,
        },
        "openingHours": HOURS,
        "priceRange": "¥199-¥999",
    }


# ══════════════════════════════════════════════════════════
# FAQ 内容（帮助页用）
# ══════════════════════════════════════════════════════════

FAQ_DELIVERY = [
    {"q": "深圳送花多久能到？", "a": "深圳同城 2 小时达。当天 16:00 前下单当日送达，21:00 前下单次日达。"},
    {"q": "其他城市多久能到？", "a": "广州次日达，全国 200+ 城市顺丰冷链次日达，偏远地区 2-3 天。"},
    {"q": "运费怎么算？", "a": "满 ¥199 免运费，不满收 ¥15。偏远地区 ¥25 起。"},
    {"q": "能指定送达时间吗？", "a": "深圳同城可选两个时段：14:00-16:00 和 18:00-20:00。其他城市无法指定具体时段。"},
    {"q": "收花人不在怎么办？", "a": "配送员会电话联系。连续 3 次联系不上，订单退回并安排二次配送（需补配送费）。"},
]

FAQ_RETURNS = [
    {"q": "花有问题怎么办？", "a": "24 小时内拍照联系我们，支持补送或退款。客服 2 小时内响应。"},
    {"q": "什么情况可以退？", "a": "花材破损、不新鲜、与描述不符、配送延迟超 2 小时，都可以申请。"},
    {"q": "退款多久到账？", "a": "1-3 个工作日原路退回。"},
    {"q": "什么情况不能退？", "a": "送达超 24 小时才提出、没有照片无法核实、收花人自身原因（拒收/地址错误/联系不上）导致的损耗。"},
]

FAQ_GENERAL = [
    {"q": "最早什么时候能送到？", "a": "深圳 2 小时，其他城市次日。当天 16:00 前下单深圳当日送达。"},
    {"q": "能指定送达时间吗？", "a": "深圳可选时段（14:00-16:00、18:00-20:00），其他城市不能指定。"},
    {"q": "花是新鲜的吗？", "a": "每日云南直采，冷链到店，当日现做。不做隔夜花。"},
    {"q": "花能养几天？", "a": "含保鲜剂常温可养 5-7 天。每天换水、斜剪根部、避免暴晒可延长到 8-10 天。"},
    {"q": "必须登录才能买吗？", "a": "不用。游客也能下单，但只能在当前浏览器查单，无法在线申请售后。"},
    {"q": "游客订单能找回吗？", "a": "登录同一手机号后，系统会自动认领该手机号下的历史订单。"},
    {"q": "支持哪些支付方式？", "a": "微信支付、支付宝、银行卡。"},
    {"q": "可以开发票吗？", "a": "可以，联系客服提供开票信息。"},
]


# ══════════════════════════════════════════════════════════
# 生成 SEO 块
# ══════════════════════════════════════════════════════════

def build_seo_block(filename: str, cfg: dict) -> str:
    """生成要插入 <head> 的完整 SEO 块"""
    url = f"{SITE}/{filename}" if filename != "index.html" else f"{SITE}/"
    title = cfg.get("title", BRAND)
    desc = cfg.get("description", "")
    keywords = cfg.get("keywords", "")
    og_type = cfg.get("og_type", "website")
    should_index = cfg.get("index", True)

    parts = []

    # ── robots ──
    if should_index:
        parts.append('<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">')
    else:
        parts.append('<meta name="robots" content="noindex, nofollow">')

    # ── 基础 meta ──
    # description 必须有（搜索引擎摘要），和 og:description 内容一致
    if desc:
        parts.append(f'<meta name="description" content="{desc}">')
    if keywords:
        parts.append(f'<meta name="keywords" content="{keywords}">')

    parts.append(f'<link rel="canonical" href="{url}">')

    # ── Open Graph ──
    parts.append(f'<meta property="og:type" content="{og_type}">')
    parts.append(f'<meta property="og:site_name" content="{BRAND}">')
    parts.append(f'<meta property="og:locale" content="zh_CN">')
    parts.append(f'<meta property="og:title" content="{title}">')
    parts.append(f'<meta property="og:description" content="{desc}">')
    parts.append(f'<meta property="og:url" content="{url}">')
    parts.append(f'<meta property="og:image" content="{OG_IMAGE}">')
    parts.append('<meta property="og:image:width" content="1200">')
    parts.append('<meta property="og:image:height" content="1200">')

    # ── Twitter Card ──
    parts.append('<meta name="twitter:card" content="summary_large_image">')
    parts.append(f'<meta name="twitter:title" content="{title}">')
    parts.append(f'<meta name="twitter:description" content="{desc}">')
    parts.append(f'<meta name="twitter:image" content="{OG_IMAGE}">')

    # ── 其他 ──
    parts.append(f'<meta name="author" content="{BRAND_FULL}">')
    parts.append('<meta name="format-detection" content="telephone=no">')
    parts.append('<meta name="theme-color" content="#ffffff">')

    # ── JSON-LD ──
    schemas = cfg.get("schema", [])
    ld_blocks = []

    for s in schemas:
        if s == "Florist":
            ld_blocks.append(schema_florist())
        elif s == "WebSite":
            ld_blocks.append(schema_website())
        elif s == "Organization":
            ld_blocks.append(schema_organization())
        elif s == "CollectionPage":
            ld_blocks.append(schema_collection(title, desc, filename))
        elif s == "WebPage":
            ld_blocks.append(schema_webpage(title, desc, filename))
        elif s == "Article":
            ld_blocks.append(schema_article(title, desc, filename))
        elif s == "AboutPage":
            ld_blocks.append(schema_about())
        elif s == "ContactPage":
            ld_blocks.append(schema_contact())
        elif s == "LocalBusiness":
            ld_blocks.append(schema_localbusiness())
        elif s == "Product":
            ld_blocks.append(schema_product())
        elif s == "FAQPage":
            # 按页面选 FAQ 内容
            if filename == "help-faq.html":
                faq = FAQ_GENERAL
            elif filename == "help-delivery.html":
                faq = FAQ_DELIVERY
            elif filename == "help-returns.html":
                faq = FAQ_RETURNS
            else:
                faq = []
            if faq:
                ld_blocks.append(schema_faq(faq))
        elif s == "BreadcrumbList":
            # 按页面选面包屑父级
            parents = {
                "shop.html": None,
                "product.html": [("全部花束", f"{SITE}/shop.html")],
                "flower-language.html": None,
                "flower-language-detail.html": [("花语百科", f"{SITE}/flower-language.html")],
                "about.html": None,
                "contact.html": None,
                "help-delivery.html": None,
                "help-returns.html": None,
                "help-faq.html": None,
            }
            name = title.split(" - ")[0].split(" | ")[0]
            ld_blocks.append(schema_breadcrumb(filename, name, parents.get(filename)))

    for ld in ld_blocks:
        parts.append(
            '<script type="application/ld+json">\n'
            + json.dumps(ld, ensure_ascii=False, indent=2)
            + '\n</script>'
        )

    return "\n".join(parts)


# ══════════════════════════════════════════════════════════
# 注入
# ══════════════════════════════════════════════════════════

MARKER_START = "<!-- SEO-START -->"
MARKER_END = "<!-- SEO-END -->"

print("=" * 70)
print("  SEO / GEO 元信息注入")
print("=" * 70)
print()

ok = 0
skip = 0

for filename, cfg in PAGES.items():
    path = FRONTEND / filename

    if not path.exists():
        print(f"  ✗ {filename} 不存在")
        continue

    html = path.read_text(encoding="utf-8")

    # 先删掉旧的 SEO 块
    html = re.sub(
        re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
        "",
        html,
        flags=re.DOTALL,
    )

    # 也删掉之前手写的 og / canonical / JSON-LD（花语详情页有）
    html = re.sub(r'<meta property="og:[^"]*"[^>]*>\s*', "", html)
    html = re.sub(r'<meta name="twitter:[^"]*"[^>]*>\s*', "", html)
    html = re.sub(r'<link rel="canonical"[^>]*>\s*', "", html)
    html = re.sub(r'<script type="application/ld\+json">.*?</script>\s*', "", html, flags=re.DOTALL)
    html = re.sub(r'<meta name="robots"[^>]*>\s*', "", html)

    # 生成新块
    block = f"{MARKER_START}\n{build_seo_block(filename, cfg)}\n{MARKER_END}"

    # 插到 </head> 之前
    if "</head>" in html:
        html = html.replace("</head>", block + "\n</head>", 1)
        path.write_text(html, encoding="utf-8")
        s = "索引" if cfg.get("index") else "不索引"
        print(f"  ✓ {filename:<32} {s}")
        ok += 1
    else:
        print(f"  ✗ {filename} 没有 </head>")
        skip += 1

print()
print("=" * 70)
print(f"  完成：{ok} 个页面，{skip} 个跳过")
print("=" * 70)
