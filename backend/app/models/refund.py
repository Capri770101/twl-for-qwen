# ============================================================
# 【这个文件是干什么的】
# 退款单表。
#
# 【为什么单独一张表，不在订单表上加字段】
# 一笔订单可能退多次（部分退款、分次退款）。
# 放在订单表上只能记一个数，记不了流水。
#
# 【状态流转】
#   pending（已申请）
#     ├→ approved（审核通过）→ refunded（退款成功）
#     │                      └→ failed（退款失败，可重试）
#     └→ rejected（已拒绝）
#
# 【真实接入说明】
# 这张表不依赖支付网关。
# channel 记录原支付渠道，external_ref 记录网关返回的退款流水号。
# Mock 环境下 external_ref 是 MOCKREF+时间戳。
# ============================================================

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RefundStatus:
    """退款状态"""

    PENDING = "pending"       # 已申请，待审核
    APPROVED = "approved"     # 审核通过，待退款
    REJECTED = "rejected"     # 已拒绝
    REFUNDED = "refunded"     # 退款成功
    FAILED = "failed"         # 退款失败


REFUND_STATUS_TEXT = {
    "pending": "待审核",
    "approved": "待退款",
    "rejected": "已拒绝",
    "refunded": "已退款",
    "failed": "退款失败",
}


class Refund(Base):
    """
    【干什么】退款单。

    【一行代表什么】
    一次退款申请。

    【和订单的关系】
    多对一。一笔订单可以有多次退款（部分退款）。
    """

    __tablename__ = "refunds"

    # ── 主键 ──
    id: Mapped[str] = mapped_column(
        String(40),
        primary_key=True,
        comment="内部 ID",
    )

    refund_no: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        comment="退款单号，如 RF20261021143000ABCD",
    )

    # ── 关联 ──
    order_no: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        comment="订单号",
    )

    ticket_no: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        index=True,
        comment="关联的售后工单号（如果从工单发起）",
    )

    user_id: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
        index=True,
        comment="申请用户 ID（游客为空）",
    )

    # ── 金额 ──
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="退款金额（元）",
    )

    order_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="订单实付金额（元），用于校验",
    )

    # ── 状态 ──
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=RefundStatus.PENDING,
        index=True,
        comment="pending/approved/rejected/refunded/failed",
    )

    # ── 原因 ──
    reason: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="退款原因（用户填）",
    )

    reject_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="拒绝理由（后台填）",
    )

    # ── 支付网关 ──
    channel: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="原支付渠道：wechat/alipay/mock",
    )

    external_ref: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="网关退款流水号（真实接入时填）",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="退款失败原因",
    )

    # ── 操作人 ──
    operator: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="审核人（管理员手机号或 ID）",
    )

    # ── 时间 ──
    applied_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        comment="申请时间",
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        comment="审核时间",
    )

    refunded_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        comment="退款成功时间",
    )

    # ── 演示标记 ──
    is_demo: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        index=True,
        comment="是否演示数据",
    )

    # ── 索引 ──
    __table_args__ = (
        Index("idx_refunds_order_status", "order_no", "status"),
        {"comment": "退款单表"},
    )

    def __repr__(self) -> str:
        return f"<Refund {self.refund_no} ¥{self.amount} {self.status}>"
