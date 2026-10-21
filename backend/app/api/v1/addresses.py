# ============================================================
# 【这个文件是干什么的】
# 地址簿的增删改查接口。
#
# 【必须登录】
# 地址是跟人绑定的，所以每个接口都要当前用户。
# ============================================================

from fastapi import APIRouter

from app.api.deps import CurrentUserDep, DbDep
from app.schemas.address import AddressIn, AddressListOut, AddressOut
from app.schemas.common import ApiResponse
from app.services import address_service

router = APIRouter(prefix="/addresses", tags=["地址簿"])


@router.get("", response_model=ApiResponse[AddressListOut], summary="地址列表")
async def list_addresses(user: CurrentUserDep, db: DbDep) -> ApiResponse[AddressListOut]:
    """列出当前用户所有地址，默认地址排最前"""
    items = await address_service.list_addresses(db, user.id)
    return ApiResponse[AddressListOut](
        data=AddressListOut(
            items=[AddressOut(**x) for x in items],
            total=len(items),
        )
    )


@router.post("", response_model=ApiResponse[AddressOut], summary="新增地址")
async def create_address(
    payload: AddressIn,
    user: CurrentUserDep,
    db: DbDep,
) -> ApiResponse[AddressOut]:
    """
    【干什么】新增一个地址。

    【规则】
    第一条地址自动设为默认。
    """
    data = await address_service.create_address(db, user.id, payload.model_dump())
    return ApiResponse[AddressOut](data=AddressOut(**data))


@router.put("/{address_id}", response_model=ApiResponse[AddressOut], summary="修改地址")
async def update_address(
    address_id: str,
    payload: AddressIn,
    user: CurrentUserDep,
    db: DbDep,
) -> ApiResponse[AddressOut]:
    """修改地址"""
    data = await address_service.update_address(db, user.id, address_id, payload.model_dump())
    return ApiResponse[AddressOut](data=AddressOut(**data))


@router.delete("/{address_id}", response_model=ApiResponse[dict], summary="删除地址")
async def delete_address(
    address_id: str,
    user: CurrentUserDep,
    db: DbDep,
) -> ApiResponse[dict]:
    """
    【干什么】删除地址。

    【删掉默认地址会怎样】
    剩下的最早那条自动变成默认。
    """
    await address_service.delete_address(db, user.id, address_id)
    return ApiResponse[dict](data={"message": "已删除"})


@router.post("/{address_id}/default", response_model=ApiResponse[AddressOut], summary="设为默认")
async def set_default(
    address_id: str,
    user: CurrentUserDep,
    db: DbDep,
) -> ApiResponse[AddressOut]:
    """把某个地址设为默认"""
    data = await address_service.set_default(db, user.id, address_id)
    return ApiResponse[AddressOut](data=AddressOut(**data))
