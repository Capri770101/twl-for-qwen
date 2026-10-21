# -*- coding: utf-8 -*-
"""生成文章 / 配置 / 上传路由"""

import os

B = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\backend"


# ══════════════════════════════════════════════════════════
# 1. api/v1/articles.py
# ══════════════════════════════════════════════════════════
articles_router = '''# ============================================================
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

from app.api.deps import DbDep
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
async def create_article(payload: ArticleIn, db: DbDep) -> ApiResponse[ArticleDetailOut]:
    """后台新建文章"""
    data = await content_service.create_article(db, payload.model_dump())
    return ApiResponse[ArticleDetailOut](data=ArticleDetailOut(**data))


@router.put("/admin/{article_id}", response_model=ApiResponse[ArticleDetailOut], summary="修改文章")
async def update_article(
    article_id: str,
    payload: ArticleIn,
    db: DbDep,
) -> ApiResponse[ArticleDetailOut]:
    """后台修改文章"""
    data = await content_service.update_article(db, article_id, payload.model_dump())
    return ApiResponse[ArticleDetailOut](data=ArticleDetailOut(**data))


@router.delete("/admin/{article_id}", response_model=ApiResponse[dict], summary="删除文章")
async def delete_article(article_id: str, db: DbDep) -> ApiResponse[dict]:
    """后台删除文章"""
    await content_service.delete_article(db, article_id)
    return ApiResponse[dict](data={"message": "已删除"})
'''

with open(os.path.join(B, "app/api/v1/articles.py"), "w", encoding="utf-8") as f:
    f.write(articles_router)
print("  api/v1/articles.py")


# ══════════════════════════════════════════════════════════
# 2. api/v1/settings.py
# ══════════════════════════════════════════════════════════
settings_router = '''# ============================================================
# 【这个文件是干什么的】
# 系统配置的读写接口。目前只有配送规则。
#
# 【为什么要做成配置】
# 免运费门槛、配送时段这些运营会改，
# 写死在代码里每次改都要发版。
# ============================================================

from fastapi import APIRouter

from app.api.deps import DbDep
from app.schemas.common import ApiResponse
from app.schemas.content import DeliverySetting
from app.services import content_service

router = APIRouter(prefix="/settings", tags=["配置"])


@router.get("/delivery", response_model=ApiResponse[DeliverySetting], summary="配送规则")
async def get_delivery(db: DbDep) -> ApiResponse[DeliverySetting]:
    """读配送规则，没配过就返回默认值"""
    data = await content_service.get_setting(db, "delivery")
    return ApiResponse[DeliverySetting](data=DeliverySetting(**data))


@router.put("/delivery", response_model=ApiResponse[DeliverySetting], summary="修改配送规则")
async def save_delivery(payload: DeliverySetting, db: DbDep) -> ApiResponse[DeliverySetting]:
    """修改配送规则，立即生效"""
    data = await content_service.save_setting(
        db, "delivery", payload.model_dump(), description="配送规则"
    )
    return ApiResponse[DeliverySetting](data=DeliverySetting(**data))
'''

with open(os.path.join(B, "app/api/v1/settings.py"), "w", encoding="utf-8") as f:
    f.write(settings_router)
print("  api/v1/settings.py")


# ══════════════════════════════════════════════════════════
# 3. api/v1/uploads.py
# ══════════════════════════════════════════════════════════
uploads_router = '''# ============================================================
# 【这个文件是干什么的】
# 图片上传接口。
#
# 【存哪里】
# backend/static/uploads/ 目录下。
# 访问路径是 /uploads/xxx.jpg
#
# 【为什么存本地】
# 开发环境没必要上 OSS。正式环境要换对象存储（阿里云 OSS / 腾讯云 COS），
# 因为本地磁盘在多台服务器之间不共享。
#
# 【安全限制】
#   - 只允许图片格式
#   - 单文件最大 5MB
#   - 文件名随机生成，不用原名（防路径穿越）
# ============================================================

import secrets
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.common import ApiResponse

router = APIRouter(prefix="/uploads", tags=["上传"])

# 存储目录：backend/static/uploads/
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
UPLOAD_DIR = BACKEND_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 允许的格式
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

# 单文件大小上限：5MB
MAX_SIZE = 5 * 1024 * 1024


@router.post("", response_model=ApiResponse[dict], summary="上传图片")
async def upload_image(file: UploadFile = File(...)) -> ApiResponse[dict]:
    """
    【干什么】接收一个图片文件，存到本地，返回访问 URL。

    【前端怎么用】
    用 FormData 提交，字段名是 file。
    """
    # 检查扩展名
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"只支持 {', '.join(ALLOWED_EXT)} 格式",
        )

    # 读内容并检查大小
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="文件超过 5MB")

    # 随机文件名
    name = f"{secrets.token_hex(12)}{ext}"
    path = UPLOAD_DIR / name

    with open(path, "wb") as f:
        f.write(content)

    return ApiResponse[dict](data={
        "url": f"/uploads/{name}",
        "size": len(content),
        "filename": name,
    })
'''

with open(os.path.join(B, "app/api/v1/uploads.py"), "w", encoding="utf-8") as f:
    f.write(uploads_router)
print("  api/v1/uploads.py")


# ══════════════════════════════════════════════════════════
# 4. 更新 router.py
# ══════════════════════════════════════════════════════════
router_path = os.path.join(B, "app/api/v1/router.py")
html = open(router_path, encoding="utf-8").read()

if "articles" not in html:
    html = html.replace(
        "from app.api.v1 import addresses, admin, auth, deliveries, orders, payments, products, tickets",
        "from app.api.v1 import (\n    addresses,\n    admin,\n    articles,\n    auth,\n    deliveries,\n    orders,\n    payments,\n    products,\n    settings,\n    tickets,\n    uploads,\n)"
    )
    html = html.replace(
        "api_router.include_router(admin.router)",
        "api_router.include_router(articles.router)\napi_router.include_router(settings.router)\napi_router.include_router(uploads.router)\napi_router.include_router(admin.router)"
    )
    open(router_path, "w", encoding="utf-8").write(html)
    print("  router.py: 挂载 articles + settings + uploads")

print("\n完成")
