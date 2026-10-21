# ============================================================
# 【这个文件是干什么的】
# 履约适配器的工厂 —— 按配置返回对应的实现。
#
# 【怎么加真实履约方】
# 1. 新建 adapters/fulfillment/real.py，继承 FulfillmentAdapter
# 2. 在下面的 _ADAPTERS 加一行
# 3. .env 里设 FULFILLMENT_PROVIDER=real
# ============================================================

from functools import lru_cache

from app.adapters.fulfillment.base import FulfillmentAdapter, FulfillmentError
from app.adapters.fulfillment.mock import MockFulfillmentAdapter
from app.core.config import settings
from app.core.exceptions import BusinessError

_ADAPTERS: dict[str, type[FulfillmentAdapter]] = {
    "mock": MockFulfillmentAdapter,
    # "real": RealFulfillmentAdapter,   ← 接入真实履约系统时取消注释
}


@lru_cache
def get_fulfillment_adapter() -> FulfillmentAdapter:
    """
    【干什么】获取当前配置的履约适配器。

    【可能抛出】
        BusinessError：配置的履约方没有对应实现
    """
    provider = settings.FULFILLMENT_PROVIDER

    adapter_class = _ADAPTERS.get(provider)
    if adapter_class is None:
        raise BusinessError(
            f"未配置的履约方: {provider}",
            code="FULFILLMENT_PROVIDER_NOT_CONFIGURED",
            status_code=500,
        )

    return adapter_class()


__all__ = [
    "FulfillmentAdapter",
    "FulfillmentError",
    "MockFulfillmentAdapter",
    "get_fulfillment_adapter",
]
