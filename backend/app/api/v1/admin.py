# ============================================================
# 【这个文件是干什么的】
# 管理后台的接口：数据看板、全部订单、全部商品、状态日志。
#
# 【TODO：上线前必须加管理员鉴权】
# 现在的实现任何人都能访问，生产环境绝对不行。
# 加鉴权的方式：在 router 上加 dependencies=[Depends(require_admin)]
# ============================================================

from fastapi import APIRouter, Query

from app.api.deps import AdminDep

from app.api.deps import DbDep
from app.models import STATUS_TEXT
from app.repositories import OrderRepository, ProductRepository, TicketRepository
from app.schemas import ApiResponse

router = APIRouter(prefix="/admin", tags=["管理后台"])


# ════════════════════════════════════════════════════════════
# 【数据看板】
# ════════════════════════════════════════════════════════════

@router.get(
    "/stats",
    response_model=ApiResponse[dict],
    summary="【后台】数据看板",
    description="订单数、营收、商品数、待处理工单",
)
async def get_stats(admin: AdminDep, db: DbDep):
    """
    【干什么】后台首页的数字看板。

    【返回】
        - orders_total:  总订单数
        - orders_paid:   已支付订单数
        - orders_today:  今日订单数
        - revenue:       累计营收（元）
        - products_on:   在售商品数
        - tickets_open:  待处理工单数
        - by_status:     各状态订单分布
    """
    order_repo = OrderRepository(db)
    product_repo = ProductRepository(db)
    ticket_repo = TicketRepository(db)

    stats = await order_repo.get_stats()
    tickets_open = await ticket_repo.count_open()

    # 统计在售商品数
    from sqlalchemy import func, select
    from app.models import Product, ProductStatus

    result = await db.execute(
        select(func.count(Product.id)).where(Product.status == ProductStatus.ON.value)
    )
    products_on = result.scalar_one()

    return ApiResponse(data={
        "orders_total": stats["orders_total"],
        "orders_paid": stats["orders_paid"],
        "orders_today": stats["orders_today"],
        "revenue": str(stats["revenue"]),
        "products_on": products_on,
        "tickets_open": tickets_open,
        "by_status": [
            {
                "status": k,
                "text": STATUS_TEXT.get(k, k),
                "count": v,
            }
            for k, v in stats["by_status"].items()
        ],
    })


# ════════════════════════════════════════════════════════════
# 【全部订单】
# ════════════════════════════════════════════════════════════

@router.get(
    "/orders",
    response_model=ApiResponse[dict],
    summary="【后台】全部订单",
    description="包含所有状态的订单，可按状态筛选",
)
async def list_all_orders(
    admin: AdminDep,
    db: DbDep,
    status: str | None = Query(None, description="按状态筛选"),
    limit: int = Query(100, ge=1, le=500),
):
    """
    【干什么】查全部订单（后台用）。

    【和前台 /orders 的区别】
    前台只查自己的订单，后台查所有订单。
    """
    from sqlalchemy import select
    from app.models import Order
    from sqlalchemy.orm import selectinload

    stmt = select(Order).options(selectinload(Order.items))

    if status:
        stmt = stmt.where(Order.status == status)

    stmt = stmt.order_by(Order.created_at.desc()).limit(limit)

    result = await db.execute(stmt)
    orders = list(result.scalars().all())

    return ApiResponse(data={
        "items": [
            {
                "order_no": o.order_no,
                "status": o.status,
                "status_text": STATUS_TEXT.get(o.status, o.status),
                "pay_amount": str(o.pay_amount),
                "receiver": o.receiver,
                "phone": o.phone,
                "address": "".join(filter(None, [
                    o.province, o.city, o.district, o.address_detail,
                ])),
                "delivery_date": o.delivery_date,
                "delivery_slot": o.delivery_slot,
                "items": [
                    {"name": i.product_name, "qty": i.qty, "price": str(i.price)}
                    for i in o.items
                ],
                "created_at": o.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "paid_at": o.paid_at,
            }
            for o in orders
        ],
        "total": len(orders),
    })


# ════════════════════════════════════════════════════════════
# 【全部商品】
# ════════════════════════════════════════════════════════════

@router.get(
    "/products",
    response_model=ApiResponse[dict],
    summary="【后台】全部商品",
    description="包含已下架的商品",
)
async def list_all_products(
    admin: AdminDep,
    db: DbDep,
    limit: int = Query(200, ge=1, le=500),
):
    """
    【干什么】查全部商品（后台用）。

    【和前台 /products 的区别】
    前台只显示上架的，后台显示全部（含下架）。
    """
    repo = ProductRepository(db)
    products = await repo.list_admin(limit=limit)

    return ApiResponse(data={
        "items": [
            {
                "id": p.id,
                "name": p.name,
                "subtitle": p.subtitle,
                "price": str(p.price),
                "category": p.category,
                "status": p.status,
                "stock": p.stock,
                "sort_order": p.sort_order,
                "created_at": p.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for p in products
        ],
        "total": len(products),
    })


# ════════════════════════════════════════════════════════════
# 【状态日志】
# ════════════════════════════════════════════════════════════

@router.get(
    "/logs",
    response_model=ApiResponse[list],
    summary="【后台】状态流转日志",
    description="最近发生的所有订单状态变化",
)
async def list_logs(
    admin: AdminDep,
    db: DbDep,
    limit: int = Query(100, ge=1, le=1000),
):
    """
    【干什么】查最近的状态变化记录。

    【什么时候用】
    - 排查问题：某个订单为什么卡住了
    - 追责：谁把订单改成了这个状态
    """
    from sqlalchemy import select
    from app.models import OrderLog

    stmt = select(OrderLog).order_by(OrderLog.id.desc()).limit(limit)
    result = await db.execute(stmt)
    logs = list(result.scalars().all())

    return ApiResponse(data=[
        {
            "order_no": log.order_no,
            "from_status": log.from_status,
            "to_status": log.to_status,
            "reason": log.reason,
            "operator": log.operator,
            "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for log in logs
    ])


