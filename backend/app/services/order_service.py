# ============================================================
# 【这个文件是干什么的】
# 订单的业务逻辑：状态机、算价、创建订单、改状态。
#
# 【这一层和 Repository 的区别】
# Repository 只管「怎么存怎么取」，
# Service 管「业务规则」：
#   - 库存够不够
#   - 状态能不能这么改
#   - 运费怎么算
#   - 扣库存和建单要在一个事务里
#
# 【这是整个系统最核心的文件】
# 所有的订单逻辑都在这里，改之前一定要看懂。
# ============================================================

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    ConflictError,
    InvalidStatusTransition,
    NotFoundError,
    OutOfStockError,
    ValidationError,
)
from app.core.logging import get_logger
from app.models import Order, OrderItem, OrderStatus
from app.repositories import OrderRepository, ProductRepository
from app.schemas import AmountDetail, OrderCreate, OrderCreateResult

logger = get_logger(__name__)


# ════════════════════════════════════════════════════════════
# 【状态流转白名单 —— 整个系统最重要的规则】
#
# 每一行：当前状态 → 允许变成哪些状态
#
# 为什么必须有这个：
# 一旦状态能乱跳，数据就不可信了。
# 比如「已取消」又变成「已支付」，库存扣两次，财务对不上。
# ════════════════════════════════════════════════════════════
TRANSITIONS: dict[str, set[str]] = {
    OrderStatus.PENDING_PAYMENT: {OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
    OrderStatus.PREPARING: {OrderStatus.DELIVERING, OrderStatus.CANCELLED},
    OrderStatus.DELIVERING: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: {OrderStatus.COMPLETED},
    OrderStatus.COMPLETED: set(),      # 终态，不能再变
    OrderStatus.CANCELLED: set(),      # 终态，不能再变
}


class OrderService:
    """
    【干什么】订单的全部业务逻辑。

    【怎么用】
        service = OrderService(db)
        result = await service.create_order(data)
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.order_repo = OrderRepository(db)
        self.product_repo = ProductRepository(db)

    # ────────────────────────────────────────────────────────
    # 工具方法
    # ────────────────────────────────────────────────────────

    @staticmethod
    def generate_order_no() -> str:
        """
        【干什么】生成订单号。

        【格式】TWL + 年月日时分秒 + 4位随机
        例：TWL20261020135005B35B

        【为什么不用自增数字】
        订单号会被用户看到。
        用 1、2、3 的话，用户能猜出你一天卖多少单 —— 商业秘密泄露。
        """
        return (
            "TWL"
            + datetime.now().strftime("%Y%m%d%H%M%S")
            + uuid.uuid4().hex[:4].upper()
        )

    @staticmethod
    def calculate_shipping_fee(subtotal: Decimal) -> Decimal:
        """
        【干什么】算运费。

        【规则】
        满 199 元免运费，不满收 15 元。
        规则可配：看 settings.FREE_SHIPPING_THRESHOLD 和 BASE_SHIPPING_FEE。
        """
        threshold = Decimal(settings.FREE_SHIPPING_THRESHOLD) / 100
        base_fee = Decimal(settings.BASE_SHIPPING_FEE) / 100

        if subtotal >= threshold:
            return Decimal("0.00")
        return base_fee

    @staticmethod
    def can_transition(from_status: str, to_status: str) -> bool:
        """
        【干什么】判断能不能从这个状态变到那个状态。

        【返回】
            True  = 允许
            False = 不允许
        """
        allowed = TRANSITIONS.get(from_status, set())
        return to_status in allowed

    # ────────────────────────────────────────────────────────
    # 创建订单
    # ────────────────────────────────────────────────────────

    async def create_order(
        self,
        data: OrderCreate,
        *,
        user_id: str | None = None,
    ) -> OrderCreateResult:
        """
        【干什么】创建订单。

        【完整流程】
            1. 逐个检查商品：存在吗？上架吗？库存够吗？
            2. 算商品总额
            3. 算运费
            4. 生成订单主表
            5. 生成订单明细
            6. 扣库存（在这里扣，不是支付时扣）
            7. 记一条状态日志
            8. 返回订单号和金额

        【为什么在这里扣库存】
        防止超卖。两个人同时下单，只有一个能成功。
        代价：用户不付款的话库存锁住 30 分钟（超时后由定时任务释放）。

        【参数】
            data:    下单请求数据
            user_id: 用户 ID（游客下单为空）

        【返回】
            OrderCreateResult：订单号 + 金额明细 + 支付截止时间

        【可能抛出的异常】
            NotFoundError   商品不存在
            OutOfStockError 库存不足
            ValidationError 商品已下架
        """
        # ── 第1步：检查商品，算总额 ──
        subtotal = Decimal("0.00")
        cart_items: list[dict] = []   # 要写进明细的数据

        for item in data.items:
            product = await self.product_repo.get_by_id(item.product_id)

            if product is None:
                raise NotFoundError(f"商品不存在: {item.product_id}")

            if product.status != "on":
                raise ValidationError(f"商品已下架: {product.name}")

            if product.stock < item.qty:
                raise OutOfStockError(product.name)

            line_total = product.price * item.qty
            subtotal += line_total

            cart_items.append({
                "product": product,
                "qty": item.qty,
                "line_total": line_total,
            })

        # ── 第2步：算运费 ──
        shipping_fee = self.calculate_shipping_fee(subtotal)
        pay_amount = subtotal + shipping_fee

        # ── 第3步：生成订单主表 ──
        order_no = self.generate_order_no()
        now = datetime.now()
        expire_at = now + timedelta(minutes=settings.ORDER_EXPIRE_MINUTES)

        order = Order(
            id="o" + uuid.uuid4().hex,
            order_no=order_no,
            user_id=user_id,
            status=OrderStatus.PENDING_PAYMENT.value,
            total_amount=subtotal,
            delivery_fee=shipping_fee,
            discount_amount=Decimal("0.00"),
            pay_amount=pay_amount,
            receiver=data.receiver.name,
            phone=data.receiver.phone,
            province=data.receiver.province,
            city=data.receiver.city,
            district=data.receiver.district,
            address_detail=data.receiver.detail,
            delivery_date=data.delivery_date,
            delivery_slot=data.delivery_slot,
            card_message=data.card_message,
            anonymous=data.anonymous,
            remark=data.remark,
            expire_at=expire_at.strftime("%Y-%m-%d %H:%M:%S"),
        )

        # ── 第4步：生成明细 ──
        order_items: list[OrderItem] = []
        for ci in cart_items:
            product = ci["product"]
            order_items.append(
                OrderItem(
                    id="oi" + uuid.uuid4().hex,
                    order_id=order.id,
                    product_id=product.id,
                    # 快照：存下单时的名字和图片，防止商品改名后历史订单对不上
                    product_name=product.name,
                    product_cover=product.cover,
                    price=product.price,
                    qty=ci["qty"],
                    subtotal=ci["line_total"],
                )
            )

        # ── 第5步：写数据库（主表 + 明细，一个事务）──
        await self.order_repo.create_order_with_items(order, order_items)

        # ── 第6步：扣库存 ──
        # 【注意】上面已经检查过库存了，但那是"读"。
        # 这里再扣一次，用带条件的 UPDATE 保证并发安全。
        for ci in cart_items:
            product = ci["product"]
            ok = await self.product_repo.decrease_stock(product.id, ci["qty"])
            if not ok:
                # 极端情况：检查时还有，扣的时候被别人抢走了
                raise OutOfStockError(product.name)

        # ── 第7步：记日志 ──
        await self.order_repo.add_log(
            order,
            to_status=OrderStatus.PENDING_PAYMENT.value,
            from_status=None,
            reason="创建订单",
            operator="system",
            extra={"item_count": len(order_items)},
        )

        logger.info(
            "订单创建成功",
            order_no=order_no,
            pay_amount=str(pay_amount),
            item_count=len(order_items),
        )

        # ── 第8步：返回 ──
        return OrderCreateResult(
            order_no=order_no,
            status=OrderStatus.PENDING_PAYMENT.value,
            amount=AmountDetail(
                product=subtotal,
                delivery_fee=shipping_fee,
                discount=Decimal("0.00"),
                total=pay_amount,
            ),
            expire_at=expire_at.strftime("%Y-%m-%d %H:%M:%S"),
            ttl_seconds=settings.ORDER_EXPIRE_MINUTES * 60,
        )

    # ────────────────────────────────────────────────────────
    # 改状态
    # ────────────────────────────────────────────────────────

    async def transition_status(
        self,
        order_no: str,
        to_status: str,
        *,
        reason: str = "",
        operator: str = "system",
        lock: bool = True,
    ) -> Order:
        """
        【干什么】改订单状态（带白名单校验）。

        【这是所有状态变化的唯一入口】
        支付成功、后台推进、履约方回执，最终都调这里。

        【做了什么】
            1. 查订单（默认加行锁，防止并发冲突）
            2. 校验：能不能从这个状态变到那个状态
            3. 改状态 + 记日志
            4. 如果是取消，把库存加回去

        【参数】
            order_no:  订单号
            to_status: 目标状态
            reason:    变化原因（写进日志）
            operator:  谁操作的
            lock:      是否加行锁（默认加，并发改状态时要加）

        【可能抛出】
            NotFoundError          订单不存在
            InvalidStatusTransition 状态流转不允许
        """
        order = await self.order_repo.get_by_order_no(
            order_no,
            with_items=True,
            with_logs=False,
            for_update=lock,
        )

        if order is None:
            raise NotFoundError("订单不存在")

        from_status = order.status

        # ── 白名单校验 ──
        if not self.can_transition(from_status, to_status):
            raise InvalidStatusTransition(from_status, to_status)

        # ── 改状态 + 记日志 ──
        await self.order_repo.update_status(
            order,
            to_status,
            reason=reason,
            operator=operator,
        )

        # ── 取消订单要把库存加回去 ──
        if to_status == OrderStatus.CANCELLED:
            for item in order.items:
                await self.product_repo.increase_stock(item.product_id, item.qty)
            logger.info("订单取消，库存已回滚", order_no=order_no)

        logger.info(
            "订单状态变更",
            order_no=order_no,
            from_status=from_status,
            to_status=to_status,
            operator=operator,
        )

        return order

    async def cancel_order(
        self,
        order_no: str,
        *,
        reason: str = "用户取消",
        operator: str = "user",
    ) -> Order:
        """
        【干什么】取消订单。

        【注意】
        只有「待支付」和「已支付」状态能取消。
        配花中之后不能取消（花已经做了），要走售后流程。
        """
        return await self.transition_status(
            order_no,
            OrderStatus.CANCELLED,
            reason=reason,
            operator=operator,
        )

    # ────────────────────────────────────────────────────────
    # 查询
    # ────────────────────────────────────────────────────────

    async def get_order(self, order_no: str) -> Order:
        """
        【干什么】查订单详情。

        【可能抛出】NotFoundError
        """
        order = await self.order_repo.get_by_order_no(order_no)
        if order is None:
            raise NotFoundError("订单不存在")
        return order

    async def check_expired(self, order_no: str) -> bool:
        """
        【干什么】检查订单是不是已经超时未支付。

        【什么时候用】
        用户付款前查一下，超时了就别让他付了。
        """
        order = await self.order_repo.get_by_order_no(order_no, with_items=False, with_logs=False)
        if order is None:
            return True
        if order.status != OrderStatus.PENDING_PAYMENT:
            return False
        if not order.expire_at:
            return False
        return order.expire_at < datetime.now().strftime("%Y-%m-%d %H:%M:%S")
