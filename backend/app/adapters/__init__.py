# 外部系统适配器包
#
# 每个子包代表一类外部依赖：
#   payment/      支付网关
#   fulfillment/  履约系统

from app.adapters.fulfillment import get_fulfillment_adapter
from app.adapters.payment import get_payment_adapter

__all__ = ["get_payment_adapter", "get_fulfillment_adapter"]
