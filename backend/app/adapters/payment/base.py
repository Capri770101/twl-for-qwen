# ============================================================
# 【这个文件是干什么的】
# 支付网关的抽象接口 —— 定义「支付网关应该能做什么」。
#
# 【什么是端口-适配器架构】
# 打个比方：插座（端口）和插头（适配器）。
#   - 端口 = 定义形状（这里有 create_payment、verify_callback 等方法）
#   - 适配器 = 具体实现（Mock 版、微信版、支付宝版）
#
# 好处：
#   业务代码只依赖「端口」，不关心「插头」是谁。
#   换支付渠道 = 加一个新的适配器，业务代码一行不改。
#
# 【怎么用】
#   adapter = get_payment_adapter()      # 拿当前配置的适配器
#   result = await adapter.create_payment(...)
# ============================================================

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any


class PaymentAdapter(ABC):
    """
    【干什么】支付网关的抽象基类。

    【子类必须实现这三个方法】
        create_payment   —— 发起支付
        verify_callback  —— 验证回调真伪
        parse_callback   —— 解析回调内容

    【为什么 verify_callback 和 parse_callback 分开】
    验证签名要拿到原始数据（原始 body、header），
    解析要拿到业务字段。
    两步分开，职责更清晰。
    """

    @abstractmethod
    async def create_payment(
        self,
        order_no: str,
        amount: Decimal,
        channel: str,
    ) -> dict[str, Any]:
        """
        【干什么】向支付网关发起一笔支付。

        【参数】
            order_no: 订单号
            amount:   金额（元）
            channel:  渠道（wechat / alipay）

        【返回】
            一个字典，包含前端调起支付需要的参数。
            Mock：  {"mock_pay_url": "/api/v1/payments/mock/pay?order_no=xxx"}
            微信：  {"prepay_id": "...", "pay_sign": "...", "timestamp": "...", "nonce_str": "..."}
            支付宝：{"pay_url": "https://..."}

        【可能抛出】
            PaymentError：网关报错
        """
        ...

    @abstractmethod
    async def verify_callback(
        self,
        headers: dict[str, str],
        body: bytes,
    ) -> bool:
        """
        【干什么】验证回调是不是真的来自支付网关。

        【为什么必须做】
        不验签的话，任何人都能伪造一个「支付成功」的请求，
        白拿花不给钱。

        【怎么验】
        微信：用 API 密钥算 HMAC-SHA256 签名，和回调里的签名比对
        支付宝：用支付宝公钥验证 RSA2 签名

        【参数】
            headers: 请求头（微信签名在 header 里）
            body:    原始请求体（字节，不能先解析）

        【返回】
            True = 签名有效
            False = 签名无效（要拒绝这个请求）
        """
        ...

    @abstractmethod
    async def parse_callback(
        self,
        body: bytes,
    ) -> dict[str, Any]:
        """
        【干什么】把回调的原始数据解析成统一格式。

        【返回格式】
        {
            "order_no": "TWL123",
            "trade_no": "微信的交易号",
            "amount": Decimal("299.00"),
            "success": True,
            "raw": {...}          # 原始内容，存起来备查
        }
        """
        ...

    # ────────────────────────────────────────────────────────
    # 可选方法：有默认实现，子类可以不覆盖
    # ────────────────────────────────────────────────────────

    async def query_payment(self, order_no: str) -> dict[str, Any] | None:
        """
        【干什么】主动查询支付结果。

        【什么时候用】
        回调丢了，或者用户说付了钱但系统没收到。
        主动去网关查一下真实状态。

        【默认返回 None】表示这个渠道不支持主动查询。
        """
        return None

    async def refund(
        self,
        order_no: str,
        amount: Decimal,
        reason: str = "",
    ) -> dict[str, Any]:
        """
        【干什么】发起退款。

        【默认实现】抛异常，表示不支持。
        真实网关要覆盖这个方法。
        """
        raise NotImplementedError("这个支付渠道不支持退款")
