# ============================================================
# 【这个文件是干什么的】
# 商品表的 ORM 模型。
#
# 【ORM 是什么】
# Object-Relational Mapping，对象关系映射。
# 用 Python 类操作数据库，不用手写 SQL。
#   Product(name="玫瑰", price=29900)  ←→  INSERT INTO products ...
#
# 【跟数据库的关系】
# 这个类对应数据库里的 products 表。
# 改这个类之后，要生成迁移文件（alembic revision）再升级数据库。
# ============================================================

from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProductCategory(StrEnum):
    """
    【干什么】商品分类。

    【为什么要用枚举】
    防止写错。定义成枚举后，只能填这几个值，
    拼错了会报错，不会出现 "love" 和 "loves" 两种数据。
    """

    DAILY = "daily"           # 日常
    LOVE = "love"             # 告白
    BIRTHDAY = "birthday"     # 生日
    SYMPATHY = "sympathy"     # 探望
    BUSINESS = "business"     # 商务


class ProductStatus(StrEnum):
    """商品状态"""

    ON = "on"                 # 上架可售
    OFF = "off"               # 下架


class Product(Base):
    """
    【干什么】商品表。

    【一行代表什么】
    一个可售卖的花束。

    【字段说明】
    见每个字段的 comment。

    【关于价格】
    用 Numeric(10, 2) 存元，不用整数存分。
    为什么？PostgreSQL 的 Numeric 是精确小数，
    不会像 float 那样有精度问题。
    读取时是 Decimal 类型，避免浮点误差。
    """

    __tablename__ = "products"

    # ── 主键 ──
    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        comment="商品编号，如 TW-001",
    )

    # ── 基本信息 ──
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="商品名称",
    )

    subtitle: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="副标题，如「香槟玫瑰 20 枝」",
    )

    # ── 价格（单位：元）──
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="售价（元）",
    )

    original_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="原价/划线价（元）",
    )

    # ── 媒体 ──
    cover: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="主图 URL",
    )

    images: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="详情图数组（JSON）",
    )

    # ── 内容 ──
    flowers: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="花材清单（JSON 数组）",
    )

    meaning: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="花语",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="商品描述（详情页正文）",
    )

    # ── 分类与状态 ──
    category: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ProductCategory.DAILY.value,
        index=True,
        comment="分类：daily/love/birthday/sympathy/business",
    )

    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=ProductStatus.ON.value,
        index=True,
        comment="状态：on=上架 / off=下架",
    )

    # ── 库存 ──
    stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=999,
        comment="库存数量",
    )

    # ── 排序 ──
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="排序权重，越小越靠前",
    )

    # ── 索引 ──
    __table_args__ = (
        Index("idx_products_category_status", "category", "status"),
        Index("idx_products_sort", "sort_order", "created_at"),
        {"comment": "商品表"},
    )

    def __repr__(self) -> str:
        return f"<Product {self.id} {self.name} ¥{self.price}>"
