# -*- coding: utf-8 -*-
"""统计 v2 版本的完整状态"""

import glob, os, re

PROTO = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\prototype\luxe"

# 页面定义：(文件, 中文名, 分类, 布局类型, 交互说明)
PAGES = [
    ("index.html", "首页", "核心流程", "叙事流", "购物袋角标"),
    ("shop.html", "全部花束", "核心流程", "4 列网格", "分类筛选 / 排序"),
    ("product.html", "商品详情", "核心流程", "左右分栏", "尺寸 / 包装 / 数量 / 加购 / 立即购买"),
    ("cart.html", "购物袋", "核心流程", "左右分栏", "数量增减 / 移除 / 实时算价"),
    ("checkout.html", "确认订单", "核心流程", "左右分栏", "表单校验 / 去支付"),
    ("pay.html", "支付", "核心流程", "左右分栏", "方式选择 / 倒计时 / 支付跳转"),
    ("order-success.html", "下单成功", "核心流程", "左右分栏", "复制订单号 / 提示关闭"),

    ("login.html", "登录", "账户", "居中卡片", "验证码倒计时 / 手机校验"),
    ("orders.html", "我的订单", "账户", "表格行", "状态筛选"),
    ("order-detail.html", "订单详情", "账户", "左右分栏", "操作按钮"),
    ("address.html", "地址簿", "账户", "3 列卡片", "删除 / 编辑"),
    ("after-sale.html", "申请售后", "账户", "左右分栏", "类型选择 / 提交校验"),

    ("flower-language.html", "花语百科", "内容", "4 列网格", "分类筛选"),
    ("flower-language-detail.html", "花语详情", "内容", "左正文 + 右目录", "目录平滑滚动"),
    ("about.html", "关于", "内容", "居中长文", "—"),
    ("contact.html", "联系", "内容", "左右两栏", "—"),
    ("search.html", "搜索", "内容", "4 列网格", "实时搜索 / 热门词"),

    ("help-delivery.html", "配送范围", "帮助", "左目录 + 右内容", "—"),
    ("help-returns.html", "售后政策", "帮助", "左目录 + 右内容", "—"),
    ("help-faq.html", "常见问题", "帮助", "左目录 + 右内容", "—"),

    ("admin.html", "数据看板", "后台", "侧栏 + 主区", "登录门禁 / 8 页切换"),
]

print("| # | 页面 | 分类 | 布局 | 交互 | 大小 |")
print("|---|---|---|---|---|---|")
total_kb = 0
for i, (fn, name, cat, layout, inter) in enumerate(PAGES, 1):
    p = os.path.join(PROTO, fn)
    if os.path.exists(p):
        kb = round(os.path.getsize(p) / 1024)
        total_kb += kb
    else:
        kb = 0
    print(f"| {i:02d} | {name} | {cat} | {layout} | {inter} | {kb}KB |")

print(f"\n总计: {len(PAGES)} 个页面, {total_kb} KB")
