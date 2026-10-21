# ============================================================
# 【这个文件是干什么的】
# 登录相关的接口。
#
# 【生产级设计】
#   - 验证码走短信适配器（开发 mock / 生产阿里云）
#   - 三重限流（手机号间隔、日限、IP 时限）
#   - 验证码只在非生产环境返回给前端
#   - 退出登录把 token 加入黑名单，立即失效
# ============================================================

from fastapi import APIRouter, Header, Request

from app.api.deps import CurrentUserDep, DbDep
from app.core.config import settings
from app.schemas.auth import LoginIn, LoginOut, SendCodeIn, SendCodeOut, UserOut
from app.schemas.common import ApiResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


def _client_ip(request: Request) -> str:
    """
    【干什么】取真实客户端 IP。

    【为什么要看 X-Forwarded-For】
    部署在 Nginx 后面时，request.client.host 拿到的是 Nginx 的 IP。
    真实 IP 在 X-Forwarded-For 头的第一个。
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


@router.post("/send-code", response_model=ApiResponse[SendCodeOut], summary="发送验证码")
async def send_code(payload: SendCodeIn, request: Request) -> ApiResponse[SendCodeOut]:
    """
    【干什么】给手机号发验证码。

    【限流】
    同一手机号 60 秒 1 次，每天 10 次；同一 IP 每小时 20 次。

    【开发环境】
    验证码放在 dev_code 里返回，方便测试。
    生产环境这个字段是 None。
    """
    ok, message, dev_code = await auth_service.send_code(
        payload.phone, _client_ip(request)
    )

    return ApiResponse[SendCodeOut](
        data=SendCodeOut(
            phone=auth_service.mask_phone(payload.phone),
            expires_in=300,
            dev_code=dev_code,
        )
    )


@router.post("/login", response_model=ApiResponse[LoginOut], summary="登录")
async def login(payload: LoginIn, db: DbDep) -> ApiResponse[LoginOut]:
    """
    【干什么】校验验证码，登录或自动注册。

    【防爆破】
    同一手机号连续失败 5 次，锁 15 分钟。
    """
    # 先查是不是被锁了
    await auth_service.check_login_attempts(payload.phone)

    # 校验验证码
    try:
        await auth_service.verify_code(payload.phone, payload.code)
    except Exception:
        await auth_service.record_login_fail(payload.phone)
        raise

    # 登录成功，清失败计数
    await auth_service.clear_login_fail(payload.phone)

    # 找用户或建用户
    user, is_new = await auth_service.get_or_create_user(db, payload.phone)

    # 签 token
    token = auth_service.make_token(user.id)

    return ApiResponse[LoginOut](
        data=LoginOut(
            token=token,
            user=UserOut(**auth_service.user_to_dict(user)),
            is_new=is_new,
        )
    )


@router.get("/me", response_model=ApiResponse[UserOut], summary="当前用户")
async def me(user: CurrentUserDep) -> ApiResponse[UserOut]:
    """查当前登录用户的信息"""
    return ApiResponse[UserOut](data=UserOut(**auth_service.user_to_dict(user)))


@router.post("/logout", response_model=ApiResponse[dict], summary="退出登录")
async def logout(
    user: CurrentUserDep,
    authorization: str | None = Header(None),
) -> ApiResponse[dict]:
    """
    【干什么】退出登录。

    【做了什么】
    把当前 token 加入黑名单，立即失效。
    即使有人拿到了这个 token，也用不了了。
    """
    if authorization and settings.TOKEN_BLACKLIST_ENABLED:
        parts = authorization.split()
        if len(parts) == 2:
            await auth_service.revoke_token(parts[1])

    return ApiResponse[dict](data={"message": "已退出"})
