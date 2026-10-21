# -*- coding: utf-8 -*-
"""
SEO / GEO 配置表
每个页面的 title / description / keywords / OG / JSON-LD

【域名】
上线时把 SITE 改成真实域名，其他都不用动。
"""

# ══════════════════════════════════════════════════════════
# 站点基础信息
# ══════════════════════════════════════════════════════════

SITE = "https://h5.tiaowulan.com"

BRAND = "跳舞兰"
BRAND_FULL = "深圳市跳舞兰科技有限公司"
BRAND_EN = "Tiao Wu Lan"
SLOGAN = "Living With Flowers Every Day"

PHONE = "400-000-0000"
EMAIL = "hello@tiaowulan.com"
HOURS = "Mo-Su 09:00-21:00"

CITY = "深圳市"
PROVINCE = "广东省"
COUNTRY = "CN"

# 默认 OG 图
OG_IMAGE = f"{SITE}/images/01_chenguang.png"


# ══════════════════════════════════════════════════════════
# 页面配置
#
# index=True  → 允许搜索引擎收录
# index=False → noindex（后台、购物车、订单等）
# ══════════════════════════════════════════════════════════

PAGES = {

    # ────────────────────────────────────────────────────
    # 首页
    # ────────────────────────────────────────────────────
    "index.html": {
        "index": True,
        "title": "跳舞兰花艺 - 深圳同城2小时达的日常花束",
        "description": "跳舞兰是深圳的花艺团队。当日现做花束，香槟玫瑰、白郁金香、向日葵等 8 款日常花束，¥199 起。深圳同城 2 小时达，全国 200+ 城市次日达，满 199 免运费。",
        "keywords": "深圳鲜花,深圳花店,花束配送,同城送花,日常花束,跳舞兰",
        "og_type": "website",
        "schema": ["Florist", "WebSite", "Organization"],
    },

    # ────────────────────────────────────────────────────
    # 商城
    # ────────────────────────────────────────────────────
    "shop.html": {
        "index": True,
        "title": "全部花束 - 8 款当日现做鲜花 | 跳舞兰",
        "description": "跳舞兰全部花束。日常、告白、生日、探望四个场景，8 款当日现做。香槟玫瑰 ¥299 起，向日葵 ¥219 起。深圳同城 2 小时达，满 199 免运费。",
        "keywords": "花束,鲜花,买花,花店,深圳鲜花,告白花束,生日花束",
        "og_type": "website",
        "schema": ["CollectionPage", "BreadcrumbList"],
    },

    # ────────────────────────────────────────────────────
    # 商品详情（动态，schema 由 JS 注入）
    # ────────────────────────────────────────────────────
    "product.html": {
        "index": True,
        "title": "花束详情 - 当日现做鲜花 | 跳舞兰",
        "description": "跳舞兰花束详情。含花材清单、规格尺寸、养护方法。深圳同城 2 小时达，16:00 前下单当日送达，满 199 免运费。",
        "keywords": "花束详情,鲜花,花材,养护方法,深圳鲜花",
        "og_type": "product",
        "schema": ["Product", "BreadcrumbList"],
        "dynamic": True,  # 商品名和价格由 JS 填充
    },

    # ────────────────────────────────────────────────────
    # 花语百科
    # ────────────────────────────────────────────────────
    "flower-language.html": {
        "index": True,
        "title": "花语百科 - 每种花都有它的意思 | 跳舞兰",
        "description": "香槟玫瑰、白郁金香、向日葵、绣球、山茶……每种花的花语、适合送的场景、养护方法。选花之前，先知道它要说什么。",
        "keywords": "花语,花语大全,玫瑰花语,向日葵花语,郁金香花语,送花含义",
        "og_type": "website",
        "schema": ["CollectionPage", "BreadcrumbList"],
    },

    # ────────────────────────────────────────────────────
    # 花语详情（动态）
    # ────────────────────────────────────────────────────
    "flower-language-detail.html": {
        "index": True,
        "title": "花语百科 - 花语含义与送花指南 | 跳舞兰",
        "description": "每种花的花语含义、适合送的场景、搭配建议、养护方法。含常见问题解答。",
        "keywords": "花语,花语含义,送花指南,鲜花养护",
        "og_type": "article",
        "schema": ["Article", "FAQPage", "BreadcrumbList"],
        "dynamic": True,
    },

    # ────────────────────────────────────────────────────
    # 关于
    # ────────────────────────────────────────────────────
    "about.html": {
        "index": True,
        "title": "关于跳舞兰 - 一家在深圳做花的团队",
        "description": "跳舞兰是深圳市跳舞兰科技有限公司旗下的花艺品牌。每日云南直采，冷链到店，当日现做。不做隔夜花，不做假花，不做过度包装。",
        "keywords": "跳舞兰,深圳花店,花艺品牌,关于我们",
        "og_type": "website",
        "schema": ["AboutPage", "Organization", "BreadcrumbList"],
    },

    # ────────────────────────────────────────────────────
    # 联系
    # ────────────────────────────────────────────────────
    "contact.html": {
        "index": True,
        "title": "联系我们 - 跳舞兰花艺",
        "description": "跳舞兰联系方式：邮箱 hello@tiaowulan.com，电话 400-000-0000，服务时间每天 9:00-21:00。订单问题、花材问题、企业订花、定制需求，2 小时内回复。",
        "keywords": "跳舞兰联系方式,深圳花店电话,企业订花,花艺定制",
        "og_type": "website",
        "schema": ["ContactPage", "LocalBusiness", "BreadcrumbList"],
    },

    # ────────────────────────────────────────────────────
    # 帮助：配送
    # ────────────────────────────────────────────────────
    "help-delivery.html": {
        "index": True,
        "title": "配送范围与时效 - 深圳2小时达 | 跳舞兰",
        "description": "深圳同城 2 小时达，广州次日达，全国 200+ 城市顺丰冷链。满 ¥199 免运费，不满收 ¥15。深圳当日达 16:00 前下单，其他城市提前 1 天。",
        "keywords": "鲜花配送,送花时效,深圳送花,配送范围,运费",
        "og_type": "article",
        "schema": ["WebPage", "BreadcrumbList"],
    },

    # ────────────────────────────────────────────────────
    # 帮助：售后
    # ────────────────────────────────────────────────────
    "help-returns.html": {
        "index": True,
        "title": "售后政策 - 花有问题我们负责到底 | 跳舞兰",
        "description": "花材破损、不新鲜、与描述不符，24 小时内拍照联系我们，支持补送或退款。客服 2 小时内响应，退款 1-3 个工作日到账。",
        "keywords": "鲜花售后,退款政策,花色差,补送,鲜花质量",
        "og_type": "article",
        "schema": ["WebPage", "BreadcrumbList"],
    },

    # ────────────────────────────────────────────────────
    # 帮助：FAQ
    # ────────────────────────────────────────────────────
    "help-faq.html": {
        "index": True,
        "title": "常见问题 - 送花、花材、支付、账号 | 跳舞兰",
        "description": "跳舞兰常见问题：最早什么时候能送到、能指定时间吗、花是新鲜的吗、能养几天、必须登录才能买吗、游客订单能找回吗、花有问题怎么办。",
        "keywords": "鲜花常见问题,送花时间,鲜花保鲜,游客下单,鲜花售后",
        "og_type": "article",
        "schema": ["FAQPage", "BreadcrumbList"],
    },

    # ────────────────────────────────────────────────────
    # 不索引的页面
    # ────────────────────────────────────────────────────
    "admin.html": {"index": False, "title": "管理后台 | 跳舞兰", "description": "管理后台"},
    "cart.html": {"index": False, "title": "购物袋 | 跳舞兰", "description": "查看购物袋中的商品"},
    "checkout.html": {"index": False, "title": "确认订单 | 跳舞兰", "description": "确认订单信息"},
    "pay.html": {"index": False, "title": "支付 | 跳舞兰", "description": "完成支付"},
    "order-success.html": {"index": False, "title": "下单成功 | 跳舞兰", "description": "订单已提交"},
    "orders.html": {"index": False, "title": "我的订单 | 跳舞兰", "description": "查看历史订单"},
    "order-detail.html": {"index": False, "title": "订单详情 | 跳舞兰", "description": "查看订单详情"},
    "address.html": {"index": False, "title": "地址簿 | 跳舞兰", "description": "管理收货地址"},
    "after-sale.html": {"index": False, "title": "申请售后 | 跳舞兰", "description": "提交售后申请"},
    "login.html": {"index": False, "title": "登录 | 跳舞兰", "description": "登录账号"},
    "search.html": {"index": False, "title": "搜索 | 跳舞兰", "description": "搜索花束"},
}
