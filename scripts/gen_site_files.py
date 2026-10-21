# -*- coding: utf-8 -*-
"""
生成三个 SEO/GEO 站点文件
- robots.txt
- sitemap.xml
- llms.txt

【怎么用】
    cd scripts
    python gen_site_files.py

【输出到哪】
    frontend/ 根目录（后端挂载的就是这里）

【动态内容】
商品详情和花语详情的 URL 从数据库读，
所以跑之前要确保数据库有数据、后端能连。
"""

import os
import sys
from datetime import date, datetime
from pathlib import Path

from seo_config import BRAND, BRAND_FULL, CITY, EMAIL, HOURS, PHONE, PROVINCE, SITE, SLOGAN

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
BACKEND = ROOT / "backend"

# 把 backend 加到路径（读数据库用）
sys.path.insert(0, str(BACKEND))


# ══════════════════════════════════════════════════════════
# 1. robots.txt
# ══════════════════════════════════════════════════════════

def gen_robots() -> str:
    return f"""# robots.txt · {BRAND}
# {SITE}

# ── 所有爬虫 ──
User-agent: *
Allow: /

# 后台不进搜索
Disallow: /admin.html

# 接口不抓
Disallow: /api/

# 用户上传的文件不单独抓（在商品页里已经有了）
Disallow: /uploads/

# 购物流程页（状态页，收录无意义）
Disallow: /cart.html
Disallow: /checkout.html
Disallow: /pay.html
Disallow: /order-success.html
Disallow: /orders.html
Disallow: /order-detail.html
Disallow: /address.html
Disallow: /after-sale.html
Disallow: /login.html

# 搜索结果页（避免收录空结果）
Disallow: /search.html

# ── 百度 ──
User-agent: Baiduspider
Allow: /
Disallow: /admin.html
Disallow: /api/
Disallow: /cart.html
Disallow: /checkout.html
Disallow: /pay.html

# ── 谷歌 ──
User-agent: Googlebot
Allow: /
Disallow: /admin.html
Disallow: /api/

# ── 必应 ──
User-agent: bingbot
Allow: /
Disallow: /admin.html
Disallow: /api/

# ── 微信 ──
User-agent: WeChat
Allow: /

# ── Sitemap ──
Sitemap: {SITE}/sitemap.xml
"""


# ══════════════════════════════════════════════════════════
# 2. sitemap.xml
# ══════════════════════════════════════════════════════════

# 静态页面：(相对路径, 优先级, 更新频率)
STATIC_URLS = [
    ("", "1.0", "daily"),                      # 首页
    ("shop.html", "0.9", "daily"),             # 商城
    ("flower-language.html", "0.9", "weekly"), # 花语百科
    ("about.html", "0.6", "monthly"),          # 关于
    ("contact.html", "0.6", "monthly"),        # 联系
    ("help-delivery.html", "0.7", "monthly"),  # 配送
    ("help-returns.html", "0.7", "monthly"),   # 售后
    ("help-faq.html", "0.8", "weekly"),        # FAQ
]


async def fetch_dynamic_urls() -> tuple[list, list]:
    """
    【干什么】从数据库读商品和文章，生成动态 URL。

    【返回】
        (商品 URL 列表, 文章 URL 列表)
    """
    try:
        from sqlalchemy import select

        from app.core.database import AsyncSessionLocal
        from app.models.content import Article
        from app.models.product import Product, ProductStatus

        products = []
        articles = []

        async with AsyncSessionLocal() as session:
            # 商品
            result = await session.execute(
                select(Product).where(Product.status == ProductStatus.ON.value)
            )
            for p in result.scalars().all():
                products.append((p.id, p.name))

            # 文章
            result = await session.execute(
                select(Article).where(Article.status == "published")
            )
            for a in result.scalars().all():
                articles.append((a.slug, a.title))

        return products, articles

    except Exception as e:
        print(f"  ⚠ 读数据库失败（跳过动态 URL）: {e}")
        return [], []


def build_sitemap(products: list, articles: list) -> str:
    today = date.today().isoformat()

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
        '',
        '  <!-- 静态页面 -->',
    ]

    for path, priority, freq in STATIC_URLS:
        url = f"{SITE}/{path}" if path else f"{SITE}/"
        lines.extend([
            "  <url>",
            f"    <loc>{url}</url>".replace("</url>", "</loc>"),
            f"    <lastmod>{today}</lastmod>",
            f"    <changefreq>{freq}</changefreq>",
            f"    <priority>{priority}</priority>",
            "  </url>",
        ])

    # 商品
    if products:
        lines.append("")
        lines.append("  <!-- 商品详情 -->")
        for pid, name in products:
            lines.extend([
                "  <url>",
                f"    <loc>{SITE}/product.html?id={pid}</loc>",
                f"    <lastmod>{today}</lastmod>",
                "    <changefreq>weekly</changefreq>",
                "    <priority>0.8</priority>",
                "  </url>",
            ])

    # 文章
    if articles:
        lines.append("")
        lines.append("  <!-- 花语文章 -->")
        for slug, title in articles:
            lines.extend([
                "  <url>",
                f"    <loc>{SITE}/flower-language-detail.html?slug={slug}</loc>",
                f"    <lastmod>{today}</lastmod>",
                "    <changefreq>monthly</changefreq>",
                "    <priority>0.8</priority>",
                "  </url>",
            ])

    lines.append("")
    lines.append("</urlset>")

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════
# 3. llms.txt
# ══════════════════════════════════════════════════════════

