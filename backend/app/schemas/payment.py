# ============================================================
# 【这个文件是干什么的】
# 支付接口的请求/响应格式。
# ============================================================

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.common import BaseSchema


# ════════════════════════════════════════════════════════════
# 【发起支付】
# ════════════════════════════════════════════════════════════

class PaymentCreate(BaseSchema):
    """发起支付的请求"""

    order_no: str = Field(..., description="订单号")
    channel: str = Field("wechat", description="支付渠道：wechat/alipay/mock")


class PaymentCreateResult(BaseSchema):
    """
    【干什么】发起支付后返回给前端的数据。

    【真实环境返回什么】
    微信：prepay_id、时间戳、随机串、签名（前端拿去调起微信支付）
    支付宝：一段表单 HTML 或跳转链接

    【现在返回什么】
    mock_pay_url —— 假的收银台地址
    """

    payment_id: str = Field(..., description="支付记录 ID")
    order_no: str = Field(..., description="订单号")
    channel: str = Field(..., description="支付渠道")
    amount: Decimal = Field(..., description="支付金额（元）")
    mock_pay_url: str | None = Field(None, description="【Mock 专用】模拟收银台地址")

    # 真实渠道的字段（现在为空，接入后填充）
    prepay_id: str | None = Field(None, description="微信预支付 ID")
    pay_sign: str | None = Field(None, description="支付签名")
    timestamp: str | None = Field(None, description="时间戳")
    nonce_str: str | None = Field(None, description="随机串")
    pay_url: str | None = Field(None, description="支付宝跳转地址")


# ════════════════════════════════════════════════════════════
# 【支付回调】
# ════════════════════════════════════════════════════════════

class PaymentCallback(BaseSchema):
    """
    【干什么】支付网关回调时传过来的数据。

    【注意】
    真实接入时字段要跟微信/支付宝的文档对齐。
    微信和支付宝字段名不一样，接的时候要改这个类。
    """

    order_no: str = Field(..., description="订单号")
    channel: str = Field("mock", description="渠道")
    trade_no: str | None = Field(None, description="第三方交易号")
    amount: Decimal = Field(..., description="支付金额（元）")
    success: bool = Field(True, description="是否成功")
    raw: dict | None = Field(None, description="原始回调内容")


class PaymentCallbackResult(BaseSchema):
    """回调处理结果"""

    order_no: str
    status: str = Field(..., description="订单处理后的状态")
    idempotent: bool = Field(False, description="是否为重复回调（已处理过）")


# ════════════════════════════════════════════════════════════
# 【支付记录查询】
# ════════════════════════════════════════════════════════════

class PaymentOut(BaseSchema):
    """支付记录"""

    id: str
    order_no: str
    channel: str
    trade_no: str | None = None
    amount: Decimal
    status: str
    paid_at: str | None = None
    created_at: datetime
