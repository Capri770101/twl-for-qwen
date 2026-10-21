# ============================================================
# 【这个文件是干什么的】
# 统一导出所有数据访问层（Repository）。
#
# 【怎么用】
#   from app.repositories import ProductRepository, OrderRepository
# ============================================================

from app.repositories.base import BaseRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.payment_repo import DeliveryRepository, PaymentRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.ticket_repo import TicketRepository

__all__ = [
    "BaseRepository",
    "ProductRepository",
    "OrderRepository",
    "PaymentRepository",
    "DeliveryRepository",
    "TicketRepository",
]
