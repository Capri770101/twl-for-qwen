# ============================================================
# 【这个文件是干什么的】
# FastAPI 的依赖注入定义 —— 把数据库会话、Service 注入到路由里。
#
# 【什么是依赖注入】
# 路由函数不需要自己创建数据库连接、不需要自己 new Service，
# 只要在参数里声明「我需要什么」，FastAPI 自动给你。
#
# 【怎么用】
#   @router.get("/x")
#   async def handler(
#       product_service: ProductServiceDep,     # 自动拿到 ProductService
#       db: DbDep,                              # 自动拿到数据库会话
#   ):
# ============================================================

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import (
    DeliveryService,
    OrderService,
    PaymentService,
    ProductService,
    TicketService,
)


# ────────────────────────────────────────────────────────────
# 数据库会话
# ────────────────────────────────────────────────────────────
DbDep = Annotated[AsyncSession, Depends(get_db)]


# ────────────────────────────────────────────────────────────
# 各个 Service
#
# 【为什么要这么写】
# 每次请求都新建一个 Service 实例，绑定当前的数据库会话。
# 这样不同请求之间不会串数据。
# ────────────────────────────────────────────────────────────

async def _get_product_service(db: DbDep) -> ProductService:
    return ProductService(db)


async def _get_order_service(db: DbDep) -> OrderService:
    return OrderService(db)


async def _get_payment_service(db: DbDep) -> PaymentService:
    return PaymentService(db)


async def _get_ticket_service(db: DbDep) -> TicketService:
    return TicketService(db)


async def _get_delivery_service(db: DbDep) -> DeliveryService:
    return DeliveryService(db)


ProductServiceDep = Annotated[ProductService, Depends(_get_product_service)]
OrderServiceDep = Annotated[OrderService, Depends(_get_order_service)]
PaymentServiceDep = Annotated[PaymentService, Depends(_get_payment_service)]
TicketServiceDep = Annotated[TicketService, Depends(_get_ticket_service)]
DeliveryServiceDep = Annotated[DeliveryService, Depends(_get_delivery_service)]

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

    user_id = await auth_service.parse_token(token)
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

async def require_admin(user: CurrentUserDep) -> User:
    """
    【干什么】要求当前用户是管理员。

    【为什么单独一个依赖】
    后台接口全部要走这个，避免漏加。
    漏加一个就是数据泄露。
    """
    if not getattr(user, "is_admin", False):
        raise BusinessError("需要管理员权限", code="FORBIDDEN", status_code=403)
    return user


AdminDep = Annotated[User, Depends(require_admin)]

