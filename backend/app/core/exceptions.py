# ============================================================
# 【这个文件是干什么的】
# 统一管理所有业务异常，以及把异常转成 HTTP 响应。
#
# 【为什么要有这个】
# 没有统一异常处理的话：
#   - 每个接口都要写 try/except
#   - 错误格式不统一，前端要写多种判断
#   - 500 错误直接把堆栈暴露给用户，不安全
#
# 有了它：
#   - 业务代码只管 raise 异常
#   - 格式统一（{code, message, detail}）
#   - 生产环境不暴露堆栈
#
# 【怎么用】
#   from app.core.exceptions import NotFoundError, BusinessError
#   raise NotFoundError("商品不存在")
#   raise BusinessError("库存不足", code="OUT_OF_STOCK")
# ============================================================

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


# ════════════════════════════════════════════════════════════
# 【业务异常基类】
#
# 所有业务异常都继承它。
# 带 code 和 message，前端能根据 code 做不同处理。
# ════════════════════════════════════════════════════════════
class BusinessError(Exception):
    """
    【干什么】业务逻辑错误的基类。

    【参数】
        message: 给人看的错误说明
        code:    给程序看的错误码（前端根据这个判断怎么处理）
        status_code: HTTP 状态码
        detail:  额外信息（可选）
    """

    def __init__(
        self,
        message: str,
        *,
        code: str = "BUSINESS_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: Any = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


# ════════════════════════════════════════════════════════════
# 【常用异常 —— 直接用这些，不用每次写 BusinessError】
# ════════════════════════════════════════════════════════════

class NotFoundError(BusinessError):
    """资源不存在（商品、订单、工单找不到）"""

    def __init__(self, message: str = "资源不存在", detail: Any = None) -> None:
        super().__init__(
            message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class ValidationError(BusinessError):
    """参数校验失败（缺字段、格式不对）"""

    def __init__(self, message: str, detail: Any = None) -> None:
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class UnauthorizedError(BusinessError):
    """未登录 / Token 无效"""

    def __init__(self, message: str = "请先登录") -> None:
        super().__init__(
            message,
            code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenError(BusinessError):
    """没权限"""

    def __init__(self, message: str = "没有权限") -> None:
        super().__init__(
            message,
            code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ConflictError(BusinessError):
    """状态冲突（比如订单状态不允许这个操作）"""

    def __init__(self, message: str, detail: Any = None) -> None:
        super().__init__(
            message,
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


# ════════════════════════════════════════════════════════════
# 【具体业务异常】
# ════════════════════════════════════════════════════════════

class OutOfStockError(BusinessError):
    """库存不足"""

    def __init__(self, product_name: str) -> None:
        super().__init__(
            f"库存不足: {product_name}",
            code="OUT_OF_STOCK",
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"product_name": product_name},
        )


class InvalidStatusTransition(BusinessError):
    """订单状态流转不合法"""

    def __init__(self, from_status: str, to_status: str) -> None:
        super().__init__(
            f"不允许的状态流转: {from_status} → {to_status}",
            code="INVALID_STATUS_TRANSITION",
            status_code=status.HTTP_409_CONFLICT,
            detail={"from": from_status, "to": to_status},
        )


class PaymentError(BusinessError):
    """支付相关错误"""

    def __init__(self, message: str, detail: Any = None) -> None:
        super().__init__(
            message,
            code="PAYMENT_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


# ════════════════════════════════════════════════════════════
# 【异常处理器 —— 把异常转成统一的 JSON 响应】
#
# 注册到 FastAPI 后，所有异常都会被这里接管。
# ════════════════════════════════════════════════════════════

def _error_response(
    status_code: int,
    code: str,
    message: str,
    detail: Any = None,
) -> JSONResponse:
    """
    【干什么】生成统一格式的错误响应。

    【格式】
    {
        "code": "NOT_FOUND",
        "message": "商品不存在",
        "detail": null
    }
    """
    body: dict[str, Any] = {"code": code, "message": message}
    if detail is not None:
        body["detail"] = detail
    return JSONResponse(status_code=status_code, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    """
    【干什么】把所有异常处理器注册到 FastAPI 应用上。

    【在哪调用】app/main.py 里创建 app 之后立刻调用。
    """

    # ── 1. 业务异常 ──
    @app.exception_handler(BusinessError)
    async def business_error_handler(request: Request, exc: BusinessError):
        # 业务异常是预期内的，用 warning 级别，不用 error
        logger.warning(
            "业务异常",
            path=request.url.path,
            code=exc.code,
            message=exc.message,
        )
        return _error_response(exc.status_code, exc.code, exc.message, exc.detail)

    # ── 2. 参数校验失败（FastAPI 自动抛的）──
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        logger.warning(
            "参数校验失败",
            path=request.url.path,
            errors=exc.errors(),
        )
        # 把 Pydantic 的错误信息整理成人能看懂的样子
        details = [
            {
                "field": ".".join(str(x) for x in e["loc"][1:]) or str(e["loc"]),
                "message": e["msg"],
            }
            for e in exc.errors()
        ]
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "VALIDATION_ERROR",
            "请求参数有误",
            details,
        )

    # ── 3. HTTP 异常（FastAPI 内置的 404 等）──
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return _error_response(
            exc.status_code,
            f"HTTP_{exc.status_code}",
            str(exc.detail),
        )

    # ── 4. 兜底：所有未捕获的异常 ──
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # 这是没预料到的错误，用 error 级别，带完整堆栈
        logger.error(
            "未处理的异常",
            path=request.url.path,
            exc_info=exc,
        )
        # 【重要】生产环境不暴露堆栈给用户
        if settings_is_dev():
            message = f"{type(exc).__name__}: {exc}"
        else:
            message = "服务器内部错误，请稍后重试"
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "INTERNAL_ERROR",
            message,
        )


def settings_is_dev() -> bool:
    """判断是不是开发环境（用来决定要不要暴露错误细节）"""
    from app.core.config import settings

    return settings.APP_ENV == "development"
