# ============================================================
# 【这个文件是干什么的】
# 支付适配器的工厂 —— 根据配置返回对应的适配器。
#
# 【这就是「留接口」的实现】
# 业务代码只调 get_payment_adapter()，不关心具体是哪个渠道。
# 换渠道只改 .env 里的 PAYMENT_PROVIDER，代码一行不动。
#
# 【怎么加新渠道（比如银联）】
# 1. 新建 adapters/payment/unionpay.py，继承 PaymentAdapter
# 2. 在下面的 _ADAPTERS 字典里加一行
# 3. .env 里设 PAYMENT_PROVIDER=unionpay
# 完成，业务代码不用改。
# ============================================================

from functools import lru_cache

from app.adapters.payment.base import PaymentAdapter
from app.adapters.payment.mock import MockPaymentAdapter
from app.core.config import settings
from app.core.exceptions import BusinessError

# 【渠道注册表】新增渠道往这里加
_ADAPTERS: dict[str, type[PaymentAdapter]] = {
    "mock": MockPaymentAdapter,
    # "wechat": WechatPaymentAdapter,    ← 接入微信支付时取消注释
    # "alipay": AlipayPaymentAdapter,    ← 接入支付宝时取消注释
}


@lru_cache
def get_payment_adapter() -> PaymentAdapter:
    """
    【干什么】获取当前配置的支付适配器。

    【返回】
        一个 PaymentAdapter 实例（单例，缓存了）

    【配置从哪来】
        .env 里的 PAYMENT_PROVIDER

    【可能抛出】
        BusinessError：配置的渠道没有对应的适配器
    """
    provider = settings.PAYMENT_PROVIDER

    adapter_class = _ADAPTERS.get(provider)
    if adapter_class is None:
        raise BusinessError(
            f"未配置的支付渠道: {provider}",
            code="PAYMENT_PROVIDER_NOT_CONFIGURED",
            status_code=500,
        )

    return adapter_class()


def register_adapter(name: str, adapter_class: type[PaymentAdapter]) -> None:
    """
    【干什么】运行时注册新适配器。

    【什么时候用】
    插件化场景：某个渠道的实现作为独立包提供，
    不想改这个文件的话，可以在启动时动态注册。
    """
    _ADAPTERS[name] = adapter_class
    get_payment_adapter.cache_clear()   # 清缓存，让新注册的生效


__all__ = [
    "PaymentAdapter",
    "MockPaymentAdapter",
    "get_payment_adapter",
    "register_adapter",
]
