# ============================================================
# 【这个文件是干什么的】
# 跳舞兰的 MCP Server —— 让 AI 智能体（千问、Claude、Cursor 等）
# 能直接查询商品、下单、查订单、提售后。
#
# 【为什么需要这个】
# GEO（生成式引擎优化）的核心是「让 AI 能调用你」。
# 光有 llms.txt 只解决「AI 能读到你」，
# MCP Server 解决的是「AI 能操作你」。
#
# 【怎么启动】
#   cd backend
#   .venv\Scripts\python.exe -m app.mcp_server
#
# 【怎么接到 AI 客户端】
# 在 MCP 客户端配置里加：
#   {
#     "mcpServers": {
#       "tiaowulan": {
#         "command": "D:\\...\\backend\\.venv\\Scripts\\python.exe",
#         "args": ["-m", "app.mcp_server"],
#         "cwd": "D:\\...\\backend"
#       }
#     }
#   }
#
# 【提供的工具】
#   search_flowers      搜花
#   get_product         商品详情
#   check_delivery      配送可用性
#   create_order        下单
#   query_order         查订单
#   create_ticket       提售后
#   list_categories     分类列表
#   get_flower_meaning  查花语（内容库）
#   list_articles       花语文章列表
# ============================================================

import asyncio
import json
import sys
from decimal import Decimal

from mcp.server.fastmcp import FastMCP
from sqlalchemy import func, or_, select

from app.core.database import AsyncSessionLocal
from app.models.content import Article
from app.models.order import Order, OrderItem
from app.models.product import Product, ProductStatus
from app.models.ticket import Ticket
from app.services import order_service, product_service, ticket_service

mcp = FastMCP("tiaowulan")


# ════════════════════════════════════════════════════════════
# 【工具 1】搜索花束
# ════════════════════════════════════════════════════════════

@mcp.tool()
async def search_flowers(
    keyword: str = "",
    category: str = "",
    max_price: float = 0,
    limit: int = 10,
) -> str:
    """
    搜索花束。

    Args:
        keyword: 关键词，匹配花束名、花材、花语（如「玫瑰」「香槟」「生日」）
        category: 分类，可选 love / daily / birthday / sympathy / business
        max_price: 最高价格（元），0 表示不限
        limit: 返回数量，默认 10，最多 30

    Returns:
        JSON 字符串，包含花束列表
    """
    limit = min(max(limit, 1), 30)

    async with AsyncSessionLocal() as db:
        stmt = select(Product).where(Product.status == ProductStatus.ON.value)

        if category:
            stmt = stmt.where(Product.category == category)

        if max_price > 0:
            stmt = stmt.where(Product.price <= Decimal(str(max_price)))

        if keyword:
            kw = f"%{keyword}%"
            # 匹配名称、副标题、花语、花材（JSON 转文本后 LIKE）
            stmt = stmt.where(
                or_(
                    Product.name.ilike(kw),
                    Product.subtitle.ilike(kw),
                    Product.meaning.ilike(kw),
                    func.cast(Product.flowers, __import__("sqlalchemy").Text).ilike(kw),
                )
            )

        stmt = stmt.order_by(Product.sort_order).limit(limit)
        result = await db.execute(stmt)
        products = result.scalars().all()

        return json.dumps(
            {
                "count": len(products),
                "products": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "subtitle": p.subtitle,
                        "price": float(p.price),
                        "original_price": float(p.original_price) if p.original_price else None,
                        "category": p.category,
                        "meaning": p.meaning,
                        "flowers": p.flowers,
                        "cover": p.cover,
                        "in_stock": p.stock > 0,
                    }
                    for p in products
                ],
            },
            ensure_ascii=False,
            indent=2,
        )


# ════════════════════════════════════════════════════════════
# 【工具 2】商品详情
# ════════════════════════════════════════════════════════════

