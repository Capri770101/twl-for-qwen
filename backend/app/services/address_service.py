# ============================================================
# 【这个文件是干什么的】
# 地址簿的增删改查业务逻辑。
#
# 【核心规则】
#   1. 一个人最多存 20 个地址
#   2. 设为默认时，其他地址自动取消默认
#   3. 删掉默认地址后，最早的那个自动变成默认
# ============================================================

import secrets

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessError
from app.models.user import Address

# 一个人的地址上限
MAX_ADDRESS = 20


def _addr_to_dict(a: Address) -> dict:
    """ORM → dict"""
    parts = [p for p in [a.province, a.city, a.district, a.detail] if p]
    return {
        "id": a.id,
        "receiver": a.receiver,
        "phone": a.phone,
        "province": a.province,
        "city": a.city,
        "district": a.district,
        "detail": a.detail,
        "tag": a.tag,
        "is_default": a.is_default,
        "full_address": "".join(parts),
    }


async def list_addresses(db: AsyncSession, user_id: str) -> list[dict]:
    """
    【干什么】列出用户所有地址，默认的排最前。

    【为什么默认排前】
    下单时最常用的是默认地址，让用户少滚动一次。
    """
    result = await db.execute(
        select(Address)
        .where(Address.user_id == user_id)
        .order_by(Address.is_default.desc(), Address.id.desc())
    )
    return [_addr_to_dict(a) for a in result.scalars().all()]


async def create_address(db: AsyncSession, user_id: str, data: dict) -> dict:
    """新增地址"""
    # 数量限制
    result = await db.execute(select(Address).where(Address.user_id == user_id))
    count = len(result.scalars().all())
    if count >= MAX_ADDRESS:
        raise BusinessError(f"最多存 {MAX_ADDRESS} 个地址，请先删掉不用的", code="ADDRESS_LIMIT")

    # 第一个地址自动设为默认
    is_default = data.get("is_default", False) or count == 0

    if is_default:
        await db.execute(
            update(Address).where(Address.user_id == user_id).values(is_default=False)
        )

    addr = Address(
        id=f"a{secrets.token_hex(12)}",
        user_id=user_id,
        receiver=data["receiver"],
        phone=data["phone"],
        province=data.get("province"),
        city=data.get("city"),
        district=data.get("district"),
        detail=data["detail"],
        tag=data.get("tag"),
        is_default=is_default,
    )
    db.add(addr)
    await db.commit()
    await db.refresh(addr)
    return _addr_to_dict(addr)


async def update_address(db: AsyncSession, user_id: str, address_id: str, data: dict) -> dict:
    """修改地址"""
    result = await db.execute(
        select(Address).where(Address.id == address_id, Address.user_id == user_id)
    )
    addr = result.scalar_one_or_none()

    if not addr:
        raise BusinessError("地址不存在", code="ADDRESS_NOT_FOUND", status_code=404)

    # 设为默认：先把其他的取消
    if data.get("is_default") and not addr.is_default:
        await db.execute(
            update(Address).where(Address.user_id == user_id).values(is_default=False)
        )

    for k in ["receiver", "phone", "province", "city", "district", "detail", "tag", "is_default"]:
        if k in data and data[k] is not None:
            setattr(addr, k, data[k])

    await db.commit()
    await db.refresh(addr)
    return _addr_to_dict(addr)


async def delete_address(db: AsyncSession, user_id: str, address_id: str) -> None:
    """
    【干什么】删除地址。

    【删掉默认地址后怎么办】
    把剩下的最早那条设为默认，保证永远有一条是默认的。
    """
    result = await db.execute(
        select(Address).where(Address.id == address_id, Address.user_id == user_id)
    )
    addr = result.scalar_one_or_none()

    if not addr:
        raise BusinessError("地址不存在", code="ADDRESS_NOT_FOUND", status_code=404)

    was_default = addr.is_default
    await db.delete(addr)
    await db.commit()

    # 补一个默认
    if was_default:
        result = await db.execute(
            select(Address).where(Address.user_id == user_id).order_by(Address.id).limit(1)
        )
        first = result.scalar_one_or_none()
        if first:
            first.is_default = True
            await db.commit()


async def set_default(db: AsyncSession, user_id: str, address_id: str) -> dict:
    """把某个地址设为默认"""
    await db.execute(
        update(Address).where(Address.user_id == user_id).values(is_default=False)
    )
    result = await db.execute(
        select(Address).where(Address.id == address_id, Address.user_id == user_id)
    )
    addr = result.scalar_one_or_none()
    if not addr:
        raise BusinessError("地址不存在", code="ADDRESS_NOT_FOUND", status_code=404)

    addr.is_default = True
    await db.commit()
    await db.refresh(addr)
    return _addr_to_dict(addr)
