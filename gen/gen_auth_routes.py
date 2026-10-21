# -*- coding: utf-8 -*-
"""生成认证 + 地址簿路由，并更新 deps / router"""

import os

B = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\backend"


# ══════════════════════════════════════════════════════════
# 1. deps.py 追加认证依赖
# ══════════════════════════════════════════════════════════
deps_path = os.path.join(B, "app/api/deps.py")
html = open(deps_path, encoding="utf-8").read()

extra_deps = '''

# ────────────────────────────────────────────────────────────
# 认证依赖
#
# 【干什么】
# 从请求头 Authorization: Bearer <token> 里取出 token，
# 校验通过后返回当前用户。
#
# 【怎么用】
#   @router.get("/x")
#   async def handler(user: CurrentUserDep):
#       # user 是 User 对象，拿不到会自动 401
# ────────────────────────────────────────────────────────────

from fastapi import Header

from app.core.exceptions import BusinessError
from app.models.user import User
from app.services import auth_service


async def get_current_user(
    db: DbDep,
    authorization: str | None = Header(None),
) -> User:
    """
    【干什么】解析 token，返回当前登录用户。

    【没登录怎么办】
    抛 401，前端收到后跳登录页。
    """
    if not authorization:
        raise BusinessError("请先登录", code="UNAUTHORIZED", status_code=401)

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise BusinessError("认证头格式不对", code="UNAUTHORIZED", status_code=401)

    token = parts[1]

    # 特殊：支持 guest token 方式（游客）
    if token.startswith("guest_"):
        raise BusinessError("游客身份不支持该操作，请先登录", code="LOGIN_REQUIRED", status_code=401)

    user_id = auth_service.parse_token(token)
    user = await auth_service.get_user_by_id(db, user_id)

    if not user or not user.is_active:
        raise BusinessError("用户不存在或已停用", code="UNAUTHORIZED", status_code=401)

    return user


async def get_optional_user(
    db: DbDep,
    authorization: str | None = Header(None),
) -> User | None:
    """
    【干什么】有 token 就返回用户，没有就返回 None。

    【用在哪】
    允许游客访问、但登录了能多看到一些东西的接口。
    """
    if not authorization:
        return None
    try:
        return await get_current_user(db, authorization)
    except Exception:
        return None


CurrentUserDep = Annotated[User, Depends(get_current_user)]
OptionalUserDep = Annotated[User | None, Depends(get_optional_user)]
'''

if "CurrentUserDep" not in html:
    html = html.rstrip() + extra_deps + "\n"
    open(deps_path, "w", encoding="utf-8").write(html)
    print("  deps.py: 加认证依赖")


# ══════════════════════════════════════════════════════════
# 2. api/v1/auth.py
# ══════════════════════════════════════════════════════════
auth_router = '''# ============================================================
# 【这个文件是干什么的】
# 登录相关的接口。
#
# 【三个接口】
#   POST /auth/send-code   发验证码
#   POST /auth/login       登录
#   GET  /auth/me          查当前用户
#   POST /auth/logout      退出（前端删 token 就行，这里是示意）
# ============================================================

from fastapi import APIRouter

from app.api.deps import CurrentUserDep, DbDep
from app.schemas.auth import LoginIn, LoginOut, SendCodeIn, SendCodeOut
from app.schemas.common import ApiResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/send-code", response_model=ApiResponse[SendCodeOut], summary="发送验证码")
async def send_code(payload: SendCodeIn) -> ApiResponse[SendCodeOut]:
    """
    【干什么】给手机号发验证码。

    【开发环境】
    验证码直接放在响应的 dev_code 里返回，方便测试。
    正式环境要把这个字段去掉，改成真的发短信。
    """
    code, ttl = auth_service.send_code(payload.phone)

    from app.core.config import settings

    return ApiResponse[SendCodeOut](
        data=SendCodeOut(
            phone=auth_service.mask_phone(payload.phone),
            expires_in=ttl,
            dev_code=code if settings.DEBUG else None,
        )
    )


@router.post("/login", response_model=ApiResponse[LoginOut], summary="登录")
async def login(payload: LoginIn, db: DbDep) -> ApiResponse[LoginOut]:
    """
    【干什么】校验验证码，登录或自动注册。

    【没注册过怎么办】
    自动创建账号（手机号就是身份）。
    """
    # 校验验证码
    auth_service.verify_code(payload.phone, payload.code)

    # 找用户或建用户
    user, is_new = await auth_service.get_or_create_user(db, payload.phone)

    # 签 token
    token = auth_service.make_token(user.id)

    return ApiResponse[LoginOut](
        data=LoginOut(
            token=token,
            user=auth_service.user_to_dict(user),
            is_new=is_new,
        )
    )


@router.get("/me", response_model=ApiResponse[dict], summary="当前用户")
async def me(user: CurrentUserDep) -> ApiResponse[dict]:
    """查当前登录用户的信息"""
    return ApiResponse[dict](data=auth_service.user_to_dict(user))


@router.post("/logout", response_model=ApiResponse[dict], summary="退出登录")
async def logout(user: CurrentUserDep) -> ApiResponse[dict]:
    """
    【干什么】退出登录。

    【为什么后端不做实际处理】
    token 是无状态的（签名校验），后端没有 session 可删。
    前端把 localStorage 里的 token 删掉就等于退出。
    这个接口只是给前端一个统一的调用点。
    """
    return ApiResponse[dict](data={"message": "已退出"})
'''

with open(os.path.join(B, "app/api/v1/auth.py"), "w", encoding="utf-8") as f:
    f.write(auth_router)
print("  api/v1/auth.py")


# ══════════════════════════════════════════════════════════
# 3. api/v1/addresses.py
# ══════════════════════════════════════════════════════════
addr_router = '''# ============================================================
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
'''

with open(os.path.join(B, "app/api/v1/addresses.py"), "w", encoding="utf-8") as f:
    f.write(addr_router)
print("  api/v1/addresses.py")


# ══════════════════════════════════════════════════════════
# 4. 更新 router.py
# ══════════════════════════════════════════════════════════
router_path = os.path.join(B, "app/api/v1/router.py")
html = open(router_path, encoding="utf-8").read()

if "addresses" not in html:
    html = html.replace(
        "from app.api.v1 import admin, deliveries, orders, payments, products, tickets",
        "from app.api.v1 import addresses, admin, auth, deliveries, orders, payments, products, tickets"
    )
    html = html.replace(
        "api_router.include_router(products.router)",
        "api_router.include_router(auth.router)\napi_router.include_router(addresses.router)\napi_router.include_router(products.router)"
    )
    open(router_path, "w", encoding="utf-8").write(html)
    print("  router.py: 挂载 auth + addresses")

print("\n完成")
