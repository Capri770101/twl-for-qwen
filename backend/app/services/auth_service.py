# ============================================================
# 【这个文件是干什么的】
# 登录相关的业务逻辑：验证码、限流、token 签发与校验。
#
# 【生产级设计】
#   - 验证码存缓存层（开发=内存，生产=Redis）
#   - 发送走短信适配器（开发=Mock，生产=阿里云）
#   - 三重限流：手机号间隔、手机号日限、IP 时限
#   - token 支持黑名单（退出登录后立即失效）
# ============================================================

import hashlib
import hmac
import random
import secrets
import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.cache import get_cache
from app.adapters.sms import get_sms
from app.core.config import settings
from app.core.exceptions import BusinessError
from app.models.user import User

# ════════════════════════════════════════════════════════════
# 【常量】
# ════════════════════════════════════════════════════════════

CODE_TTL = 300            # 验证码有效期（秒）
CODE_LENGTH = 6           # 验证码位数
MAX_VERIFY_FAIL = 5       # 验证码最多试错次数


# ════════════════════════════════════════════════════════════
# 【Token】
# ════════════════════════════════════════════════════════════

def _secret() -> bytes:
    """取签名密钥"""
    return settings.SECRET_KEY.encode()


def _sign(payload: str) -> str:
    """HMAC-SHA256 签名"""
    return hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()[:32]


def make_token(user_id: str) -> str:
    """
    【干什么】签发 token。

    【格式】
        user_id.expire_ts.signature

    【为什么这样设计】
    无状态，服务端不用存 session，重启也不影响已发出的 token。
    缺点是没法主动作废 —— 所以加了黑名单。
    """
    expire = int(time.time()) + settings.TOKEN_EXPIRE_MINUTES * 60
    payload = f"{user_id}.{expire}"
    return f"{payload}.{_sign(payload)}"


