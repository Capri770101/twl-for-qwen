# ============================================================
# 【这个文件是干什么的】
# 售后工单的接口。
# ============================================================

from fastapi import APIRouter, Query

from app.api.deps import DbDep, TicketServiceDep
from app.repositories import TicketRepository
from app.schemas import (
    ApiResponse,
    TicketCreate,
    TicketCreateResult,
    TicketOut,
    TicketReply,
)

router = APIRouter(prefix="/tickets", tags=["售后"])


# ════════════════════════════════════════════════════════════
# 【提交售后】
# ════════════════════════════════════════════════════════════

@router.post(
    "",
    response_model=ApiResponse[TicketCreateResult],
    summary="提交售后申请",
    description="花材破损、配送延迟、送错、质量问题，都走这个接口",
)
async def create_ticket(data: TicketCreate, service: TicketServiceDep):
    """
    【干什么】用户提交售后申请。

    【返回】
        工单号 + 预计响应时间

    【注意】
        同一个订单同时只能有一张处理中的工单，
        重复提交会返回 409。
    """
    result = await service.create_ticket(data)
    return ApiResponse(data=result)


# ════════════════════════════════════════════════════════════
# 【查询工单】
# ════════════════════════════════════════════════════════════

@router.get(
    "/{ticket_no}",
    response_model=ApiResponse[TicketOut],
    summary="工单详情",
)
async def get_ticket(ticket_no: str, service: TicketServiceDep):
    """
    【干什么】按工单号查详情。
    """
    ticket = await service.get_ticket(ticket_no)
    return ApiResponse(data=TicketOut.model_validate(ticket))


@router.get(
    "",
    response_model=ApiResponse[dict],
    summary="【后台】工单列表",
    description="可按状态筛选",
)
async def list_tickets(
    db: DbDep,
    status: str | None = Query(None, description="状态：submitted/processing/resolved/closed"),
    limit: int = Query(100, ge=1, le=500),
):
    """
    【干什么】查工单列表（后台用）。
    """
    repo = TicketRepository(db)
    tickets = await repo.list_tickets(status=status, limit=limit)

    return ApiResponse(data={
        "items": [
            {
                "ticket_no": t.ticket_no,
                "order_no": t.order_no,
                "type": t.type,
                "reason": t.reason,
                "status": t.status,
                "reply": t.reply,
                "solution": t.solution,
                "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for t in tickets
        ],
        "total": len(tickets),
    })


# ════════════════════════════════════════════════════════════
# 【客服回复】
# ════════════════════════════════════════════════════════════

@router.post(
    "/{ticket_no}/reply",
    response_model=ApiResponse[TicketOut],
    summary="【后台】回复工单",
    description="TODO: 上线前必须加客服鉴权",
)
async def reply_ticket(
    ticket_no: str,
    data: TicketReply,
    service: TicketServiceDep,
):
    """
    【干什么】客服回复工单。

    【处理方案】
        resend         —— 补送
        refund         —— 全额退款
        partial_refund —— 部分退款
        none           —— 无需处理
    """
    ticket = await service.reply_ticket(ticket_no, data)
    return ApiResponse(data=TicketOut.model_validate(ticket))