@mcp.tool()
async def get_product(product_id: str) -> str:
    """
    查一个花束的完整详情。

    Args:
        product_id: 商品编号，如 TW-001

    Returns:
        JSON 字符串，包含花材、花语、价格、库存
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Product).where(Product.id == product_id))
        p = result.scalar_one_or_none()

        if not p:
            return json.dumps({"error": f"商品 {product_id} 不存在"}, ensure_ascii=False)

        return json.dumps(
            {
                "id": p.id,
                "name": p.name,
                "subtitle": p.subtitle,
                "price": float(p.price),
                "original_price": float(p.original_price) if p.original_price else None,
                "description": p.description,
                "flowers": p.flowers,
                "meaning": p.meaning,
                "category": p.category,
                "cover": p.cover,
                "stock": p.stock,
                "available": p.status == ProductStatus.ON.value and p.stock > 0,
            },
            ensure_ascii=False,
            indent=2,
        )


# ════════════════════════════════════════════════════════════
# 【工具 3】配送可用性
# ════════════════════════════════════════════════════════════

@mcp.tool()
async def check_delivery(product_id: str, delivery_date: str = "") -> str:
    """
    查某个花束在指定日期能不能送达。

    Args:
        product_id: 商品编号
        delivery_date: 配送日期，格式 2026-10-25；留空表示今天

    Returns:
        JSON 字符串，包含是否可送、运费、可选时段
    """
    async with AsyncSessionLocal() as db:
        # 配送规则从配置读
        from app.services import content_service

        delivery = await content_service.get_setting(db, "delivery")

        result = await db.execute(select(Product).where(Product.id == product_id))
        p = result.scalar_one_or_none()

        if not p:
            return json.dumps({"error": f"商品 {product_id} 不存在"}, ensure_ascii=False)

        configured = delivery.get("configured", False)

        return json.dumps(
            {
                "product_id": product_id,
                "delivery_date": delivery_date or "今天",
                "available": configured and p.stock > 0,
                "configured": configured,
                "note": (
                    "配送规则已配置"
                    if configured
                    else "商家尚未配置配送规则，具体时效与运费需联系客服确认"
                ),
                "delivery_slots": delivery.get("delivery_slots") or [],
                "free_shipping_threshold": delivery.get("free_shipping_threshold"),
                "base_shipping_fee": delivery.get("base_shipping_fee"),
            },
            ensure_ascii=False,
            indent=2,
        )


# ════════════════════════════════════════════════════════════
# 【工具 4】下单
# ════════════════════════════════════════════════════════════

@mcp.tool()
async def create_order(
    product_id: str,
    quantity: int,
    receiver_name: str,
    receiver_phone: str,
    receiver_address: str,
    card_message: str = "",
    remark: str = "",
) -> str:
    """
    创建一个订单。

    【重要】会真实占用库存。下单前应该先跟用户确认。

    Args:
        product_id: 商品编号，如 TW-001
        quantity: 数量
        receiver_name: 收花人姓名
        receiver_phone: 收花人手机号（11 位）
        receiver_address: 详细地址（省市区 + 街道门牌）
        card_message: 贺卡留言，可选
        remark: 订单备注，可选

    Returns:
        JSON 字符串，包含订单号和应付金额
    """
    from app.schemas.order import OrderCreate, OrderItemIn, ReceiverInfo

    async with AsyncSessionLocal() as db:
        try:
            payload = OrderCreate(
                items=[OrderItemIn(product_id=product_id, qty=quantity)],
                receiver=ReceiverInfo(
                    name=receiver_name,
                    phone=receiver_phone,
                    detail=receiver_address,
                ),
                card_message=card_message or None,
                remark=remark or None,
            )

            svc = order_service.OrderService(db)
            order = await svc.create_order(payload, user_id=None)

            # 【必须手动 commit】
            # service 层只 flush 不 commit，commit 是 get_db 依赖做的。
            # MCP 直接开 session，要自己提交，否则数据不落库。
            await db.commit()

            return json.dumps(
                {
                    "success": True,
                    "order_no": order.order_no,
                    "status": order.status,
                    "amount": {
                        "product": float(order.amount.product),
                        "delivery_fee": float(order.amount.delivery_fee),
                        "discount": float(order.amount.discount),
                        "total": float(order.amount.total),
                    },
                    "expire_at": order.expire_at,
                    "ttl_seconds": order.ttl_seconds,
                    "next_step": "调用 POST /payments/create 完成付款",
                },
                ensure_ascii=False,
                indent=2,
            )

        except Exception as e:
            return json.dumps(
                {"success": False, "error": str(e)},
                ensure_ascii=False,
                indent=2,
            )


# ════════════════════════════════════════════════════════════
# 【工具 5】查订单
# ════════════════════════════════════════════════════════════

@mcp.tool()
async def query_order(order_no: str) -> str:
    """
    查订单状态和详情。

    Args:
        order_no: 订单号，如 TWL20261021140255A082

    Returns:
        JSON 字符串，包含状态、商品明细、金额、时间线
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Order).where(Order.order_no == order_no))
        o = result.scalar_one_or_none()

        if not o:
            return json.dumps({"error": f"订单 {order_no} 不存在"}, ensure_ascii=False)

        # 明细
        items_result = await db.execute(
            select(OrderItem).where(OrderItem.order_id == o.id)
        )
        items = items_result.scalars().all()

        from app.models import STATUS_TEXT

        return json.dumps(
            {
                "order_no": o.order_no,
                "status": o.status,
                "status_text": STATUS_TEXT.get(o.status, o.status),
                "pay_amount": float(o.pay_amount),
                "receiver": o.receiver,
                "phone": o.phone,
                "address": o.address_detail,
                "card_message": o.card_message,
                "remark": o.remark,
                "created_at": str(o.created_at),
                "paid_at": o.paid_at,
                "items": [
                    {
                        "product_id": i.product_id,
                        "name": i.product_name,
                        "qty": i.qty,
                        "unit_price": float(i.price),
                        "subtotal": float(i.subtotal),
                    }
                    for i in items
                ],
            },
            ensure_ascii=False,
            indent=2,
        )


