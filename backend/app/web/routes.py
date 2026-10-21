# ============================================================
# 【这个文件是干什么的】
# 给动态页面加服务端渲染（SSR）路由。
#
# 【为什么需要】
# 前端是静态 HTML + JS 渲染。爬虫不执行 JS，读不到商品和文章。
# 实测：商城、商品详情、花语列表、花语详情 四个页面爬虫拿到的都是空壳。
#
# 【怎么工作】
# 1. 拦截这几个页面的请求（路由优先于 StaticFiles 挂载）
# 2. 读静态模板 + 查数据库 + 渲染内容
# 3. 返回完整 HTML
#
# 【对用户有影响吗】
# 没有。SSR 渲染的内容和 JS 渲染的一模一样，JS 加载后会接管交互。
# ============================================================

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from app.api.deps import DbDep
from app.web import render

router = APIRouter(tags=["页面"], include_in_schema=False)


@router.get("/shop.html", response_class=HTMLResponse, summary="商城页（SSR）")
async def shop_page(db: DbDep) -> HTMLResponse:
    """商城页：服务端把商品列表渲染进 HTML"""
    html = await render.render_shop(db)

    if html is None:
        return HTMLResponse("页面模板缺失", status_code=500)

    return HTMLResponse(html)


@router.get("/product.html", response_class=HTMLResponse, summary="商品详情页（SSR）")
async def product_page(
    db: DbDep,
    id: str = Query("", description="商品编号"),
) -> HTMLResponse:
    """
    商品详情页：服务端渲染商品信息。

    【为什么不带 id 也能访问】
    前端 JS 会从 URL 读 id。带 id 访问时后端先渲染好，爬虫能读到。
    """
    html = await render.render_product(db, id)

    if html is None:
        return HTMLResponse("页面模板缺失", status_code=500)

    return HTMLResponse(html)


@router.get("/flower-language.html", response_class=HTMLResponse, summary="花语列表页（SSR）")
async def flower_list_page(db: DbDep) -> HTMLResponse:
    """花语列表页：服务端把文章列表渲染进 HTML"""
    html = await render.render_flower_list(db)

    if html is None:
        return HTMLResponse("页面模板缺失", status_code=500)

    return HTMLResponse(html)


@router.get(
    "/flower-language-detail.html",
    response_class=HTMLResponse,
    summary="花语详情页（SSR）",
)
async def flower_detail_page(
    db: DbDep,
    slug: str = Query("", description="文章标识"),
) -> HTMLResponse:
    """花语详情页：服务端把正文渲染进 HTML"""
    html = await render.render_flower_detail(db, slug)

    if html is None:
        return HTMLResponse("页面模板缺失", status_code=500)

    return HTMLResponse(html)
