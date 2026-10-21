# ============================================================
# 【这个文件是干什么的】
# 系统级公开配置接口。
#
# 【为什么要这个接口】
# 前端需要知道：
#   1. 现在是演示模式还是正式模式
#   2. 配送规则填了没有
#   3. 顶部公告显示什么
#
# 这些信息每个页面都要用，所以单独一个接口，
# 页面加载时读一次，存到 window.APP_CONFIG。
#
# 【为什么不放 /settings】
# /settings 是后台用的（需要管理员权限）；
# 这个是前台用的，公开，不含敏感信息。
# ============================================================

from fastapi import APIRouter

from app.api.deps import DbDep
from app.core.config import settings
from app.schemas.common import ApiResponse
from app.services import content_service

router = APIRouter(prefix="/system", tags=["系统"])


@router.get("/config", response_model=ApiResponse[dict], summary="前台配置")
async def get_public_config(db: DbDep) -> ApiResponse[dict]:
    """
    【干什么】返回前台需要的配置。

    【返回什么】
        demo_mode      是否演示模式
        delivery       配送规则（未配置时各字段为 None）
        contact        联系方式占位
    """
    delivery = await content_service.get_setting(db, "delivery")

    return ApiResponse[dict](data={
        "demo_mode": settings.DEMO_MODE,
        "env": settings.APP_ENV,
        "delivery": {
            "configured": delivery.get("configured", False),
            "announcement": delivery.get("announcement") or "",
            "free_shipping_threshold": delivery.get("free_shipping_threshold"),
            "base_shipping_fee": delivery.get("base_shipping_fee"),
            "same_city_hours": delivery.get("same_city_hours"),
            "cutoff_hour": delivery.get("cutoff_hour"),
            "service_hours": delivery.get("service_hours") or "",
        },
    })
