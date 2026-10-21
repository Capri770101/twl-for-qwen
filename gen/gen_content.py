# -*- coding: utf-8 -*-
"""生成文章 + 配置 + 上传模块"""

import os

B = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\backend"


# ══════════════════════════════════════════════════════════
# 1. models/content.py（文章 + 配置）
# ══════════════════════════════════════════════════════════
content_model = '''# ============================================================
# 【这个文件是干什么的】
# 内容表（花语文章）和配置表的 ORM 模型。
#
# 【为什么文章要入库】
# 花语百科是 SEO 的核心资产，20+ 篇文章。
# 放数据库里才能后台写、改、下线，不用改代码。
#
# 【为什么配置要入库】
# 免运费门槛、配送时段这些运营会改，
# 写死在代码里每次改都要发版。
# ============================================================

from sqlalchemy import Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Article(Base):
    """
    【干什么】花语文章表。

    【一行代表什么】
    一篇花语科普文章，如「香槟玫瑰的花语是什么」。

    【slug 是什么】
    网址里的短名，如 /flower-language/champagne-rose。
    用英文和短横线，利于 SEO。
    """

    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, comment="文章 ID")

    slug: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        nullable=False,
        index=True,
        comment="网址短名，如 champagne-rose",
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="标题")
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="摘要（列表页和 meta description 用）")

    content: Mapped[str] = mapped_column(Text, nullable=False, default="", comment="正文（Markdown 或 HTML）")

    cover: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="封面图 URL")

    category: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
        index=True,
        comment="分类：rose/tulip/sunflower 等",
    )

    # 花语一句话
    meaning: Mapped[str | None] = mapped_column(String(300), nullable=True, comment="花语一句话")

    # 标签数组
    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True, comment="标签数组")

    # FAQ 数组：[{question, answer}]
    faq: Mapped[list | None] = mapped_column(JSONB, nullable=True, comment="FAQ 数组，用于结构化数据")

    # 状态：draft / published / archived
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        index=True,
        comment="状态：draft/published/archived",
    )

    # SEO 字段
    seo_title: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="SEO 标题")
    seo_description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="SEO 描述")

    # 排序权重（数字越大越靠前）
    sort_weight: Mapped[int] = mapped_column(nullable=False, default=0, comment="排序权重")

    # 阅读数
    view_count: Mapped[int] = mapped_column(nullable=False, default=0, comment="阅读数")

    __table_args__ = (
        Index("idx_articles_status_weight", "status", "sort_weight"),
        {"comment": "花语文章表"},
    )

    def __repr__(self) -> str:
        return f"<Article {self.slug} {self.title[:20]}>"


class Setting(Base):
    """
    【干什么】系统配置表。

    【一行代表什么】
    一组配置，如「配送规则」。

    【为什么用 key-value + JSON】
    配置项会不断增加，每加一个就改表结构太麻烦。
    用 JSON 存一组配置，结构自己定。
    """

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(60), primary_key=True, comment="配置键，如 delivery")
    value: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, comment="配置值（JSON）")
    description: Mapped[str | None] = mapped_column(String(300), nullable=True, comment="说明")

    __table_args__ = ({"comment": "系统配置表"},)

    def __repr__(self) -> str:
        return f"<Setting {self.key}>"
'''

with open(os.path.join(B, "app/models/content.py"), "w", encoding="utf-8") as f:
    f.write(content_model)
print("  models/content.py")


# ══════════════════════════════════════════════════════════
# 2. schemas/content.py
# ══════════════════════════════════════════════════════════
content_schema = '''# ============================================================
# 【这个文件是干什么的】
# 文章和配置的请求/响应格式。
# ============================================================

from pydantic import Field

from app.schemas.common import BaseSchema


# ── 文章 ──

class ArticleIn(BaseSchema):
    """新增/修改文章的请求"""

    slug: str = Field(..., min_length=1, max_length=120, description="网址短名")
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    summary: str | None = Field(None, max_length=500, description="摘要")
    content: str = Field("", description="正文")
    cover: str | None = Field(None, max_length=500, description="封面图")
    category: str | None = Field(None, max_length=40, description="分类")
    meaning: str | None = Field(None, max_length=300, description="花语一句话")
    tags: list[str] | None = Field(None, description="标签")
    faq: list[dict] | None = Field(None, description="FAQ 数组")
    status: str = Field("draft", description="draft/published/archived")
    seo_title: str | None = Field(None, max_length=200)
    seo_description: str | None = Field(None, max_length=500)
    sort_weight: int = Field(0, description="排序权重")


class ArticleOut(BaseSchema):
    """文章信息（列表用，不含正文）"""

    id: str
    slug: str
    title: str
    summary: str | None = None
    cover: str | None = None
    category: str | None = None
    meaning: str | None = None
    tags: list | None = None
    status: str = "draft"
    view_count: int = 0


class ArticleDetailOut(ArticleOut):
    """文章详情（含正文和 FAQ）"""

    content: str = ""
    faq: list | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    sort_weight: int = 0


class ArticleListOut(BaseSchema):
    items: list[ArticleOut]
    total: int


# ── 配置 ──

class DeliverySetting(BaseSchema):
    """配送规则"""

    free_shipping_threshold: float = Field(199, description="免运费门槛（元）")
    base_shipping_fee: float = Field(15, description="基础运费（元）")
    remote_shipping_fee: float = Field(25, description="偏远地区运费（元）")
    same_city_hours: int = Field(2, description="同城配送时效（小时）")
    cutoff_hour: int = Field(16, description="当日达截止时间（点）")
    delivery_slots: list[str] = Field(
        default_factory=lambda: ["14:00-16:00", "18:00-20:00"],
        description="可选配送时段",
    )
    payment_timeout_minutes: int = Field(30, description="订单支付超时（分钟）")
    service_hours: str = Field("9:00-21:00", description="客服时间")
'''

