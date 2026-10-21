# ============================================================
# 【这个文件是干什么的】
# 售后工单表的 ORM 模型。
#
# 【工单是什么】
# 用户收到花后有问题（破损、送晚、送错、质量差），
# 提交一个工单，客服跟进处理，处理完关闭。
#
# 【为什么不能直接在订单上改状态】
# 售后是一个独立流程，可能反复沟通多次。
# 单独建表，一个订单可以有多张工单，每张工单有完整对话记录。
# ============================================================

from enum import StrEnum

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TicketType(StrEnum):
    """售后类型"""

    DAMAGED = "damaged"       # 花材破损
    LATE = "late"             # 配送延迟
    WRONG = "wrong"           # 送错地址/送错花
    QUALITY = "quality"       # 花材质量差
    OTHER = "other"           # 其他


class TicketStatus(StrEnum):
    """工单状态"""

    SUBMITTED = "submitted"   # 已提交，待客服处理
    PROCESSING = "processing"  # 客服处理中
    RESOLVED = "resolved"     # 已解决
    CLOSED = "closed"         # 已关闭（用户确认或超时）


class Ticket(Base):
    """
    【干什么】售后工单表。

    【一行代表什么】
    用户提交的一次售后申请。
    """

    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(
        String(40),
        primary_key=True,
        comment="工单 ID",
    )

    ticket_no: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        comment="工单号，如 TK2026102015123",
    )

    # ── 关联订单 ──
    order_id: Mapped[str] = mapped_column(
        String(40),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="关联订单",
    )

    order_no: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        comment="订单号（冗余，方便查）",
    )

    # ── 用户 ──
    user_id: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
        comment="提交人（游客为空）",
    )

    contact_phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="联系电话",
    )

    # ── 问题 ──
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TicketType.OTHER.value,
        index=True,
        comment="类型：damaged/late/wrong/quality/other",
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="问题描述",
    )

    images: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="问题图片（JSON 数组）",
    )

    # ── 处理 ──
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TicketStatus.SUBMITTED.value,
        index=True,
        comment="工单状态",
    )

    reply: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="客服回复",
    )

    solution: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="处理方案：resend=补送 / refund=退款 / partial_refund=部分退款 / none=无需处理",
    )

    operator: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="处理人",
    )

    resolved_at: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="解决时间",
    )

    __table_args__ = (
        Index("idx_tickets_status_created", "status", "created_at"),
        Index("idx_tickets_order", "order_no"),
        {"comment": "售后工单表"},
    )

    def __repr__(self) -> str:
        return f"<Ticket {self.ticket_no} {self.type} {self.status}>"
