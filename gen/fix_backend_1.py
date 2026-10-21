# -*- coding: utf-8 -*-
"""阶段1：订单超时任务 + 日志脱敏 + 请求ID"""

import os

B = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\backend"

# ══════════════════════════════════════════════════════════
# 1. 订单超时自动取消任务
# ══════════════════════════════════════════════════════════
order_task = '''# ============================================================
# 【这个文件是干什么的】
# 后台定时任务：扫描超时未支付的订单，自动取消并释放库存。
#
# 【为什么需要】
# 用户下单后不付钱，库存就被占着。不清理的话，
# 热门商品会被「假单」锁死，别人买不到。
#
# 【怎么跑的】
# 服务启动时创建一个 asyncio 后台任务，每隔 60 秒跑一次。
# 不用 Celery / APScheduler，因为只有一个任务，asyncio 够了。
#
# 【正式环境建议】
# 多机部署时每个进程都会跑这个任务，会重复处理。
# 要么只让一台机器跑，要么用 Redis 分布式锁。
# 现在单机部署没问题，注释里标了要多机时改哪里。
# ============================================================

import asyncio

import structlog
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.order import Order, OrderStatus

logger = structlog.get_logger(__name__)

# 扫描间隔（秒）
SCAN_INTERVAL = 60

# 任务句柄
_task: asyncio.Task | None = None

# 是否正在运行（防止重入）
_running = False


async def cancel_expired_orders() -> int:
    """
    【干什么】扫一遍数据库，把超时的待支付订单取消掉。

    【返回】
        取消了几个订单

    【怎么判断超时】
    expire_at < 当前时间，且状态还是 pending_payment。
    """
    from datetime import datetime, timezone

    from sqlalchemy import update

    from app.models.order import OrderLog

    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # 查超时订单
        result = await db.execute(
            select(Order).where(
                Order.status == OrderStatus.PENDING_PAYMENT,
                Order.expire_at.isnot(None),
                Order.expire_at < now,
            )
        )
        orders = result.scalars().all()

        if not orders:
            return 0

        cancelled = 0

        for order in orders:
            try:
                # 改状态
                order.status = OrderStatus.CANCELLED
                order.cancel_reason = "支付超时，系统自动取消"

                # 记日志
                db.add(OrderLog(
                    order_id=order.id,
                    status=OrderStatus.CANCELLED,
                    status_text="已取消",
                    reason="支付超时自动取消",
                    operator="system",
                ))

                # 释放库存
                from app.models.product import Product
                for item in order.items:
                    await db.execute(
                        update(Product)
                        .where(Product.id == item.product_id)
                        .values(stock=Product.stock + item.qty)
                    )

                cancelled += 1
                logger.info(
                    "订单超时自动取消",
                    order_no=order.order_no,
                )

            except Exception as e:
                logger.error(
                    "取消订单失败",
                    order_no=order.order_no,
                    error=str(e),
                )

        if cancelled:
            await db.commit()

        return cancelled


async def _loop() -> None:
    """
    【干什么】循环跑，每 60 秒一次。

    【怎么停】
    进程退出时 cancel。
    """
    global _running
    _running = True
    logger.info("订单超时扫描任务已启动", interval=SCAN_INTERVAL)

    while True:
        try:
            await asyncio.sleep(SCAN_INTERVAL)
            n = await cancel_expired_orders()
            if n:
                logger.info("本轮清理完成", cancelled=n)
        except asyncio.CancelledError:
            logger.info("订单超时扫描任务已停止")
            _running = False
            break
        except Exception as e:
            logger.error("扫描任务异常", error=str(e))
            # 出错了也继续，不要整个任务挂掉
            await asyncio.sleep(SCAN_INTERVAL)


def start() -> None:
    """
    【干什么】启动后台任务。

    【在哪调用】
    main.py 的 startup 里。

    【只跑一次】
    重复调用会直接返回。
    """
    global _task
    if _task is not None and not _task.done():
        return
    _task = asyncio.create_task(_loop())


async def stop() -> None:
    """
    【干什么】停掉后台任务。

    【在哪调用】
    main.py 的 shutdown 里。
    """
    global _task
    if _task is None:
        return

    _task.cancel()
    try:
        await _task
    except asyncio.CancelledError:
        pass
    _task = None
'''

with open(os.path.join(B, "app/services/order_task.py"), "w", encoding="utf-8") as f:
    f.write(order_task)
print("  services/order_task.py")


# ══════════════════════════════════════════════════════════
# 2. 日志中间件（请求 ID + 脱敏）
# ══════════════════════════════════════════════════════════
log_mw = '''# ============================================================
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
_PHONE_RE = re.compile(r"\\b(1[3-9]\\d)\\d{4}(\\d{4})\\b")

# 身份证：110*** **** **** 1234
_IDCARD_RE = re.compile(r"\\b(\\d{3})\\d{11}(\\d{4})\\b")

# token（user_id.expire.sig 格式或 JWT）
_TOKEN_RE = re.compile(r"\\b[A-Za-z0-9_-]{20,}\\.[A-Za-z0-9_-]{6,}\\.[a-f0-9]{16,}\\b")

# 邮箱
_EMAIL_RE = re.compile(r"\\b([\\w.+-]{1,3})[\\w.+-]*(@[\\w.-]+)\\b")


def mask_sensitive(text: str) -> str:
    """
    【干什么】把文本里的敏感信息打码。

    【例子】
        13812345678   → 138****5678
        13812345678@x → 138****5678
        token 字符串   → ***
    """
    if not text:
        return text

    text = _PHONE_RE.sub(r"\\1****\\2", text)
    text = _IDCARD_RE.sub(r"\\1***********\\2", text)
    text = _TOKEN_RE.sub("***TOKEN***", text)
    text = _EMAIL_RE.sub(r"\\1***\\2", text)

    return text


def mask_dict(data: dict) -> dict:
    """
    【干什么】把 dict 里的敏感字段打码。

    【哪些字段】
    名字里带 phone / token / password / secret / key 的。
    """
    if not isinstance(data, dict):
        return data

    sensitive_keys = ("phone", "token", "password", "secret", "key", "authorization")

    out = {}
    for k, v in data.items():
        k_lower = str(k).lower()

        if any(s in k_lower for s in sensitive_keys):
            if isinstance(v, str) and len(v) > 6:
                out[k] = v[:3] + "***" + v[-2:]
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
'''

with open(os.path.join(B, "app/core/request_log.py"), "w", encoding="utf-8") as f:
    f.write(log_mw)
print("  core/request_log.py")

print("\n阶段1 部分完成")
