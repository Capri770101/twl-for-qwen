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

    async def refund(
        self,
        order_no: str,
        amount,
        reason: str = "",
    ) -> dict:
        """
        【干什么】Mock 退款。

        【真实接入时要做什么】
        微信支付：调 /v3/refund/domestic/refunds
          - transaction_id 或 out_trade_no → order_no
          - amount.refund → amount（单位：分）
          - 返回 refund_id → 这里的 refund_no

        支付宝：调 alipay.trade.refund
          - out_trade_no → order_no
          - refund_amount → amount（单位：元）
          - 返回 trade_no → 这里的 refund_no

        【为什么 Mock 直接返回成功】
        退款流程的业务逻辑（校验、状态机、金额）和网关无关。
        Mock 模拟「网关返回成功」，让流程能跑通。
        """
        import time

        refund_no = f"MOCKREF{int(time.time() * 1000)}"

        logger.info(
            "mock_refund",
            order_no=order_no,
            amount=str(amount),
            reason=reason,
            refund_no=refund_no,
        )

        return {
            "success": True,
            "refund_no": refund_no,
            "amount": str(amount),
            "channel": "mock",
            "message": "Mock 退款成功",
        }