with open(os.path.join(B, "app/schemas/content.py"), "w", encoding="utf-8") as f:
    f.write(content_schema)
print("  schemas/content.py")


# ══════════════════════════════════════════════════════════
# 3. services/content_service.py
# ══════════════════════════════════════════════════════════
content_service = '''# ============================================================
# 【这个文件是干什么的】
# 文章和配置的业务逻辑。
# ============================================================

import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessError
from app.models.content import Article, Setting


# ════════════════════════════════════════════════════════════
# 【文章】
# ════════════════════════════════════════════════════════════

def _article_to_dict(a: Article, with_content: bool = False) -> dict:
    """ORM → dict"""
    d = {
        "id": a.id,
        "slug": a.slug,
        "title": a.title,
        "summary": a.summary,
        "cover": a.cover,
        "category": a.category,
        "meaning": a.meaning,
        "tags": a.tags,
        "status": a.status,
        "view_count": a.view_count,
    }
    if with_content:
        d.update({
            "content": a.content,
            "faq": a.faq,
            "seo_title": a.seo_title,
            "seo_description": a.seo_description,
            "sort_weight": a.sort_weight,
        })
    return d


async def list_articles(
    db: AsyncSession,
    status: str | None = "published",
    category: str | None = None,
    size: int = 100,
) -> list[dict]:
    """
    【干什么】列出文章。

    【默认只返回已发布的】
    后台要看全部，传 status=None。
    """
    stmt = select(Article)

    if status:
        stmt = stmt.where(Article.status == status)
    if category:
        stmt = stmt.where(Article.category == category)

    stmt = stmt.order_by(Article.sort_weight.desc(), Article.id.desc()).limit(size)

    result = await db.execute(stmt)
    return [_article_to_dict(a) for a in result.scalars().all()]


async def get_article_by_slug(db: AsyncSession, slug: str) -> dict:
    """按 slug 查文章（含正文），并累加阅读数"""
    result = await db.execute(select(Article).where(Article.slug == slug))
    a = result.scalar_one_or_none()

    if not a:
        raise BusinessError("文章不存在", code="ARTICLE_NOT_FOUND", status_code=404)

    # 累加阅读数
    a.view_count = (a.view_count or 0) + 1
    await db.commit()
    await db.refresh(a)

    return _article_to_dict(a, with_content=True)


async def create_article(db: AsyncSession, data: dict) -> dict:
    """新建文章"""
    # slug 不能重复
    result = await db.execute(select(Article).where(Article.slug == data["slug"]))
    if result.scalar_one_or_none():
        raise BusinessError("slug 已被占用，换一个", code="SLUG_EXISTS")

    a = Article(
        id=f"art{secrets.token_hex(10)}",
        **{k: v for k, v in data.items() if hasattr(Article, k)},
    )
    db.add(a)
    await db.commit()
    await db.refresh(a)
    return _article_to_dict(a, with_content=True)


async def update_article(db: AsyncSession, article_id: str, data: dict) -> dict:
    """修改文章"""
    result = await db.execute(select(Article).where(Article.id == article_id))
    a = result.scalar_one_or_none()

    if not a:
        raise BusinessError("文章不存在", code="ARTICLE_NOT_FOUND", status_code=404)

    for k, v in data.items():
        if v is not None and hasattr(Article, k):
            setattr(a, k, v)

    await db.commit()
    await db.refresh(a)
    return _article_to_dict(a, with_content=True)


async def delete_article(db: AsyncSession, article_id: str) -> None:
    """删除文章"""
    result = await db.execute(select(Article).where(Article.id == article_id))
    a = result.scalar_one_or_none()
    if not a:
        raise BusinessError("文章不存在", code="ARTICLE_NOT_FOUND", status_code=404)
    await db.delete(a)
    await db.commit()


# ════════════════════════════════════════════════════════════
# 【配置】
# ════════════════════════════════════════════════════════════

# 默认配送规则（数据库没配时用这个）
DEFAULT_DELIVERY = {
    "free_shipping_threshold": 199,
    "base_shipping_fee": 15,
    "remote_shipping_fee": 25,
    "same_city_hours": 2,
    "cutoff_hour": 16,
    "delivery_slots": ["14:00-16:00", "18:00-20:00"],
    "payment_timeout_minutes": 30,
    "service_hours": "9:00-21:00",
}


async def get_setting(db: AsyncSession, key: str) -> dict:
    """读配置，没有就返回默认值"""
    result = await db.execute(select(Setting).where(Setting.key == key))
    s = result.scalar_one_or_none()

    if not s:
        return DEFAULT_DELIVERY if key == "delivery" else {}

    return s.value or {}


async def save_setting(db: AsyncSession, key: str, value: dict, description: str | None = None) -> dict:
    """写配置（有就更新，没有就建）"""
    result = await db.execute(select(Setting).where(Setting.key == key))
    s = result.scalar_one_or_none()

    if s:
        s.value = value
        if description:
            s.description = description
    else:
        s = Setting(key=key, value=value, description=description or key)
        db.add(s)

    await db.commit()
    return s.value
'''

with open(os.path.join(B, "app/services/content_service.py"), "w", encoding="utf-8") as f:
    f.write(content_service)
print("  services/content_service.py")

print("\n完成")
