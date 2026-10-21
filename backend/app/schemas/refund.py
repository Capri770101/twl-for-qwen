# ============================================================
# 【这个文件是干什么的】
# 退款的请求格式和响应格式。
# ============================================================

from datetime import datetime
from decimal import Decimal

from pydantic import Field, field_validator

from app.schemas.common import BaseSchema


# ════════════════════════════════════════════════════════════
# 【申请退款】
# ════════════════════════════════════════════════════════════

class RefundCreate(BaseSchema):
    """用户申请退款"""

    order_no: str = Field(..., max_length=32, description="订单号")

    amount: Decimal = Field(
        ...,
        gt=0,
        description="退款金额（元）。全额退款就填实付金额",
    )

    reason: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="退款原因",
    )

    ticket_no: str | None = Field(
        None,
        max_length=32,
        description="关联的售后工单号（可选）",
    )

    contact_phone: str | None = Field(None, description="联系电话")


# ════════════════════════════════════════════════════════════
# 【审核】
# ════════════════════════════════════════════════════════════

class RefundReview(BaseSchema):
    """后台审核退款"""

    approve: bool = Field(..., description="true=通过，false=拒绝")

    reject_reason: str | None = Field(
        None,
        max_length=500,
        description="拒绝理由（approve=false 时必填）",
    )

    adjusted_amount: Decimal | None = Field(
        None,
        gt=0,
        description="调整后的退款金额（可选，不超过申请金额）",
    )

    @field_validator("reject_reason")
    @classmethod
    def check_reject_reason(cls, v: str | None) -> str | None:
        return v.strip() if v else None


# ════════════════════════════════════════════════════════════
# 【响应】
# ════════════════════════════════════════════════════════════

class RefundOut(BaseSchema):
    """退款单详情"""

    id: str
    refund_no: str
    order_no: str
    ticket_no: str | None = None
    user_id: str | None = None

    amount: Decimal
    order_amount: Decimal

    status: str
    status_text: str = ""

    reason: str
    reject_reason: str | None = None

    channel: str | None = None
    external_ref: str | None = None
    error_message: str | None = None

    operator: str | None = None

    applied_at: datetime
    reviewed_at: datetime | None = None
    refunded_at: datetime | None = None

    is_demo: bool = False


class RefundBrief(BaseSchema):
    """退款单简要（列表页）"""

    refund_no: str
    order_no: str
    amount: Decimal
    status: str
    status_text: str = ""
    reason: str
    applied_at: datetime
    is_demo: bool = False


class RefundReviewResult(BaseSchema):
    """审核结果"""

    refund_no: str
    status: str
    status_text: str
    external_ref: str | None = None
    error_message: str | None = None
