# ============================================================
# 【这个文件是干什么的】
# 订单相关的三张表：订单主表、订单明细、状态日志。
#
# 【三张表的分工】
#   orders       —— 一笔订单的全部信息（谁买、寄给谁、多少钱、什么状态）
#   order_items  —— 这笔订单买了哪几个商品（一单可以多件）
#   order_logs   —— 这笔订单的状态怎么变的（什么时候、为什么、谁操作的）
#
# 【为什么明细要单独一张表】
# 如果塞在 orders 表里（比如存成 JSON），
# 就没法按商品统计销量、没法做库存核算。
# 单独建表，每个商品一行，方便统计。
# ============================================================

from decimal import Decimal
from enum import StrEnum

from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ════════════════════════════════════════════════════════════
# 【订单状态枚举】
#
# 【为什么要用枚举】
# 状态是系统的骨架，写错一个字母整个流程就断了。
# 用枚举，拼错会立刻报错。
# ════════════════════════════════════════════════════════════
class OrderStatus(StrEnum):
    """订单状态。流转规则见 order_service.py 的 TRANSITIONS。"""

    PENDING_PAYMENT = "pending_payment"   # 待支付
    PAID = "paid"                          # 已支付
    PREPARING = "preparing"                # 配花中
    DELIVERING = "delivering"              # 配送中
    DELIVERED = "delivered"                # 已送达
    COMPLETED = "completed"                # 已完成
    CANCELLED = "cancelled"                # 已取消


# 状态的中文名（给前端显示用）
STATUS_TEXT: dict[str, str] = {
    OrderStatus.PENDING_PAYMENT: "待支付",
    OrderStatus.PAID: "已支付",
    OrderStatus.PREPARING: "配花中",
    OrderStatus.DELIVERING: "配送中",
    OrderStatus.DELIVERED: "已送达",
    OrderStatus.COMPLETED: "已完成",
    OrderStatus.CANCELLED: "已取消",
}


class Order(Base):
    """
    【干什么】订单主表。

    【一行代表什么】
    一笔订单。用户提交一次订单就有这一行。

    【金额单位】
    全部用 Numeric(10,2)，单位是元，精确到分。
    例：Decimal("299.00")
    """

    __tablename__ = "orders"

    # ── 主键 ──
    id: Mapped[str] = mapped_column(
        String(40),
        primary_key=True,
        comment="内部 ID（不对外）",
    )

    order_no: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        comment="订单号（对外唯一标识），如 TWL20261020135005B35B",
    )

    # ── 归属 ──
    user_id: Mapped[str | None] = mapped_column(
        String(40),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="下单用户（游客下单为空）",
    )

    # ── 状态 ──
    status: Mapped[str] = mapped_column(
        String(24),
        nullable=False,
        default=OrderStatus.PENDING_PAYMENT.value,
        index=True,
        comment="订单状态",
    )

    # ── 金额（单位：元）──
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="商品总额",
    )

    delivery_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="运费",
    )

    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="优惠金额",
    )

    pay_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="应付总额 = 商品 + 运费 - 优惠",
    )

    # ── 收花人 ──
    receiver: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="收花人姓名",
    )

    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="收花人手机号",
    )

    province: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="省")
    city: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="市")
    district: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="区")
    address_detail: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        comment="详细地址",
    )

    # ── 配送 ──
    delivery_date: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="配送日期，如 2026-10-21",
    )

    delivery_slot: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
        comment="配送时段，如 18:00-20:00",
    )

    # ── 附加信息 ──
    card_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="贺卡留言",
    )

    anonymous: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        comment="是否匿名送花",
    )

    # ── 演示标记 ──
    is_demo: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        index=True,
        comment="是否演示订单（交付环境用）",
    )

    remark: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="订单备注",
    )

    # ── 支付 ──
    pay_channel: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="支付渠道：wechat/alipay/mock",
    )

    paid_at: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="支付成功时间",
    )

    # ── 超时 ──
    expire_at: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="支付截止时间，超时自动取消",
    )

    # ── 关系 ──
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",     # 查订单时自动带出明细，不用额外查询
    )

    logs: Mapped[list["OrderLog"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderLog.created_at",
        lazy="selectin",
    )

    # ── 索引 ──
    __table_args__ = (
        Index("idx_orders_status_created", "status", "created_at"),
        Index("idx_orders_user_created", "user_id", "created_at"),
        {"comment": "订单主表"},
    )

    def __repr__(self) -> str:
        return f"<Order {self.order_no} {self.status} ¥{self.pay_amount}>"


class OrderItem(Base):
    """
    【干什么】订单明细表。

    【一行代表什么】
    订单里的一个商品。

    【为什么存 name 和 price 快照】
    商品改名字、改价格之后，历史订单不能跟着变。
    所以下单时把当时的名字和单价存下来。
    """

    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(
        String(40),
        primary_key=True,
        comment="明细 ID",
    )

    order_id: Mapped[str] = mapped_column(
        String(40),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属订单",
    )

    product_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        comment="商品 ID",
    )

    # ── 快照字段（下单时的值，不随商品变化）──
    product_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="商品名快照",
    )

    product_cover: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="商品图快照",
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="下单时的单价",
    )

    qty: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="数量",
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="小计 = 单价 × 数量",
    )

    # ── 关系 ──
    order: Mapped["Order"] = relationship(back_populates="items")

    def __repr__(self) -> str:
        return f"<OrderItem {self.product_name}×{self.qty}>"


class OrderLog(Base):
    """
    【干什么】订单状态日志。

    【一行代表什么】
    订单状态变化的一次记录。

    【为什么必须有这张表】
    出问题时（用户说「我明明付了钱」），
    查这张表就知道：什么时候付的、走的什么渠道、系统怎么处理的。
    这是排查和追责的唯一依据。
    """

    __tablename__ = "order_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="自增 ID",
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
        comment="订单号（冗余一份，方便直接查）",
    )

    from_status: Mapped[str | None] = mapped_column(
        String(24),
        nullable=True,
        comment="原状态（首次为空）",
    )

    to_status: Mapped[str] = mapped_column(
        String(24),
        nullable=False,
        comment="新状态",
    )

    reason: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="变化原因",
    )

    operator: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="system",
        comment="操作方：system/user/payment/delivery/admin",
    )

    extra: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="附加信息（JSON）",
    )

    # ── 关系 ──
    order: Mapped["Order"] = relationship(back_populates="logs")

    __table_args__ = (
        Index("idx_order_logs_order_created", "order_no", "created_at"),
        {"comment": "订单状态日志"},
    )

    def __repr__(self) -> str:
        return f"<OrderLog {self.order_no} {self.from_status}→{self.to_status}>"
