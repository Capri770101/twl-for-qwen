# -*- coding: utf-8 -*-
"""生成认证 + 地址簿模块"""

import os

B = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\backend"

# ══════════════════════════════════════════════════════════
# 1. schemas/auth.py
# ══════════════════════════════════════════════════════════
auth_schema = '''# ============================================================
# 【这个文件是干什么的】
# 登录相关的请求格式和响应格式。
#
# 【登录流程】
#   1. 前端调 /auth/send-code，传手机号
#   2. 后端生成 6 位验证码（开发环境直接返回，正式环境发短信）
#   3. 前端调 /auth/login，传手机号 + 验证码
#   4. 后端校验通过，创建/查找用户，返回 token
#   5. 前端把 token 存起来，后续请求带在 Authorization 头里
# ============================================================

from pydantic import Field, field_validator

from app.schemas.common import BaseSchema


class SendCodeIn(BaseSchema):
    """发送验证码的请求"""

    phone: str = Field(..., description="手机号")

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str) -> str:
        """校验手机号格式：11 位数字，1 开头"""
        v = v.strip().replace(" ", "").replace("-", "")
        if not v.isdigit() or len(v) != 11 or not v.startswith("1"):
            raise ValueError("手机号格式不对")
        return v


class SendCodeOut(BaseSchema):
    """发送验证码的响应"""

    phone: str = Field(..., description="手机号（脱敏）")
    expires_in: int = Field(..., description="有效期（秒）")
    dev_code: str | None = Field(None, description="【开发环境】验证码，正式环境为空")


class LoginIn(BaseSchema):
    """登录请求"""

    phone: str = Field(..., description="手机号")
    code: str = Field(..., min_length=4, max_length=6, description="验证码")

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str) -> str:
        v = v.strip().replace(" ", "").replace("-", "")
        if not v.isdigit() or len(v) != 11 or not v.startswith("1"):
            raise ValueError("手机号格式不对")
        return v


class UserOut(BaseSchema):
    """用户信息"""

    id: str = Field(..., description="用户 ID")
    phone: str | None = Field(None, description="手机号（脱敏）")
    nickname: str | None = Field(None, description="昵称")
    avatar: str | None = Field(None, description="头像")
    created_at: str | None = Field(None, description="注册时间")


class LoginOut(BaseSchema):
    """登录成功的响应"""

    token: str = Field(..., description="登录凭证，后续请求放在 Authorization: Bearer <token>")
    user: UserOut = Field(..., description="用户信息")
    is_new: bool = Field(False, description="是否新注册用户")
'''

with open(os.path.join(B, "app/schemas/auth.py"), "w", encoding="utf-8") as f:
    f.write(auth_schema)
print("  schemas/auth.py")


# ══════════════════════════════════════════════════════════
# 2. schemas/address.py
# ══════════════════════════════════════════════════════════
addr_schema = '''# ============================================================
# 【这个文件是干什么的】
# 地址簿的请求格式和响应格式。
# ============================================================

from pydantic import Field, field_validator

from app.schemas.common import BaseSchema


class AddressIn(BaseSchema):
    """新增/修改地址的请求"""

    receiver: str = Field(..., min_length=1, max_length=50, description="收件人姓名")
    phone: str = Field(..., description="手机号")
    province: str | None = Field(None, max_length=50, description="省")
    city: str | None = Field(None, max_length=50, description="市")
    district: str | None = Field(None, max_length=50, description="区")
    detail: str = Field(..., min_length=1, max_length=300, description="详细地址")
    tag: str | None = Field(None, max_length=20, description="标签：家/公司/学校")
    is_default: bool = Field(False, description="是否设为默认")

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str) -> str:
        v = v.strip().replace(" ", "").replace("-", "")
        if not v.isdigit() or len(v) != 11 or not v.startswith("1"):
            raise ValueError("手机号格式不对")
        return v


class AddressOut(BaseSchema):
    """地址信息"""

    id: str
    receiver: str
    phone: str
    province: str | None = None
    city: str | None = None
    district: str | None = None
    detail: str
    tag: str | None = None
    is_default: bool = False
    full_address: str = ""


class AddressListOut(BaseSchema):
    """地址列表"""

    items: list[AddressOut]
    total: int
'''

with open(os.path.join(B, "app/schemas/address.py"), "w", encoding="utf-8") as f:
    f.write(addr_schema)
print("  schemas/address.py")


