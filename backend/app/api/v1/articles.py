# ============================================================
# 【这个文件是干什么的】
# 花语文章的读写接口。
#
# 【前台用什么】
#   GET /articles          列表（只返回已发布）
#   GET /articles/{slug}   详情
#
# 【后台用什么】
#   GET    /articles/admin        全部（含草稿）
#   POST   /articles/admin        新建
#   PUT    /articles/admin/{id}   修改
#   DELETE /articles/admin/{id}   删除
# ============================================================

from fastapi import APIRouter, Query

from app.api.deps import AdminDep, DbDep
from app.schemas.common import ApiResponse
from app.schemas.content import ArticleIn, ArticleListOut, ArticleOut, ArticleDetailOut
from app.services import content_service

router = APIRouter(prefix="/articles", tags=["花语"])


@router.get("", response_model=ApiResponse[ArticleListOut], summary="文章列表")
async def list_articles(
    db: DbDep,
    category: str | None = Query(None, description="分类筛选"),
    size: int = Query(100, ge=1, le=200, description="返回条数"),
) -> ApiResponse[ArticleListOut]:
    """
    【干什么】列出已发布的文章。

    【为什么只给已发布】
    草稿是后台在编辑的，前台不该看到。
    """
    items = await content_service.list_articles(db, status="published", category=category, size=size)
    return ApiResponse[ArticleListOut](
        data=ArticleListOut(
            items=[ArticleOut(**x) for x in items],
            total=len(items),
        )
    )


@router.get("/admin", response_model=ApiResponse[ArticleListOut], summary="全部文章（后台）")
async def list_all_articles(
    admin: AdminDep,
    db: DbDep,
    size: int = Query(200, ge=1, le=500),
) -> ApiResponse[ArticleListOut]:
    """后台用：返回全部文章，含草稿"""
    items = await content_service.list_articles(db, status=None, size=size)
    return ApiResponse[ArticleListOut](
        data=ArticleListOut(
            items=[ArticleOut(**x) for x in items],
            total=len(items),
        )
    )


@router.get("/{slug}", response_model=ApiResponse[ArticleDetailOut], summary="文章详情")
async def get_article(slug: str, db: DbDep) -> ApiResponse[ArticleDetailOut]:
    """按 slug 查文章，同时累加阅读数"""
    data = await content_service.get_article_by_slug(db, slug)
    return ApiResponse[ArticleDetailOut](data=ArticleDetailOut(**data))


@router.post("/admin", response_model=ApiResponse[ArticleDetailOut], summary="新建文章")
async def create_article(
    payload: ArticleIn,
    admin: AdminDep,
    db: DbDep,
) -> ApiResponse[ArticleDetailOut]:
    """后台新建文章"""
    data = await content_service.create_article(db, payload.model_dump())
    return ApiResponse[ArticleDetailOut](data=ArticleDetailOut(**data))


@router.put("/admin/{article_id}", response_model=ApiResponse[ArticleDetailOut], summary="修改文章")
async def update_article(
    article_id: str,
    payload: ArticleIn,
    admin: AdminDep,
    db: DbDep,
) -> ApiResponse[ArticleDetailOut]:
    """后台修改文章"""
    data = await content_service.update_article(db, article_id, payload.model_dump())
    return ApiResponse[ArticleDetailOut](data=ArticleDetailOut(**data))


@router.delete("/admin/{article_id}", response_model=ApiResponse[dict], summary="删除文章")
async def delete_article(
    article_id: str,
    admin: AdminDep,
    db: DbDep,
) -> ApiResponse[dict]:
    """后台删除文章"""
    await content_service.delete_article(db, article_id)
    return ApiResponse[dict](data={"message": "已删除"})
