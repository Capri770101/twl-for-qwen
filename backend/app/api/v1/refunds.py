# ============================================================
# 【这个文件是干什么的】
# 退款相关的接口。
# ============================================================

from fastapi import APIRouter, Query

from app.api.deps import AdminDep, DbDep
from app.models.refund import REFUND_STATUS_TEXT
from app.schemas import ApiResponse
from app.schemas.refund import (
    RefundBrief,
    RefundCreate,
    RefundOut,
    RefundReview,
    RefundReviewResult,
)
from app.services.refund_service import RefundService

router = APIRouter(prefix="/refunds", tags=["退款"])


def _to_out(r) -> RefundOut:
    """ORM → RefundOut"""
    return RefundOut(
        id=r.id,
        refund_no=r.refund_no,
        order_no=r.order_no,
        ticket_no=r.ticket_no,
        user_id=r.user_id,
        amount=r.amount,
        order_amount=r.order_amount,
        status=r.status,
        status_text=REFUND_STATUS_TEXT.get(r.status, r.status),
        reason=r.reason,
        reject_reason=r.reject_reason,
        channel=r.channel,
        external_ref=r.external_ref,
        error_message=r.error_message,
        operator=r.operator,
        applied_at=r.applied_at,
        reviewed_at=r.reviewed_at,
        refunded_at=r.refunded_at,
        is_demo=r.is_demo,
    )


def _to_brief(r) -> RefundBrief:
    """ORM → RefundBrief"""
    return RefundBrief(
        refund_no=r.refund_no,
        order_no=r.order_no,
        amount=r.amount,
        status=r.status,
        status_text=REFUND_STATUS_TEXT.get(r.status, r.status),
        reason=r.reason,
        applied_at=r.applied_at,
        is_demo=r.is_demo,
    )


# ════════════════════════════════════════════════════════════
# 【用户侧】
# ════════════════════════════════════════════════════════════

@router.post(
    "",
    response_model=ApiResponse[RefundOut],
    summary="申请退款",
    description="用户提交退款申请。校验订单状态、金额、时效。",
)
async def create_refund(
    data: RefundCreate,
    db: DbDep,
) -> ApiResponse[RefundOut]:
    """申请退款"""
    svc = RefundService(db)
    refund = await svc.create_refund(data)

    return ApiResponse(data=_to_out(refund))


@router.get(
    "/order/{order_no}",
    response_model=ApiResponse[list[RefundBrief]],
    summary="查订单的退款记录",
)
async def list_order_refunds(
    order_no: str,
    db: DbDep,
) -> ApiResponse[list[RefundBrief]]:
    """查某笔订单的所有退款单"""
    svc = RefundService(db)
    refunds = await svc.get_order_refunds(order_no)

    return ApiResponse(data=[_to_brief(r) for r in refunds])


@router.get(
    "/{refund_no}",
    response_model=ApiResponse[RefundOut],
    summary="退款单详情",
)
async def get_refund(
    refund_no: str,
    db: DbDep,
) -> ApiResponse[RefundOut]:
    """退款单详情"""
    svc = RefundService(db)
    refund = await svc.get_refund(refund_no)

    return ApiResponse(data=_to_out(refund))


# ════════════════════════════════════════════════════════════
# 【后台】
# ════════════════════════════════════════════════════════════

@router.get(
    "",
    response_model=ApiResponse[dict],
    summary="【后台】退款单列表",
)
async def list_refunds(
    admin: AdminDep,
    db: DbDep,
    status: str | None = Query(None, description="按状态筛选"),
    order_no: str | None = Query(None, description="按订单号筛选"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> ApiResponse[dict]:
    """退款单列表"""
    svc = RefundService(db)
    items, total = await svc.list_refunds(
        status=status,
        order_no=order_no,
        page=page,
        size=size,
    )

    return ApiResponse(data={
        "items": [_to_brief(r).model_dump() for r in items],
        "total": total,
        "page": page,
        "size": size,
    })


@router.post(
    "/{refund_no}/review",
    response_model=ApiResponse[RefundReviewResult],
    summary="【后台】审核退款",
    description="通过时自动调支付网关退款。失败会记录原因，可重试。",
)
async def review_refund(
    refund_no: str,
    data: RefundReview,
    admin: AdminDep,
    db: DbDep,
) -> ApiResponse[RefundReviewResult]:
    """审核退款"""
    svc = RefundService(db)

    # 审核人用管理员手机号（脱敏后）
    operator = getattr(admin, "phone", None) or getattr(admin, "id", "admin")

    refund = await svc.review_refund(refund_no, data, operator)

    return ApiResponse(data=RefundReviewResult(
        refund_no=refund.refund_no,
        status=refund.status,
        status_text=REFUND_STATUS_TEXT.get(refund.status, refund.status),
        external_ref=refund.external_ref,
        error_message=refund.error_message,
    ))


@router.post(
    "/{refund_no}/retry",
    response_model=ApiResponse[RefundReviewResult],
    summary="【后台】重试退款",
    description="只对 status=failed 的退款单有效",
)
async def retry_refund(
    refund_no: str,
    admin: AdminDep,
    db: DbDep,
) -> ApiResponse[RefundReviewResult]:
    """重试退款"""
    svc = RefundService(db)
    refund = await svc.retry_refund(refund_no)

    return ApiResponse(data=RefundReviewResult(
        refund_no=refund.refund_no,
        status=refund.status,
        status_text=REFUND_STATUS_TEXT.get(refund.status, refund.status),
        external_ref=refund.external_ref,
        error_message=refund.error_message,
    ))
