# ============================================================
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