# ══════════════════════════════════════════════════════════
# 3. services/auth_service.py
# ══════════════════════════════════════════════════════════
auth_service = '''# ============================================================
# 【这个文件是干什么的】
# 登录相关的业务逻辑：验证码生成、校验、token 签发、token 校验。
#
# 【验证码怎么存】
# 存在内存字典里（进程重启就没了）。
# 为什么不用 Redis：开发环境没必要，单进程够用。
# 正式环境要换成 Redis，因为多进程/多机器之间内存不共享。
#
# 【token 怎么生成】
# 用 HMAC-SHA256 签一个字符串，格式：user_id.expire_ts.signature
# 为什么不用 JWT 库：少一个依赖，逻辑一样简单。
# ============================================================

import hashlib
import hmac
import random
import secrets
import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BusinessError
from app.models.user import User


# ════════════════════════════════════════════════════════════
# 【内存存储】
# ════════════════════════════════════════════════════════════

# 验证码：{phone: (code, expire_ts, fail_count)}
_CODE_STORE: dict[str, tuple[str, float, int]] = {}

# 验证码有效期（秒）
CODE_TTL = 300

# 同一手机号最多试错次数
MAX_FAIL = 5


# ════════════════════════════════════════════════════════════
# 【token】
# ════════════════════════════════════════════════════════════

# 密钥：从配置读，没配就用固定值（开发环境）
SECRET = getattr(settings, "SECRET_KEY", None) or "twl-dev-secret-2026"

# token 有效期（秒）：7 天
TOKEN_TTL = 7 * 24 * 3600


def _sign(payload: str) -> str:
    """用密钥对 payload 做 HMAC 签名"""
    return hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]


def make_token(user_id: str) -> str:
    """签发 token"""
    expire = int(time.time()) + TOKEN_TTL
    payload = f"{user_id}.{expire}"
    return f"{payload}.{_sign(payload)}"


def parse_token(token: str) -> str:
    """
    【干什么】校验 token，返回 user_id。

    【失败抛什么】
    签名不对、过期、格式错 —— 都抛 401
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise BusinessError("token 格式不对", code="UNAUTHORIZED", status_code=401)

    user_id, expire_str, sig = parts
    payload = f"{user_id}.{expire_str}"

    if not hmac.compare_digest(sig, _sign(payload)):
        raise BusinessError("token 无效", code="UNAUTHORIZED", status_code=401)

    if int(expire_str) < time.time():
        raise BusinessError("token 已过期，请重新登录", code="UNAUTHORIZED", status_code=401)

    return user_id


# ════════════════════════════════════════════════════════════
# 【验证码】
# ════════════════════════════════════════════════════════════

def send_code(phone: str) -> tuple[str, int]:
    """
    【干什么】生成并"发送"验证码。

    【返回】
        (验证码, 有效期秒数)

    【正式环境怎么改】
    把 dev_code 换成调短信服务商 API，不返回给前端。
    """
    code = f"{random.randint(0, 999999):06d}"
    expire = time.time() + CODE_TTL
    _CODE_STORE[phone] = (code, expire, 0)
    return code, CODE_TTL


def verify_code(phone: str, code: str) -> None:
    """
    【干什么】校验验证码，不通过就抛异常。

    【为什么校验完要删】
    验证码只能用一次，用过就作废，防止重放。
    """
    record = _CODE_STORE.get(phone)

    if not record:
        raise BusinessError("请先获取验证码", code="CODE_REQUIRED")

    stored_code, expire_ts, fail_count = record

    if time.time() > expire_ts:
        _CODE_STORE.pop(phone, None)
        raise BusinessError("验证码已过期，请重新获取", code="CODE_EXPIRED")

    if fail_count >= MAX_FAIL:
        _CODE_STORE.pop(phone, None)
        raise BusinessError("错误次数过多，请重新获取验证码", code="TOO_MANY_ATTEMPTS")

    if code != stored_code:
        _CODE_STORE[phone] = (stored_code, expire_ts, fail_count + 1)
        raise BusinessError("验证码不对", code="CODE_INVALID")

    # 通过，删掉
    _CODE_STORE.pop(phone, None)


# ════════════════════════════════════════════════════════════
# 【用户】
# ════════════════════════════════════════════════════════════

def mask_phone(phone: str | None) -> str | None:
    """手机号脱敏：138****6688"""
    if not phone or len(phone) != 11:
        return phone
    return f"{phone[:3]}****{phone[-4:]}"


async def get_or_create_user(db: AsyncSession, phone: str) -> tuple[User, bool]:
    """
    【干什么】按手机号找用户，没有就建一个。

    【返回】
        (用户对象, 是否新建)
    """
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()

    if user:
        return user, False

    # 新建
    user = User(
        id=f"u{secrets.token_hex(12)}",
        phone=phone,
        channel="phone",
        nickname=f"用户{phone[-4:]}",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user, True


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    """按 ID 查用户"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


def user_to_dict(user: User) -> dict:
    """把 ORM 对象转成接口能返回的 dict"""
    created = ""
    if getattr(user, "created_at", None):
        try:
            created = user.created_at.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            created = str(user.created_at)

    return {
        "id": user.id,
        "phone": mask_phone(user.phone),
        "nickname": user.nickname,
        "avatar": user.avatar,
        "created_at": created,
    }
'''

with open(os.path.join(B, "app/services/auth_service.py"), "w", encoding="utf-8") as f:
    f.write(auth_service)
print("  services/auth_service.py")


# ══════════════════════════════════════════════════════════
# 4. services/address_service.py
# ══════════════════════════════════════════════════════════
addr_service = '''# ============================================================
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
'''

with open(os.path.join(B, "app/services/address_service.py"), "w", encoding="utf-8") as f:
    f.write(addr_service)
print("  services/address_service.py")

print("\n第一部分完成")