async def parse_token(token: str) -> str:
    """
    【干什么】校验 token，返回 user_id。

    【校验顺序】
    1. 格式
    2. 黑名单（退出登录的 token）
    3. 签名
    4. 过期时间
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise BusinessError("token 格式不对", code="UNAUTHORIZED", status_code=401)

    user_id, expire_str, sig = parts
    payload = f"{user_id}.{expire_str}"

    # 黑名单检查
    if settings.TOKEN_BLACKLIST_ENABLED:
        cache = get_cache()
        if await cache.exists(f"token:blacklist:{sig}"):
            raise BusinessError("登录已失效，请重新登录", code="UNAUTHORIZED", status_code=401)

    # 签名
    if not hmac.compare_digest(sig, _sign(payload)):
        raise BusinessError("token 无效", code="UNAUTHORIZED", status_code=401)

    # 过期
    try:
        expire_ts = int(expire_str)
    except ValueError:
        raise BusinessError("token 格式不对", code="UNAUTHORIZED", status_code=401)

    if expire_ts < time.time():
        raise BusinessError("登录已过期，请重新登录", code="UNAUTHORIZED", status_code=401)

    return user_id


async def revoke_token(token: str) -> None:
    """
    【干什么】把 token 加入黑名单（退出登录）。

    【存多久】
    存到 token 自然过期为止，过了就没必要留了。
    """
    parts = token.split(".")
    if len(parts) != 3:
        return

    _, expire_str, sig = parts
    try:
        remain = int(expire_str) - int(time.time())
    except ValueError:
        return

    if remain <= 0:
        return

    cache = get_cache()
    await cache.set(f"token:blacklist:{sig}", "1", ttl=remain)


# ════════════════════════════════════════════════════════════
# 【限流】
# ════════════════════════════════════════════════════════════

async def _check_rate_limit(phone: str, client_ip: str) -> None:
    """
    【干什么】发验证码前的三重限流检查。

    【为什么三重】
    1. 手机号间隔 60 秒 —— 防止连续点
    2. 手机号日限 10 次 —— 防止一个号被刷爆
    3. IP 时限 20 次 —— 防止一个人刷很多号
    """
    cache = get_cache()

    # 1. 间隔
    last_key = f"sms:last:{phone}"
    if await cache.exists(last_key):
        raise BusinessError(
            f"请 {settings.SMS_INTERVAL_SECONDS} 秒后再试",
            code="SMS_TOO_FREQUENT",
        )

    # 2. 日限
    day_key = f"sms:day:{phone}"
    day_count = int(await cache.get(day_key) or 0)
    if day_count >= settings.SMS_DAILY_LIMIT:
        raise BusinessError("今天验证码次数用完了，明天再来", code="SMS_DAILY_LIMIT")

    # 3. IP 时限
    if client_ip:
        ip_key = f"sms:ip:{client_ip}"
        ip_count = int(await cache.get(ip_key) or 0)
        if ip_count >= settings.SMS_IP_HOURLY_LIMIT:
            raise BusinessError("请求太频繁，请稍后再试", code="SMS_IP_LIMIT")


async def _record_send(phone: str, client_ip: str) -> None:
    """记录一次发送（用于下次限流判断）"""
    cache = get_cache()
    await cache.set(f"sms:last:{phone}", "1", ttl=settings.SMS_INTERVAL_SECONDS)
    await cache.incr(f"sms:day:{phone}", ttl=86400)
    if client_ip:
        await cache.incr(f"sms:ip:{client_ip}", ttl=3600)


async def check_login_attempts(phone: str) -> None:
    """
    【干什么】检查这个手机号是不是被锁了。

    【为什么】
    防止有人拿一个手机号暴力试验证码。
    """
    cache = get_cache()
    key = f"login:fail:{phone}"
    count = int(await cache.get(key) or 0)

    if count >= settings.LOGIN_MAX_ATTEMPTS:
        raise BusinessError(
            f"失败次数过多，请 {settings.LOGIN_LOCK_MINUTES} 分钟后再试",
            code="ACCOUNT_LOCKED",
        )


async def record_login_fail(phone: str) -> None:
    """记一次登录失败"""
    cache = get_cache()
    await cache.incr(f"login:fail:{phone}", ttl=settings.LOGIN_LOCK_MINUTES * 60)


async def clear_login_fail(phone: str) -> None:
    """登录成功，清掉失败计数"""
    cache = get_cache()
    await cache.delete(f"login:fail:{phone}")


# ════════════════════════════════════════════════════════════
# 【验证码】
# ════════════════════════════════════════════════════════════

def mask_phone(phone: str | None) -> str | None:
    """手机号脱敏"""
    if not phone or len(phone) != 11:
        return phone
    return f"{phone[:3]}****{phone[-4:]}"


async def send_code(phone: str, client_ip: str = "") -> tuple[bool, str, str | None]:
    """
    【干什么】生成并发送验证码。

    【返回】
        (成功?, 提示语, 验证码[仅开发环境返回])

    【流程】
    1. 限流检查
    2. 生成 6 位数字
    3. 存缓存
    4. 调短信适配器发送
    5. 记录发送（供下次限流）
    """
    await _check_rate_limit(phone, client_ip)

    code = f"{random.randint(0, 10**CODE_LENGTH - 1):0{CODE_LENGTH}d}"

    cache = get_cache()
    await cache.set(f"sms:code:{phone}", code, ttl=CODE_TTL)
    await cache.set(f"sms:code:fail:{phone}", "0", ttl=CODE_TTL)

    # 发短信
    sms = get_sms()
    result = await sms.send_code(phone, code)

    if not result.success:
        raise BusinessError(result.message or "短信发送失败", code="SMS_SEND_FAILED")

    await _record_send(phone, client_ip)

    # 只有开发环境才把验证码返回给前端
    dev_code = code if settings.APP_ENV != "production" else None

    return True, result.message, dev_code


async def verify_code(phone: str, code: str) -> None:
    """
    【干什么】校验验证码，不通过抛异常。

    【安全设计】
    - 验证码只能用一次（校验完删掉）
    - 最多试错 5 次（超了就作废，必须重新获取）
    - 用 hmac.compare_digest 防时序攻击
    """
    cache = get_cache()
    stored = await cache.get(f"sms:code:{phone}")

    if not stored:
        raise BusinessError("请先获取验证码", code="CODE_REQUIRED")

    fail_key = f"sms:code:fail:{phone}"
    fail_count = int(await cache.get(fail_key) or 0)

    if fail_count >= MAX_VERIFY_FAIL:
        await cache.delete(f"sms:code:{phone}")
        await cache.delete(fail_key)
        raise BusinessError("错误次数过多，请重新获取验证码", code="TOO_MANY_ATTEMPTS")

    if not hmac.compare_digest(stored, code):
        await cache.incr(fail_key, ttl=CODE_TTL)
        raise BusinessError("验证码不对", code="CODE_INVALID")

    # 通过，立即作废
    await cache.delete(f"sms:code:{phone}")
    await cache.delete(fail_key)


# ════════════════════════════════════════════════════════════
# 【用户】
# ════════════════════════════════════════════════════════════

async def get_or_create_user(db: AsyncSession, phone: str) -> tuple[User, bool]:
    """
    【干什么】按手机号找用户，没有就建一个。

    【管理员怎么来的】
    ADMIN_PHONES 里配的手机号，注册时自动成为管理员。
    上线前必须清空这个配置。
    """
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()

    if user:
        return user, False

    is_admin = phone in settings.admin_phones_list

    user = User(
        id=f"u{secrets.token_hex(12)}",
        phone=phone,
        channel="phone",
        nickname=f"用户{phone[-4:]}",
        is_active=True,
        is_admin=is_admin,
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
    """ORM → dict"""
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
        "is_admin": bool(getattr(user, "is_admin", False)),
        "created_at": created,
    }
