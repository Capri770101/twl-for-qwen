# ============================================================
# 【这个文件是干什么的】
# 履约推送相关的接口。
#
# 【谁调这些接口】
# - notify          我们自己调（订单支付成功后）
# - callback        履约方调我们（回传配送状态）
# ============================================================

from fastapi import APIRouter, Query

from app.api.deps import AdminDep, DbDep, DeliveryServiceDep
from app.models.payment import DELIVERY_STATUS_TEXT
from app.schemas import ApiResponse, DeliveryNotifyResult

router = APIRouter(prefix="/deliveries", tags=["履约"])


# ════════════════════════════════════════════════════════════
# 【推送订单给履约方】
# ════════════════════════════════════════════════════════════

@router.post(
    "/notify",
    response_model=ApiResponse[DeliveryNotifyResult],
    summary="推送订单给履约方",
    description="订单支付成功后调用，把订单信息推给做花送花的一方",
)
async def notify_fulfillment(
    service: DeliveryServiceDep,
    order_no: str = Query(..., description="订单号"),
):
    """
    【干什么】把已支付的订单推给履约方。

    【流程】
        1. 检查订单是「已支付」状态
        2. 组装推送内容
        3. 调适配器推送（当前 Mock）
        4. 记配送单
        5. 订单状态改为「配花中」

    【可能失败】
        订单不存在 → 404
        订单状态不对 → 409
        推送失败 → 422
    """
    result = await service.notify_fulfillment(order_no)
    return ApiResponse(data=result)


# ════════════════════════════════════════════════════════════
# 【履约方回传状态】
#
# 【真实环境谁调】
# 履约方的系统会 POST 到这里，告诉我们"出发了"或"送到了"。
#
# 【生产环境必须做鉴权】
# 现在的实现没有验证调用方身份，生产环境要加 API Key 或签名校验。
# ════════════════════════════════════════════════════════════

@router.post(
    "/callback",
    response_model=ApiResponse[dict],
    summary="履约方状态回传",
    description="履约方调用，回传 delivering(出发) 或 delivered(送达)。TODO: 上线前加鉴权。",
)
async def delivery_callback(
    service: DeliveryServiceDep,
    order_no: str = Query(..., description="订单号"),
    status: str = Query(..., description="状态：delivering 或 delivered"),
):
    """
    【干什么】履约方回传配送状态。

    【状态流转】
        preparing → delivering → delivered

    【非法流转会被拒绝】
    比如还没配花中就直接报「已送达」，会被拒绝。
    """
    await service.handle_callback(order_no, status)

    return ApiResponse(data={
        "order_no": order_no,
        "status": status,
        "received": True,
    })


# ════════════════════════════════════════════════════════════
# 【查询配送单】
# ════════════════════════════════════════════════════════════

@router.get(
    "/{order_no}",
    response_model=ApiResponse[dict],
    summary="查配送单",
    description="查看这个订单推给履约方的完整内容和状态",
)
async def get_delivery(order_no: str, service: DeliveryServiceDep):
    """
    【干什么】查这个订单的配送单。

    【什么时候用】
    履约方说"没收到这个单"，查一下推了什么过去、什么时候推的。
    """
    delivery = await service.delivery_repo.get_latest_by_order(order_no)

    if delivery is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("配送单不存在")

    return ApiResponse(data={
        "id": delivery.id,
        "order_no": delivery.order_no,
        "provider": delivery.provider,
        "status": delivery.status,
        "external_ref": delivery.external_ref,
        "payload": delivery.payload,
        "response": delivery.response,
        "sent_at": delivery.sent_at,
        "error_message": delivery.error_message,
        "created_at": delivery.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    })

# ════════════════════════════════════════════════════════════
# 【后台：配送单列表】
# ════════════════════════════════════════════════════════════

@router.get(
    "",
    response_model=ApiResponse[dict],
    summary="【后台】配送单列表",
)
async def list_deliveries(
    admin: AdminDep,
    service: DeliveryServiceDep,
    status: str | None = Query(None, description="按状态筛选"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """配送单列表"""
    items, total = await service.list_deliveries(status=status, page=page, size=size)

    return ApiResponse(data={
        "items": [
            {
                "id": d.id,
                "order_no": d.order_no,
                "provider": d.provider,
                "status": d.status,
                "status_text": DELIVERY_STATUS_TEXT.get(d.status, d.status),
                "external_ref": d.external_ref,
                "sent_at": d.sent_at,
                "error_message": d.error_message,
            }
            for d in items
        ],
        "total": total,
        "page": page,
        "size": size,
    })


# ════════════════════════════════════════════════════════════
# 【后台：重推配送】
# ════════════════════════════════════════════════════════════

@router.post(
    "/{order_no}/retry",
    response_model=ApiResponse[dict],
    summary="【后台】重推配送",
    description="推送失败后人工重试。只对 failed / pending 状态有效。",
)
async def retry_delivery(
    order_no: str,
    admin: AdminDep,
    service: DeliveryServiceDep,
):
    """重推配送"""
    result = await service.retry_delivery(order_no)

    return ApiResponse(data={
        "order_no": order_no,
        "result": result.model_dump() if hasattr(result, "model_dump") else result,
    })
