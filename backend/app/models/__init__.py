# ============================================================
# 【这个文件是干什么的】
# 把所有 ORM 模型统一导出。
#
# 【为什么必须这样导】
# Alembic（数据库迁移工具）需要知道所有模型才能生成迁移文件。
# 如果某个模型没被导入，Alembic 就看不到它，迁移时会漏掉那张表。
#
# 【怎么用】
#   from app.models import Product, Order, OrderItem
# ============================================================

from app.models.content import Article, Setting
from app.models.order import (
    STATUS_TEXT,
    Order,
    OrderItem,
    OrderLog,
    OrderStatus,
)
from app.models.payment import (
    Delivery,
    DeliveryStatus,
    PayChannel,
    Payment,
    PaymentStatus,
)
from app.models.product import (
    Product,
    ProductCategory,
    ProductStatus,
)
from app.models.ticket import (
    Ticket,
    TicketStatus,
    TicketType,
)
from app.models.user import Address, User

# 【重要】新增模型时，一定要加到这里来
__all__ = [
    # 商品
    "Product",
    "ProductCategory",
    "ProductStatus",
    # 订单
    "Order",
    "OrderItem",
    "OrderLog",
    "OrderStatus",
    "STATUS_TEXT",
    # 支付
    "Payment",
    "PaymentStatus",
    "PayChannel",
    # 配送
    "Delivery",
    "DeliveryStatus",
    # 售后
    "Ticket",
    "TicketStatus",
    "TicketType",
    # 用户
    "User",
    "Address",
    # 内容
    "Article",
    "Setting",
]

# 退款单
from app.models.refund import (  # noqa: E402
    REFUND_STATUS_TEXT,
    Refund,
    RefundStatus,
)