# ════════════════════════════════════════════════════════════
# 【工具 6】提售后
# ════════════════════════════════════════════════════════════

@mcp.tool()
async def create_ticket(
    order_no: str,
    reason: str,
    ticket_type: str = "quality",
    contact_phone: str = "",
) -> str:
    """
    提交售后工单。

    Args:
        order_no: 订单号
        reason: 问题描述（至少 5 个字）
        ticket_type: 类型，quality（质量问题）/ delivery（配送问题）/ other（其他）
        contact_phone: 联系电话，可选

    Returns:
        JSON 字符串，包含工单号
    """
    from app.schemas.ticket import TicketCreate

    async with AsyncSessionLocal() as db:
        try:
            payload = TicketCreate(
                order_no=order_no,
                type=ticket_type,
                reason=reason,
                contact_phone=contact_phone or None,
            )

            svc = ticket_service.TicketService(db)
            ticket = await svc.create_ticket(payload)

            # 同上，MCP 里要自己 commit
            await db.commit()

            return json.dumps(
                {
                    "success": True,
                    "ticket_no": ticket.ticket_no,
                    "status": ticket.status,
                    "note": "客服会在 2 小时内响应",
                },
                ensure_ascii=False,
                indent=2,
            )

        except Exception as e:
            return json.dumps(
                {"success": False, "error": str(e)},
                ensure_ascii=False,
                indent=2,
            )


# ════════════════════════════════════════════════════════════
# 【工具 7】分类列表
# ════════════════════════════════════════════════════════════

@mcp.tool()
async def list_categories() -> str:
    """
    列出所有花束分类和每个分类的数量。

    Returns:
        JSON 字符串
    """
    # 分类中文名（枚举值 → 中文）
    CATEGORY_CN = {
        "daily": "日常",
        "love": "告白",
        "birthday": "生日",
        "sympathy": "探望",
        "business": "商务",
    }

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Product.category, func.count(Product.id))
            .where(Product.status == ProductStatus.ON.value)
            .group_by(Product.category)
        )
        rows = result.all()

        return json.dumps(
            {
                "categories": [
                    {
                        "key": row[0],
                        "name": CATEGORY_CN.get(row[0], row[0]),
                        "count": row[1],
                    }
                    for row in rows
                ]
            },
            ensure_ascii=False,
            indent=2,
        )


# ════════════════════════════════════════════════════════════
# 【工具 8】查花语（内容库）
# ════════════════════════════════════════════════════════════

@mcp.tool()
async def get_flower_meaning(flower: str) -> str:
    """
    查一种花的花语和养护知识（来自花语百科）。

    Args:
        flower: 花名或关键词，如「玫瑰」「香槟玫瑰」「向日葵」

    Returns:
        JSON 字符串，包含花语、文章标题、FAQ
    """
    async with AsyncSessionLocal() as db:
        kw = f"%{flower}%"
        result = await db.execute(
            select(Article)
            .where(Article.status == "published")
            .where(
                or_(
                    Article.title.ilike(kw),
                    Article.meaning.ilike(kw),
                    Article.content.ilike(kw),
                )
            )
            .order_by(Article.sort_weight.desc())
            .limit(3)
        )
        articles = result.scalars().all()

        if not articles:
            return json.dumps(
                {"found": False, "message": f"没有找到关于「{flower}」的花语文章"},
                ensure_ascii=False,
            )

        return json.dumps(
            {
                "found": True,
                "count": len(articles),
                "articles": [
                    {
                        "slug": a.slug,
                        "title": a.title,
                        "meaning": a.meaning,
                        "summary": a.summary,
                        "faq": a.faq,
                        "url": f"/flower-language-detail.html?slug={a.slug}",
                    }
                    for a in articles
                ],
            },
            ensure_ascii=False,
            indent=2,
        )


# ════════════════════════════════════════════════════════════
# 【工具 9】花语文章列表
# ════════════════════════════════════════════════════════════

@mcp.tool()
async def list_articles(limit: int = 20) -> str:
    """
    列出花语百科的所有文章。

    Args:
        limit: 返回数量，默认 20

    Returns:
        JSON 字符串
    """
    limit = min(max(limit, 1), 50)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Article)
            .where(Article.status == "published")
            .order_by(Article.sort_weight.desc())
            .limit(limit)
        )
        articles = result.scalars().all()

        return json.dumps(
            {
                "count": len(articles),
                "articles": [
                    {
                        "slug": a.slug,
                        "title": a.title,
                        "meaning": a.meaning,
                        "category": a.category,
                        "url": f"/flower-language-detail.html?slug={a.slug}",
                    }
                    for a in articles
                ],
            },
            ensure_ascii=False,
            indent=2,
        )


# ════════════════════════════════════════════════════════════
# 【入口】
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # stdio 模式：AI 客户端通过标准输入输出通信
    mcp.run()
