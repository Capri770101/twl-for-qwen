# ============================================================
# 【这个文件是干什么的】
# 统一导出所有业务层（Service）。
#
# 【怎么用】
#   from app.services import OrderService, PaymentService
# ============================================================

from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
from app.services.product_service import ProductService
from app.services.ticket_service import DeliveryService, TicketService

from app.services import address_service, auth_service

__all__ = [
    "ProductService",
    "OrderService",
    "PaymentService",
    "TicketService",
    "DeliveryService",
    "auth_service",
    "address_service",
]
