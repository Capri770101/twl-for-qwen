# ============================================================
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
#
# 【为什么默认全是 None】
# 交付环境没有真实配送数据，不能编。
# 前端拿到 None 就显示「待配置」，不留假承诺。
# 老板在后台填了真实规则，这里就不是 None 了。
DEFAULT_DELIVERY = {
    "configured": False,
    "announcement": "",                       # 顶部公告文案
    "free_shipping_threshold": None,
    "base_shipping_fee": None,
    "remote_shipping_fee": None,
    "same_city_hours": None,
    "cutoff_hour": None,
    "delivery_slots": [],
    "payment_timeout_minutes": 30,
    "service_hours": "",
}


async def get_setting(db: AsyncSession, key: str) -> dict:
    """
    【干什么】读配置，没有就返回默认值。

    【为什么读出来还要补默认值】
    数据库里可能只配了一半（比如只填了免运费门槛），
    缺的字段要补上，否则前端拿到不全的数据会显示 undefined。
    """
    result = await db.execute(select(Setting).where(Setting.key == key))
    s = result.scalar_one_or_none()

    if key == "delivery":
        saved = s.value if s else {}
        merged = dict(DEFAULT_DELIVERY)
        merged.update(saved or {})
        # 只要填了任一真实字段，就算已配置
        if any(merged.get(k) is not None for k in ("free_shipping_threshold","base_shipping_fee","same_city_hours","cutoff_hour")):
            merged["configured"] = True
        return merged

    return s.value if s else {}


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
