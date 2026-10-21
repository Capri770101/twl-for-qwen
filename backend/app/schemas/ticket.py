# ============================================================
# 【这个文件是干什么的】
# 售后工单接口的请求/响应格式。
# ============================================================

from datetime import datetime

from pydantic import Field

from app.schemas.common import BaseSchema


# ════════════════════════════════════════════════════════════
# 【提交售后】
# ════════════════════════════════════════════════════════════

class TicketCreate(BaseSchema):
    """提交售后申请"""

    order_no: str = Field(..., description="订单号")
    type: str = Field(
        "other",
        description="类型：damaged(破损) / late(延迟) / wrong(送错) / quality(质量) / other(其他)",
    )
    reason: str = Field(..., min_length=5, max_length=1000, description="问题描述")
    images: list[str] | None = Field(None, max_length=9, description="问题图片（最多9张）")
    contact_phone: str | None = Field(None, description="联系电话")


class TicketCreateResult(BaseSchema):
    """提交售后后返回"""

    ticket_no: str = Field(..., description="工单号")
    status: str = Field(..., description="工单状态")
    message: str = Field(..., description="提示信息")
    expected_response_time: str = Field(..., description="预计响应时间")


# ════════════════════════════════════════════════════════════
# 【工单查询】
# ════════════════════════════════════════════════════════════

class TicketOut(BaseSchema):
    """工单详情"""

    id: str
    ticket_no: str
    order_no: str
    type: str
    reason: str
    images: list[str] | None = None
    status: str
    reply: str | None = None
    solution: str | None = None
    contact_phone: str | None = None
    operator: str | None = None
    resolved_at: str | None = None
    created_at: datetime


class TicketBrief(BaseSchema):
    """工单简要信息（列表页）"""

    ticket_no: str
    order_no: str
    type: str
    reason: str
    status: str
    created_at: datetime


# ════════════════════════════════════════════════════════════
# 【客服回复】
# ════════════════════════════════════════════════════════════

class TicketReply(BaseSchema):
    """客服回复工单"""

    reply: str = Field(..., min_length=1, max_length=2000, description="回复内容")
    solution: str | None = Field(
        None,
        description="处理方案：resend(补送) / refund(退款) / partial_refund(部分退款) / none(无需处理)",
    )
    status: str = Field("resolved", description="处理后状态：processing/resolved/closed")


# ════════════════════════════════════════════════════════════
# 【配送推送】
# ════════════════════════════════════════════════════════════

class DeliveryNotifyResult(BaseSchema):
    """推送履约方后的结果"""

    delivery_id: str
    order_no: str
    status: str = Field(..., description="配送单状态")
    provider: str = Field(..., description="履约方类型")
    external_ref: str | None = Field(None, description="对方返回的单号")
    message: str = Field("", description="提示信息")
