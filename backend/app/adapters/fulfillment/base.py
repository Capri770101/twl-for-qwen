# ============================================================
# 【这个文件是干什么的】
# 履约系统的抽象接口 —— 定义「怎么把订单推给花店」。
#
# 【履约方是什么】
# 负责做花、送花的一方。可能是：
#   - 企业自有的花艺团队
#   - 合作的花店
#   - 第三方配送平台
#
# 【本系统的职责边界】
# 本系统只负责「推送订单」和「接收状态回传」，
# 不负责实际的花艺制作和配送执行。
# ============================================================

from abc import ABC, abstractmethod
from typing import Any


class FulfillmentAdapter(ABC):
    """
    【干什么】履约系统的抽象基类。

    【子类必须实现】
        push_order        —— 推送订单
        parse_callback    —— 解析对方回传的状态
    """

    @abstractmethod
    async def push_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        【干什么】把订单推送给履约方。

        【参数】
            payload: 订单的完整信息，包含：
                - order_no:     订单号
                - receiver:     收花人姓名
                - phone:        收花人电话
                - address:      收花地址
                - delivery_date: 配送日期
                - delivery_slot: 配送时段
                - card_message: 贺卡留言
                - items:        商品列表

        【返回】
            {
                "success": True,
                "external_ref": "对方系统的单号",
                "message": "接单成功"
            }

        【可能抛出】
            FulfillmentError：推送失败（网络问题、对方拒单等）
        """
        ...

    @abstractmethod
    async def parse_callback(self, body: dict[str, Any]) -> dict[str, Any]:
        """
        【干什么】解析履约方回传的状态。

        【返回格式】
        {
            "order_no": "TWL123",
            "status": "delivering",   # delivering / delivered
            "message": "骑手已取货"
        }
        """
        ...


class FulfillmentError(Exception):
    """【干什么】履约推送失败时抛的异常"""

    def __init__(self, message: str, detail: Any = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)
