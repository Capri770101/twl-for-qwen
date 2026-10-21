# -*- coding: utf-8 -*-
"""
一键清空演示数据

【怎么用】
    cd scripts
    python reset_demo.py

【会做什么】
    1. 删掉所有 is_demo=true 的商品
    2. 删掉所有 is_demo=true 的订单（及其明细、日志、支付、配送、工单）
    3. 删掉测试用户（手机号以 136/137/138/139 开头的非管理员）
    4. 保留管理员账号

【不会做什么】
    - 不删表结构
    - 不删管理员
    - 不删系统配置（配送规则等，老板填的）
    - 不删花语文章（内容是真实资产）

【什么时候用】
    老板接手、灌真实数据之前。
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from sqlalchemy import delete, select, text

from app.core.database import AsyncSessionLocal, check_database_connection
from app.core.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


async def main():
    print("=" * 70)
    print("  清空演示数据")
    print("=" * 70)
    print()

    if not await check_database_connection():
        print("数据库连不上")
        sys.exit(1)

    # 确认
    print("⚠ 这个操作会删除所有演示数据，不可恢复。")
    ans = input("确认继续？输入 yes 继续，其他任意键取消：").strip().lower()

    if ans != "yes":
        print("已取消")
        return

    print()

    async with AsyncSessionLocal() as db:
        # ── 1. 统计要删什么 ──
        r = await db.execute(text("SELECT COUNT(*) FROM products WHERE is_demo = true"))
        n_products = r.scalar()

        r = await db.execute(text("SELECT COUNT(*) FROM orders WHERE is_demo = true"))
        n_orders = r.scalar()

        print(f"将删除：")
        print(f"  商品   {n_products} 个")
        print(f"  订单   {n_orders} 笔（含明细、日志、支付、配送、工单）")
        print()

        # ── 2. 删关联表 ──
        # 先从订单派生的表开始删
        print("删除关联数据...")

        # 订单号列表
        r = await db.execute(text("SELECT order_no FROM orders WHERE is_demo = true"))
        order_nos = [row[0] for row in r.fetchall()]

        if order_nos:
            # 用 IN 批量删
            placeholders = ",".join(f"'{x}'" for x in order_nos)

            tables = [
                ("order_logs", "order_no"),
                ("payments", "order_no"),
                ("deliveries", "order_no"),
                ("tickets", "order_no"),
            ]

            for table, col in tables:
                result = await db.execute(
                    text(f"DELETE FROM {table} WHERE {col} IN ({placeholders})")
                )
                print(f"  ✓ {table}: {result.rowcount} 行")

            # 订单明细（按 order_id）
            r = await db.execute(
                text("SELECT id FROM orders WHERE is_demo = true")
            )
            order_ids = [row[0] for row in r.fetchall()]
            if order_ids:
                id_phs = ",".join(f"'{x}'" for x in order_ids)
                result = await db.execute(
                    text(f"DELETE FROM order_items WHERE order_id IN ({id_phs})")
                )
                print(f"  ✓ order_items: {result.rowcount} 行")

            # 订单主表
            result = await db.execute(
                text(f"DELETE FROM orders WHERE order_no IN ({placeholders})")
            )
            print(f"  ✓ orders: {result.rowcount} 行")

        # ── 3. 删商品 ──
        result = await db.execute(
            text("DELETE FROM products WHERE is_demo = true")
        )
        print(f"  ✓ products: {result.rowcount} 个")

        # ── 4. 删测试用户（保留管理员）──
        result = await db.execute(
            text("DELETE FROM users WHERE is_admin = false")
        )
        print(f"  ✓ users: {result.rowcount} 个（保留管理员）")

        # ── 5. 删测试地址 ──
        # 用户删了，地址会级联删除（如果有外键）
        result = await db.execute(text("DELETE FROM addresses"))
        print(f"  ✓ addresses: {result.rowcount} 条")

        await db.commit()

    print()
    print("=" * 70)
    print("  完成。数据库已清空演示数据。")
    print("=" * 70)
    print()
    print("接下来：")
    print("  1. 改 .env：DEMO_MODE=false")
    print("  2. 后台填真实配送规则")
    print("  3. 灌真实商品（后台手工录，或接数据源）")
    print()


if __name__ == "__main__":
    asyncio.run(main())
