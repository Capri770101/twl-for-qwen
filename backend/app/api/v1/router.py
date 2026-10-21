# ============================================================
# 【这个文件是干什么的】
# v1 版本 API 的总路由 —— 把所有模块的路由拼到一起。
#
# 【为什么要有版本号】
# 以后接口要大改（不兼容旧版）时，可以同时提供 /api/v1 和 /api/v2，
# 老客户端继续用 v1，新客户端用 v2，平滑过渡。
# ============================================================

from fastapi import APIRouter

from app.api.v1 import (
    addresses,
    admin,
    articles,
    auth,
    deliveries,
    orders,
    payments,
    products,
    settings,
    tickets,
    uploads,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(addresses.router)
api_router.include_router(products.router)
api_router.include_router(orders.router)
api_router.include_router(payments.router)
api_router.include_router(tickets.router)
api_router.include_router(deliveries.router)
api_router.include_router(articles.router)
api_router.include_router(settings.router)
api_router.include_router(uploads.router)
api_router.include_router(admin.router)
