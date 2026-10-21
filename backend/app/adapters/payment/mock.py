# ============================================================
# 【这个文件是干什么的】
# Mock 支付适配器 —— 开发测试用的假支付网关。
#
# 【它做什么】
# - 发起支付：返回一个假的收银台地址
# - 验证回调：永远返回 True（不验签）
# - 解析回调：直接按约定的格式读
#
# 【什么时候用】
# 开发环境、测试环境。生产环境要换成真实的微信/支付宝适配器。
#
# 【怎么切换】
# 在 .env 里设置 PAYMENT_PROVIDER=wechat 或 alipay。
# ============================================================

from decimal import Decimal
from typing import Any

from app.adapters.payment.base import PaymentAdapter
from app.core.logging import get_logger

logger = get_logger(__name__)


class MockPaymentAdapter(PaymentAdapter):
    """【干什么】假的支付网关，点一下就成功"""

    async def create_payment(
        self,
        order_no: str,
        amount: Decimal,
        channel: str,
    ) -> dict[str, Any]:
        """
        【干什么】发起支付。

        【返回什么】
        一个假的收银台地址。前端跳过去，有个「确认支付」按钮，
        点了就当作支付成功。
        """
        logger.info(
            "【Mock 支付】发起支付",
            order_no=order_no,
            amount=str(amount),
            channel=channel,
        )

        return {
            # 前端跳这个地址，就是个假收银台页面
            "mock_pay_url": f"/api/v1/payments/mock/pay?order_no={order_no}",
            # 真实渠道的字段留空
            "prepay_id": None,
            "pay_sign": None,
            "timestamp": None,
            "nonce_str": None,
            "pay_url": None,
        }

    async def verify_callback(
        self,
        headers: dict[str, str],
        body: bytes,
    ) -> bool:
        """
        【干什么】验证回调。

        【Mock 版】永远返回 True。

        【真实版必须做】
        微信：HMAC-SHA256 验签
        支付宝：RSA2 验签
        不做的话，任何人伪造一个请求就能白拿花。
        """
        logger.warning("【Mock 支付】跳过验签 —— 生产环境绝对不能这样")
        return True

    async def parse_callback(self, body: bytes) -> dict[str, Any]:
        """
        【干什么】解析回调内容。

        【Mock 版】假设 body 是 JSON，直接解析。
        """
        import json

        try:
            data = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            data = {}

        return {
            "order_no": data.get("order_no", ""),
            "trade_no": data.get("trade_no", ""),
            "amount": Decimal(str(data.get("amount", "0"))),
            "success": bool(data.get("success", True)),
            "raw": data,
        }
