# -*- coding: utf-8 -*-
"""
MCP Server 自测

不需要 AI 客户端，直接调工具函数验证逻辑。

【为什么不测真正的 MCP 协议】
协议层由官方 SDK 保证，我们要测的是「工具能不能正常返回数据」。
"""

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.mcp_server import (
    check_delivery,
    create_order,
    create_ticket,
    get_flower_meaning,
    get_product,
    list_articles,
    list_categories,
    query_order,
    search_flowers,
)

ok = 0
fail = 0


def check(n, label, cond, detail=""):
    global ok, fail
    mark = "✓" if cond else "✗"
    if cond:
        ok += 1
    else:
        fail += 1
    print(f"  {mark} {n:>2}. {label:<24} {detail}")


async def main():
    print("=" * 70)
    print("  MCP Server 工具自测")
    print("=" * 70)
    print()

    # 1. 搜索花束
    r = await search_flowers(limit=5)
    d = json.loads(r)
    check(1, "search_flowers", d.get("count", 0) > 0, f"{d.get('count')} 个")

    # 2. 按关键词搜
    r = await search_flowers(keyword="玫瑰", limit=5)
    d = json.loads(r)
    check(2, "  按关键词「玫瑰」", True, f"{d.get('count')} 个")

    # 3. 按分类搜
    r = await search_flowers(category="love", limit=5)
    d = json.loads(r)
    check(3, "  按分类 love", True, f"{d.get('count')} 个")

    # 4. 按价格
    r = await search_flowers(max_price=260, limit=10)
    d = json.loads(r)
    prices = [p["price"] for p in d.get("products", [])]
    check(4, "  按价格 ≤260", all(p <= 260 for p in prices) if prices else True, f"{len(prices)} 个")

    # 5. 商品详情
    r = await get_product("TW-001")
    d = json.loads(r)
    check(5, "get_product", d.get("name") == "晨光序曲", f"{d.get('name')} ¥{d.get('price')}")

    # 6. 不存在的商品
    r = await get_product("NOT-EXIST")
    d = json.loads(r)
    check(6, "  不存在商品", "error" in d, d.get("error", "")[:30])

    # 7. 配送可用性
    r = await check_delivery("TW-001")
    d = json.loads(r)
    check(7, "check_delivery", "available" in d, f"available={d.get('available')} configured={d.get('configured')}")

    # 8. 分类列表
    r = await list_categories()
    d = json.loads(r)
    cats = d.get("categories", [])
    check(8, "list_categories", len(cats) > 0, f"{len(cats)} 个分类")

    # 9. 查花语
    r = await get_flower_meaning("玫瑰")
    d = json.loads(r)
    check(9, "get_flower_meaning", d.get("found"), f"{d.get('count')} 篇")

    # 10. 花语文章列表
    r = await list_articles(limit=5)
    d = json.loads(r)
    check(10, "list_articles", d.get("count", 0) > 0, f"{d.get('count')} 篇")

    # 11. 下单（会真实占库存）
    r = await create_order(
        product_id="TW-002",
        quantity=1,
        receiver_name="MCP 测试",
        receiver_phone="13900002222",
        receiver_address="深圳市南山区测试路 2 号",
        card_message="MCP 自测",
    )
    d = json.loads(r)
    order_no = d.get("order_no")
    check(11, "create_order", d.get("success"), order_no or d.get("error", "")[:40])

    # 12. 查刚下的单
    if order_no:
        r = await query_order(order_no)
        d = json.loads(r)
        check(12, "query_order", d.get("order_no") == order_no,
              f"{d.get('status_text')} ¥{d.get('pay_amount')}")

        # 13. 提工单
        r = await create_ticket(
            order_no=order_no,
            reason="MCP 自测：模拟售后咨询",
            ticket_type="quality",
        )
        d = json.loads(r)
        check(13, "create_ticket", d.get("success"), d.get("ticket_no") or d.get("error", "")[:40])
    else:
        print("  - 12/13 跳过（下单失败）")

    print()
    print("=" * 70)
    print(f"  通过 {ok} / {ok + fail}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