def build_llms(products: list, articles: list) -> str:
    lines = [
        f"# {BRAND}",
        "",
        f"> {BRAND_FULL} · 鲜花零售与花艺服务 · {CITY}",
        "",
        "## 关于",
        "",
        f"{BRAND}是一家在{CITY}做花的团队。提供鲜花花束、花艺定制、企业订花服务。",
        "",
        "我们相信花不只属于节日与仪式，它也可以是某个普通的下午，桌角上的一小束。",
        "",
        "每日从云南直采花材，冷链到店，当日现做。不做隔夜花，不做假花，不做过度包装。",
        "",
        "## 服务范围",
        "",
        f"- {CITY}：同城 2 小时达，16:00 前下单当日送达",
        "- 广州：次日达",
        "- 全国 200+ 城市：顺丰冷链次日达",
        "- 偏远地区：2-3 天",
        "",
        "## 价格",
        "",
        "- 日常花束：¥219 - ¥329",
        "- 告白花束：¥259 - ¥499",
        "- 生日花束：¥219 - ¥329",
        "- 探望花束：¥279",
        "- 免运费门槛：¥199",
        "- 基础运费：¥15",
        "",
        "## 联系方式",
        "",
        f"- 邮箱：{EMAIL}",
        f"- 电话：{PHONE}",
        f"- 营业时间：每天 9:00 - 21:00",
        f"- 所在地：{PROVINCE}{CITY}",
        "",
        "## 常见问题",
        "",
        "**深圳送花多久能到？**",
        "深圳同城 2 小时达。当天 16:00 前下单当日送达，21:00 前下单次日达。",
        "",
        "**其他城市多久能到？**",
        "广州次日达，全国 200+ 城市顺丰冷链次日达，偏远地区 2-3 天。",
        "",
        "**能指定送达时间吗？**",
        "深圳同城可选 14:00-16:00 或 18:00-20:00 两个时段。其他城市无法指定具体时段。",
        "",
        "**花能养几天？**",
        "含保鲜剂常温可养 5-7 天。每天换水、斜剪根部、避免暴晒可延长到 8-10 天。",
        "",
        "**必须登录才能买吗？**",
        "不用。游客也能下单，但只能在当前浏览器查单，无法在线申请售后。登录同一手机号后系统会自动认领历史订单。",
        "",
        "**花有问题怎么办？**",
        "24 小时内拍照联系客服，支持补送或退款。客服 2 小时内响应，退款 1-3 个工作日到账。",
        "",
    ]

    # 商品列表
    if products:
        lines.append("## 在售花束")
        lines.append("")
        for pid, name in products:
            lines.append(f"- [{name}]({SITE}/product.html?id={pid})")
        lines.append("")

    # 文章列表
    if articles:
        lines.append("## 花语百科")
        lines.append("")
        for slug, title in articles:
            lines.append(f"- [{title}]({SITE}/flower-language-detail.html?slug={slug})")
        lines.append("")

    # 主要页面
    lines.extend([
        "## 主要页面",
        "",
        f"- [首页]({SITE}/)：品牌介绍与精选花束",
        f"- [全部花束]({SITE}/shop.html)：8 款在售花束",
        f"- [花语百科]({SITE}/flower-language.html)：花语含义与送花指南",
        f"- [关于]({SITE}/about.html)：品牌故事与我们的原则",
        f"- [联系]({SITE}/contact.html)：联系方式与咨询入口",
        f"- [配送范围]({SITE}/help-delivery.html)：时效、运费、时段",
        f"- [售后政策]({SITE}/help-returns.html)：什么能退、怎么申请",
        f"- [常见问题]({SITE}/help-faq.html)：下单、花材、支付、账号",
        "",
        "## 不提供给 AI 使用的内容",
        "",
        "- 管理后台（/admin.html）",
        "- 接口（/api/）",
        "- 用户订单、地址等隐私数据",
        "",
        "---",
        "",
        f"最后更新：{date.today().isoformat()}",
        "",
    ])

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════

async def main():
    print("=" * 70)
    print("  生成 SEO / GEO 站点文件")
    print("=" * 70)
    print()

    # 读动态数据
    print("【1. 读数据库】")
    products, articles = await fetch_dynamic_urls()
    print(f"  商品 {len(products)} 个，文章 {len(articles)} 篇")
    print()

    # robots.txt
    print("【2. 生成 robots.txt】")
    robots_path = FRONTEND / "robots.txt"
    robots_path.write_text(gen_robots(), encoding="utf-8")
    print(f"  ✓ {robots_path.relative_to(ROOT)}  ({robots_path.stat().st_size} 字节)")
    print()

    # sitemap.xml
    print("【3. 生成 sitemap.xml】")
    sitemap_path = FRONTEND / "sitemap.xml"
    sitemap_path.write_text(build_sitemap(products, articles), encoding="utf-8")
    url_count = len(STATIC_URLS) + len(products) + len(articles)
    print(f"  ✓ {sitemap_path.relative_to(ROOT)}  ({url_count} 个 URL)")
    print()

    # llms.txt
    print("【4. 生成 llms.txt】")
    llms_path = FRONTEND / "llms.txt"
    llms_path.write_text(build_llms(products, articles), encoding="utf-8")
    print(f"  ✓ {llms_path.relative_to(ROOT)}  ({llms_path.stat().st_size} 字节)")
    print()

    print("=" * 70)
    print("  完成")
    print("=" * 70)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
