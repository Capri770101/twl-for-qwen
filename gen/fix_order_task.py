# -*- coding: utf-8 -*-
"""修正订单超时任务，适配实际模型"""

import os

B = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\backend"

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
#
# 【多机部署要注意】
# 每个进程都会跑这个任务，会重复处理。
# 要么只让一台机器跑，要么用 Redis 分布式锁。
# 单机部署没问题。
# ============================================================

import asyncio
from datetime import datetime, timedelta

import structlog
from sqlalchemy import select, update

from app.core.database import AsyncSessionLocal
from app.models.order import Order, OrderItem, OrderLog, OrderStatus
from app.models.product import Product

logger = structlog.get_logger(__name__)

# 扫描间隔（秒）
SCAN_INTERVAL = 60

# 任务句柄
_task: asyncio.Task | None = None


def _now_str() -> str:
    """
    【干什么】当前的本地时间字符串，格式和数据库一致。

    【为什么用字符串比较】
    expire_at 字段存的是 "2026-10-21 09:49:02" 这种格式。
    同格式的字符串可以直接比较大小，不需要转 datetime。
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


async def cancel_expired_orders() -> int:
    """
    【干什么】扫一遍数据库，把超时的待支付订单取消掉。

    【返回】
        取消了几个订单

    【怎么判断超时】
    expire_at < 当前时间，且状态还是 pending_payment。
    """
    now = _now_str()

    async with AsyncSessionLocal() as db:
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
                # ── 1. 改状态 ──
                from_status = order.status
                order.status = OrderStatus.CANCELLED

                # ── 2. 记日志 ──
                db.add(OrderLog(
                    order_id=order.id,
                    order_no=order.order_no,
                    from_status=from_status,
                    to_status=OrderStatus.CANCELLED,
                    reason="支付超时，系统自动取消",
                    operator="system",
                ))

                # ── 3. 释放库存 ──
                item_result = await db.execute(
                    select(OrderItem).where(OrderItem.order_id == order.id)
                )
                for item in item_result.scalars().all():
                    await db.execute(
                        update(Product)
                        .where(Product.id == item.product_id)
                        .values(stock=Product.stock + item.qty)
                    )

                cancelled += 1
                logger.info("订单超时自动取消", order_no=order.order_no)

            except Exception as e:
                logger.error("取消订单失败", order_no=order.order_no, error=str(e))

        if cancelled:
            await db.commit()

        return cancelled


async def _loop() -> None:
    """循环跑，每 60 秒一次"""
    logger.info("订单超时扫描任务已启动", interval=SCAN_INTERVAL)

    while True:
        try:
            await asyncio.sleep(SCAN_INTERVAL)
            n = await cancel_expired_orders()
            if n:
                logger.info("本轮清理完成", cancelled=n)
        except asyncio.CancelledError:
            logger.info("订单超时扫描任务已停止")
            break
        except Exception as e:
            logger.error("扫描任务异常", error=str(e))
            await asyncio.sleep(SCAN_INTERVAL)


def start() -> None:
    """启动后台任务（在 main.py 的 startup 里调）"""
    global _task
    if _task is not None and not _task.done():
        return
    _task = asyncio.create_task(_loop())


async def stop() -> None:
    """停掉后台任务（在 main.py 的 shutdown 里调）"""
    global _task
    if _task is None:
        return

    _task.cancel()
    try:
        await _task
    except asyncio.CancelledError:
        pass
    _task = None


async def run_once() -> int:
    """
    【干什么】手动跑一次。

    【用在哪】
    测试和运维手动清理时用。
    """
    return await cancel_expired_orders()
'''

with open(os.path.join(B, "app/services/order_task.py"), "w", encoding="utf-8") as f:
    f.write(order_task)
print("  services/order_task.py 已修正")


# ══════════════════════════════════════════════════════════
# 检查 OrderStatus 定义
# ══════════════════════════════════════════════════════════
p = os.path.join(B, "app/models/order.py")
c = open(p, encoding="utf-8").read()
i = c.find("class OrderStatus")
if i > 0:
    print("\n=== OrderStatus 定义 ===")
    print(c[i:i+400])

# ══════════════════════════════════════════════════════════
# 检查 Product 是否有 stock 字段
# ══════════════════════════════════════════════════════════
p2 = os.path.join(B, "app/models/product.py")
c2 = open(p2, encoding="utf-8").read()
print("\n=== Product stock 字段 ===")
if "stock" in c2:
    idx = c2.find("stock")
    print(c2[max(0, idx-100):idx+200])
else:
    print("没有 stock 字段！")
