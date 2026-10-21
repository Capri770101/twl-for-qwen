# ============================================================
# 【这个文件是干什么的】
# 支付记录表和配送单表的 ORM 模型。
#
# 【为什么支付要单独一张表】
# 一个订单可能发起过多次支付（第一次失败、第二次成功）。
# 存在订单表里只能存最后一次，查不到历史。
# 单独建表，每次支付尝试都留痕，对账时用得上。
#
# 【为什么配送也要单独一张表】
# 推给履约方的完整内容需要留档。
# 万一对方说没收到、或者内容不对，能拿出证据。
# ============================================================

from decimal import Decimal
from enum import StrEnum

from sqlalchemy import ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# ════════════════════════════════════════════════════════════
# 【支付】
# ════════════════════════════════════════════════════════════

class PaymentStatus(StrEnum):
    """支付状态"""

    PENDING = "pending"       # 已发起，等结果
    SUCCESS = "success"       # 支付成功
    FAILED = "failed"         # 支付失败
    REFUNDED = "refunded"     # 已退款
    CLOSED = "closed"         # 已关闭（超时未付）


class PayChannel(StrEnum):
    """支付渠道"""

    WECHAT = "wechat"         # 微信支付
    ALIPAY = "alipay"         # 支付宝
    MOCK = "mock"             # 测试用


class Payment(Base):
    """
    【干什么】支付记录表。

    【一行代表什么】
    一次支付尝试。注意是「尝试」，不是「订单」。
    同一订单可以有多次支付记录。
    """

    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(
        String(40),
        primary_key=True,
        comment="支付记录 ID",
    )

    order_id: Mapped[str] = mapped_column(
        String(40),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属订单",
    )

    order_no: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        comment="订单号（冗余，方便直接查）",
    )

    channel: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="支付渠道：wechat/alipay/mock",
    )

    trade_no: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="第三方交易号（微信/支付宝返回）",
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="支付金额",
    )

    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=PaymentStatus.PENDING.value,
        index=True,
        comment="支付状态",
    )

    # ── 回调原始数据 ──
    raw_callback: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="回调原始内容（排查问题用）",
    )

    paid_at: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="支付成功时间",
    )

    __table_args__ = (
        Index("idx_payments_order_status", "order_no", "status"),
        {"comment": "支付记录表"},
    )

    def __repr__(self) -> str:
        return f"<Payment {self.order_no} {self.channel} {self.status}>"


# ════════════════════════════════════════════════════════════
# 【配送】
# ════════════════════════════════════════════════════════════

class DeliveryStatus(StrEnum):
    """配送单状态"""

    PENDING = "pending"       # 待推送
    SENT = "sent"             # 已推送
    ACCEPTED = "accepted"     # 对方已接单
    DELIVERING = "delivering"  # 配送中
    DELIVERED = "delivered"   # 已送达
    FAILED = "failed"         # 推送失败

# 配送状态中文映射
DELIVERY_STATUS_TEXT: dict[str, str] = {
    "pending": "待推送",
    "sent": "已推送",
    "accepted": "已接单",
    "delivering": "配送中",
    "delivered": "已送达",
    "failed": "推送失败",
}



class Delivery(Base):
    """
    【干什么】配送单表 —— 记录每次推给履约方的完整内容。

    【一行代表什么】
    一次推送给履约方的记录。

    【为什么要存 payload】
    万一对方说「我没收到这个单」或者「内容不对」，
    能拿出当时发过去的完整内容作为证据。
    """

    __tablename__ = "deliveries"

    id: Mapped[str] = mapped_column(
        String(40),
        primary_key=True,
        comment="配送单 ID",
    )

    order_id: Mapped[str] = mapped_column(
        String(40),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属订单",
    )

    order_no: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        comment="订单号",
    )

    provider: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="mock",
        comment="履约方类型：mock/real",
    )

    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=DeliveryStatus.PENDING.value,
        index=True,
        comment="配送单状态",
    )

    external_ref: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="对方系统返回的单号",
    )

    payload: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="推送的完整内容",
    )

    response: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="对方的响应内容",
    )

    sent_at: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="推送时间",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="失败原因",
    )

    __table_args__ = (
        Index("idx_deliveries_order", "order_no", "created_at"),
        {"comment": "配送单表"},
    )

    def __repr__(self) -> str:
        return f"<Delivery {self.order_no} {self.status}>"
