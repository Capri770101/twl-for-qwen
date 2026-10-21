# ============================================================
# 【这个文件是干什么的】
# 系统配置的读写接口。目前只有配送规则。
#
# 【为什么要做成配置】
# 免运费门槛、配送时段这些运营会改，
# 写死在代码里每次改都要发版。
# ============================================================

from fastapi import APIRouter

from app.api.deps import AdminDep, DbDep
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
async def save_delivery(
    payload: DeliverySetting,
    admin: AdminDep,
    db: DbDep,
) -> ApiResponse[DeliverySetting]:
    """修改配送规则，立即生效"""
    data = await content_service.save_setting(
        db, "delivery", payload.model_dump(), description="配送规则"
    )
    return ApiResponse[DeliverySetting](data=DeliverySetting(**data))
