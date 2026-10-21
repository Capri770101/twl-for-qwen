# ============================================================
# 【这个文件是干什么的】
# 用户表和地址簿表的 ORM 模型。
#
# 【当前状态】
# 用户表本期预留（支持游客下单，不强制登录）。
# 后续接入微信登录后启用。
#
# 【为什么要提前建表】
# 订单表要用 user_id 外键指向用户表。
# 先把表结构定下来，以后接入登录不用改订单表。
# ============================================================

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """
    【干什么】用户表。

    【一行代表什么】
    一个注册用户。

    【当前怎么用】
    游客下单时 user_id 为空。
    接入微信登录后，登录用户的订单会带上 user_id。
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(40),
        primary_key=True,
        comment="用户 ID",
    )

    # ── 外部渠道身份 ──
    external_id: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
        comment="外部渠道用户 ID（如微信 openid）",
    )

    channel: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="来源渠道：wechat/phone/guest",
    )

    # ── 基本信息 ──
    nickname: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="昵称",
    )

    avatar: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="头像 URL",
    )

    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="手机号",
    )

    # ── 状态 ──
    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        comment="是否启用",
    )

    is_admin: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        index=True,
        comment="是否管理员（能进后台）",
    )

    # ── 关系 ──
    addresses: Mapped[list["Address"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_users_phone", "phone"),
        {"comment": "用户表"},
    )

    def __repr__(self) -> str:
        return f"<User {self.id} {self.nickname or self.phone or 'guest'}>"


class Address(Base):
    """
    【干什么】地址簿表。

    【一行代表什么】
    用户保存的一个收货地址。

    【当前怎么用】
    本期前台是直接填地址，不存地址簿。
    后续做「常用地址」功能时启用。
    """

    __tablename__ = "addresses"

    id: Mapped[str] = mapped_column(
        String(40),
        primary_key=True,
        comment="地址 ID",
    )

    user_id: Mapped[str] = mapped_column(
        String(40),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属用户",
    )

    # ── 收件人 ──
    receiver: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="收件人姓名",
    )

    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="收件人手机号",
    )

    # ── 地址 ──
    province: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="省")
    city: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="市")
    district: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="区")
    detail: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        comment="详细地址",
    )

    # ── 标记 ──
    tag: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="标签：家/公司/学校",
    )

    is_default: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        comment="是否默认地址",
    )

    # ── 关系 ──
    user: Mapped["User"] = relationship(back_populates="addresses")

    __table_args__ = (
        Index("idx_addresses_user", "user_id", "is_default"),
        {"comment": "地址簿表"},
    )

    def __repr__(self) -> str:
        return f"<Address {self.receiver} {self.detail[:20]}>"
