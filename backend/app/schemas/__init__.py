# ============================================================
# 【这个文件是干什么的】
# 统一导出所有 Pydantic 模型，方便导入。
#
# 【怎么用】
#   from app.schemas import ProductOut, OrderCreate, ApiResponse
# ============================================================

from app.schemas.common import (
    ApiResponse,
    BaseSchema,
    PaginatedData,
)
from app.schemas.order import (
    AmountDetail,
    OrderBrief,
    OrderCreate,
    OrderCreateResult,
    OrderItemIn,
    OrderItemOut,
    OrderOut,
    OrderQuery,
    ReceiverInfo,
    TimelineItem,
)
from app.schemas.payment import (
    PaymentCallback,
    PaymentCallbackResult,
    PaymentCreate,
    PaymentCreateResult,
    PaymentOut,
)
from app.schemas.product import (
    DeliveryAvailability,
    DeliverySlot,
    ProductBrief,
    ProductCreate,
    ProductOut,
    ProductQuery,
    ProductUpdate,
)
from app.schemas.ticket import (
    DeliveryNotifyResult,
    TicketBrief,
    TicketCreate,
    TicketCreateResult,
    TicketOut,
    TicketReply,
)

__all__ = [
    # 通用
    "ApiResponse",
    "BaseSchema",
    "PaginatedData",
    # 商品
    "ProductCreate",
    "ProductUpdate",
    "ProductOut",
    "ProductBrief",
    "ProductQuery",
    "DeliveryAvailability",
    "DeliverySlot",
    # 订单
    "OrderCreate",
    "OrderCreateResult",
    "OrderOut",
    "OrderBrief",
    "OrderQuery",
    "OrderItemIn",
    "OrderItemOut",
    "ReceiverInfo",
    "AmountDetail",
    "TimelineItem",
    # 支付
    "PaymentCreate",
    "PaymentCreateResult",
    "PaymentCallback",
    "PaymentCallbackResult",
    "PaymentOut",
    # 售后
    "TicketCreate",
    "TicketCreateResult",
    "TicketOut",
    "TicketBrief",
    "TicketReply",
    "DeliveryNotifyResult",
]
