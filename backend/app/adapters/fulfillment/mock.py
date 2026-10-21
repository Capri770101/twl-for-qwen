# ============================================================
# 【这个文件是干什么的】
# Mock 履约适配器 —— 开发测试用。
#
# 【它做什么】
# 「假装」把订单推给了一方，实际上只打日志、返回成功。
#
# 【为什么需要它】
# 开发和测试时不依赖真实履约系统，也能跑通完整流程。
# ============================================================

import uuid
from typing import Any

from app.adapters.fulfillment.base import FulfillmentAdapter
from app.core.logging import get_logger

logger = get_logger(__name__)


class MockFulfillmentAdapter(FulfillmentAdapter):
    """【干什么】假的履约系统，推送即成功"""

    async def push_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        【干什么】假装推送订单。

        【做了什么】
        打一条日志，返回一个假的单号。
        """
        order_no = payload.get("order_no", "")
        external_ref = "MOCK-" + uuid.uuid4().hex[:12].upper()

        logger.info(
            "【Mock 履约】推送订单",
            order_no=order_no,
            receiver=payload.get("receiver"),
            address=payload.get("address"),
            items_count=len(payload.get("items", [])),
        )

        return {
            "success": True,
            "external_ref": external_ref,
            "message": "Mock 履约：已接收",
        }

    async def parse_callback(self, body: dict[str, Any]) -> dict[str, Any]:
        """【干什么】解析履约方回调（Mock 版直接读字段）"""
        return {
            "order_no": body.get("order_no", ""),
            "status": body.get("status", ""),
            "message": body.get("message", ""),
        }
