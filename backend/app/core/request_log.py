# ============================================================
# 【这个文件是干什么的】
# 请求日志中间件：给每个请求分配 ID，记录耗时，脱敏敏感信息。
#
# 【为什么要请求 ID】
# 一个请求可能打多行日志（进入、查库、出错）。
# 有了统一的 ID，排查问题时能把这些日志串起来。
#
# 【为什么要脱敏】
# 手机号、token 进了日志，等于把用户隐私写在了文件里。
# 一旦日志被泄露或误传，就是数据事故。
# ============================================================

import re
import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = structlog.get_logger(__name__)


# ════════════════════════════════════════════════════════════
# 【脱敏规则】
# ════════════════════════════════════════════════════════════

# 手机号：138****1234
_PHONE_RE = re.compile(r"\b(1[3-9]\d)\d{4}(\d{4})\b")

# 身份证：110*** **** **** 1234
_IDCARD_RE = re.compile(r"\b(\d{3})\d{11}(\d{4})\b")

# token（user_id.expire.sig 格式或 JWT）
# 第一段可能是 u123456789012 这种短 ID，所以下限放低到 6
_TOKEN_RE = re.compile(r"\b[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{6,}\.[a-f0-9]{16,}\b")

# 邮箱
_EMAIL_RE = re.compile(r"\b([\w.+-]{1,3})[\w.+-]*(@[\w.-]+)\b")


def mask_sensitive(text: str) -> str:
    """
    【干什么】把文本里的敏感信息打码。

    【例子】
        13812345678   → 138****5678
        13812345678@x → 138****5678
        token 字符串   → ***TOKEN***
    """
    if not text:
        return text

    text = _PHONE_RE.sub(r"\1****\2", text)
    text = _IDCARD_RE.sub(r"\1***********\2", text)
    text = _TOKEN_RE.sub("***TOKEN***", text)
    text = _EMAIL_RE.sub(r"\1***\2", text)

    return text


def mask_dict(data: dict) -> dict:
    """
    【干什么】把 dict 里的敏感字段打码。

    【两类字段，处理方式不同】
    · phone  → 保留首尾（138****5678），便于核对是哪个用户
    · token / password / secret / key / authorization
      → 完全替换成 ***，一点都不能露

    【为什么要分开】
    token 泄露等于账号被盗，连前 3 位都不该出现。
    """
    if not isinstance(data, dict):
        return data

    # 需要完全隐藏的
    hard_keys = ("token", "password", "passwd", "secret", "key", "authorization", "credential")

    # 可以保留首尾的
    soft_keys = ("phone", "mobile", "tel")

    out = {}
    for k, v in data.items():
        k_lower = str(k).lower()

        if any(s in k_lower for s in hard_keys):
            # 完全隐藏
            out[k] = "***"

        elif any(s in k_lower for s in soft_keys):
            # 手机号用专门的规则（138****5678）
            if isinstance(v, str):
                out[k] = mask_sensitive(v)
            else:
                out[k] = "***"

        elif isinstance(v, str):
            out[k] = mask_sensitive(v)
        elif isinstance(v, dict):
            out[k] = mask_dict(v)
        else:
            out[k] = v

    return out


# ════════════════════════════════════════════════════════════
# 【中间件】
# ════════════════════════════════════════════════════════════

class RequestLogMiddleware(BaseHTTPMiddleware):
    """
    【干什么】给每个请求：
    1. 分配一个 request_id
    2. 记录耗时和状态码
    3. 把 request_id 塞进响应头（方便前端报错时提供）
    """

    async def dispatch(self, request: Request, call_next):
        # 用客户端传的 request_id（如果有），否则新建
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]

        # 绑定到当前请求的日志上下文
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            # 异常也要记录
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(
                "请求异常",
                method=request.method,
                path=request.url.path,
                duration_ms=round(elapsed, 1),
            )
            raise

        elapsed = (time.perf_counter() - start) * 1000

        # 记录（路径里的敏感信息也要脱敏）
        logger.info(
            "请求",
            method=request.method,
            path=mask_sensitive(request.url.path),
            status=response.status_code,
            duration_ms=round(elapsed, 1),
        )

        # 响应头带上 request_id
        response.headers["X-Request-Id"] = request_id

        return response
