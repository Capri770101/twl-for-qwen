# ============================================================
# 【这个文件是干什么的】
# 订单相关的接口。
#
# 【这一层只做转手】
# 收参数 → 调 Service → 返回，不写业务逻辑。
# ============================================================

from fastapi import APIRouter, Query

from app.api.deps import OrderServiceDep
from app.models import STATUS_TEXT
from app.schemas import (
    ApiResponse,
    OrderBrief,
    OrderCreate,
    OrderCreateResult,
    OrderOut,
    OrderQuery,
    TimelineItem,
)

router = APIRouter(prefix="/orders", tags=["订单"])


# ════════════════════════════════════════════════════════════
# 【创建订单】
# ════════════════════════════════════════════════════════════

@router.post(
    "",
    response_model=ApiResponse[OrderCreateResult],
    summary="创建订单",
    description="校验商品、算价、扣库存、生成订单号",
)
async def create_order(data: OrderCreate, service: OrderServiceDep):
    """
    【干什么】用户点「去支付」时创建订单。

    【返回】
        订单号 + 金额明细 + 支付截止时间

    【注意】
        库存是在这一步扣的。
        如果用户不付款，30 分钟后超时，库存会被定时任务释放。
    """
    result = await service.create_order(data)
    return ApiResponse(data=result)


# ════════════════════════════════════════════════════════════
# 【查询订单】
# ════════════════════════════════════════════════════════════

@router.get(
    "/{order_no}",
    response_model=ApiResponse[OrderOut],
    summary="订单详情",
    description="返回订单全部信息 + 状态时间线",
)
async def get_order(order_no: str, service: OrderServiceDep):
    """
    【干什么】按订单号查详情。

    【返回】
        订单信息 + 商品明细 + 状态时间线（用户能看到订单走到哪一步）
    """
    order = await service.get_order(order_no)

    # 把时间线转成前端要的格式
    timeline = [
        TimelineItem(
            status=log.to_status,
            status_text=STATUS_TEXT.get(log.to_status, log.to_status),
            reason=log.reason,
            operator=log.operator,
            time=log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        )
        for log in order.logs
    ]

    # 【为什么手动构造而不是 model_validate(order)】
    # OrderOut 里有 status_text 和 timeline 两个字段，
    # 数据库里没有这两个字段，所以不能直接 validate ORM 对象。
    # 显式构造 dict，把计算出来的字段补上。
    out = OrderOut(
        id=order.id,
        order_no=order.order_no,
        status=order.status,
        status_text=STATUS_TEXT.get(order.status, order.status),
        total_amount=order.total_amount,
        delivery_fee=order.delivery_fee,
        discount_amount=order.discount_amount,
        pay_amount=order.pay_amount,
        receiver=order.receiver,
        phone=order.phone,
        province=order.province,
        city=order.city,
        district=order.district,
        address_detail=order.address_detail,
        delivery_date=order.delivery_date,
        delivery_slot=order.delivery_slot,
        card_message=order.card_message,
        anonymous=order.anonymous,
        pay_channel=order.pay_channel,
        paid_at=order.paid_at,
        expire_at=order.expire_at,
        created_at=order.created_at,
        items=[
            {
                "product_id": i.product_id,
                "product_name": i.product_name,
                "product_cover": i.product_cover,
                "price": i.price,
                "qty": i.qty,
                "subtotal": i.subtotal,
            }
            for i in order.items
        ],
        timeline=timeline,
    )

    return ApiResponse(data=out)


@router.get(
    "",
    response_model=ApiResponse[dict],
    summary="订单列表",
    description="支持按状态筛选、订单号搜索、电话搜索、分页",
)
async def list_orders(
    service: OrderServiceDep,
    status: str | None = Query(None, description="按状态筛选"),
    order_no: str | None = Query(None, description="按订单号搜索"),
    phone: str | None = Query(None, description="按电话搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    【干什么】查订单列表。

    【返回】
        订单摘要列表 + 总数
    """
    from app.repositories import OrderRepository

    query = OrderQuery(
        status=status,
        order_no=order_no,
        phone=phone,
        page=page,
        page_size=page_size,
    )

    repo = OrderRepository(service.db)
    orders = await repo.list_orders(query)
    total = await repo.count_orders(query)

    items = []
    for o in orders:
        # 商品摘要，比如「晨光序曲 ×1」
        summary = "、".join(f"{i.product_name}×{i.qty}" for i in o.items[:2])
        if len(o.items) > 2:
            summary += f" 等{len(o.items)}件"

        items.append({
            "order_no": o.order_no,
            "status": o.status,
            "status_text": STATUS_TEXT.get(o.status, o.status),
            "pay_amount": str(o.pay_amount),
            "receiver": o.receiver,
            "delivery_date": o.delivery_date,
            "delivery_slot": o.delivery_slot,
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "items_summary": summary,
        })

    return ApiResponse(data={"items": items, "total": total, "page": page})


# ════════════════════════════════════════════════════════════
# 【取消订单】
# ════════════════════════════════════════════════════════════

@router.post(
    "/{order_no}/cancel",
    response_model=ApiResponse[dict],
    summary="取消订单",
    description="只有「待支付」和「已支付」状态可以取消",
)
async def cancel_order(
    order_no: str,
    service: OrderServiceDep,
    reason: str = Query("用户取消", description="取消原因"),
):
    """
    【干什么】取消订单。

    【注意】
    配花中之后不能取消（花已经做了），要走售后流程。
    """
    order = await service.cancel_order(order_no, reason=reason)

    return ApiResponse(data={
        "order_no": order.order_no,
        "status": order.status,
        "status_text": STATUS_TEXT.get(order.status, order.status),
    })


# ════════════════════════════════════════════════════════════
# 【后台：推进订单状态】
# ════════════════════════════════════════════════════════════

@router.post(
    "/{order_no}/status",
    response_model=ApiResponse[dict],
    summary="【后台】推进订单状态",
    description="带白名单校验，非法流转会被拒绝",
)
async def update_status(
    service: OrderServiceDep,
    order_no: str,
    to_status: str = Query(..., description="目标状态"),
    reason: str = Query("后台手动推进", description="原因"),
    operator: str = Query("admin", description="操作方"),
):
    """
    【干什么】后台手动推进订单状态。

    【白名单校验】
    只能按合法路径推进，不能跳步。
        待支付 → 已支付 → 配花中 → 配送中 → 已送达 → 已完成
    """
    order = await service.transition_status(
        order_no,
        to_status,
        reason=reason,
        operator=operator,
    )

    return ApiResponse(data={
        "order_no": order.order_no,
        "status": order.status,
        "status_text": STATUS_TEXT.get(order.status, order.status),
    })
