# ============================================================
# 【这个文件是干什么的】
# 支付的业务逻辑：发起支付、处理回调、幂等保证。
#
# 【这个文件最关键的三个概念】
# 1. 幂等 —— 同一个回调重复来多少次，结果都一样
# 2. 状态锁 —— 改订单状态时要加行锁，防止并发
# 3. 事务 —— 支付记录和订单状态必须一起改
# ============================================================

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.payment import get_payment_adapter
from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    PaymentError,
)
from app.core.logging import get_logger
from app.models import OrderStatus, PaymentStatus
from app.repositories import OrderRepository, PaymentRepository
from app.schemas import (
    PaymentCallbackResult,
    PaymentCreate,
    PaymentCreateResult,
)

logger = get_logger(__name__)


class PaymentService:
    """【干什么】支付的全部业务逻辑"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.order_repo = OrderRepository(db)
        self.adapter = get_payment_adapter()

    # ────────────────────────────────────────────────────────
    # 发起支付
    # ────────────────────────────────────────────────────────

    async def create_payment(self, data: PaymentCreate) -> PaymentCreateResult:
        """
        【干什么】发起一次支付。

        【做了什么】
            1. 检查订单存在且是「待支付」状态
            2. 检查是不是已经超时了
            3. 创建一条支付记录（pending）
            4. 调支付网关拿支付参数

        【可能抛出】
            NotFoundError  订单不存在
            ConflictError  订单状态不对（已付过/已取消）
            PaymentError   订单已超时
        """
        from app.models import Payment

        order = await self.order_repo.get_by_order_no(
            data.order_no,
            with_items=False,
            with_logs=False,
        )

        if order is None:
            raise NotFoundError("订单不存在")

        # 只有待支付的订单才能发起支付
        if order.status != OrderStatus.PENDING_PAYMENT:
            raise ConflictError(
                f"订单当前状态是「{order.status}」，不能支付",
                detail={"status": order.status},
            )

        # 检查超时
        if order.expire_at and order.expire_at < datetime.now().strftime("%Y-%m-%d %H:%M:%S"):
            raise PaymentError("订单已超时，请重新下单")

        # 创建支付记录
        payment = Payment(
            id="p" + uuid.uuid4().hex,
            order_id=order.id,
            order_no=order.order_no,
            channel=data.channel,
            amount=order.pay_amount,
            status=PaymentStatus.PENDING.value,
        )
        await self.payment_repo.create(payment)

        # 调支付网关（Mock 或真实）
        gateway_result = await self.adapter.create_payment(
            order_no=order.order_no,
            amount=order.pay_amount,
            channel=data.channel,
        )

        logger.info(
            "发起支付",
            order_no=order.order_no,
            channel=data.channel,
            amount=str(order.pay_amount),
        )

        return PaymentCreateResult(
            payment_id=payment.id,
            order_no=order.order_no,
            channel=data.channel,
            amount=order.pay_amount,
            **gateway_result,
        )

    # ────────────────────────────────────────────────────────
    # 处理回调（核心）
    # ────────────────────────────────────────────────────────

    async def handle_callback(
        self,
        order_no: str,
        *,
        channel: str,
        trade_no: str,
        amount: Decimal,
        success: bool,
        raw: dict | None = None,
    ) -> PaymentCallbackResult:
        """
        【干什么】处理支付结果（幂等）。

        【为什么必须幂等】
        微信/支付宝的回调会重复发好几次（网络超时会重试）。
        如果不做幂等：
            第一次回调 → 订单变「已支付」✅
            第二次回调 → 又处理一遍 → 库存又扣一次 ❌

        【怎么做的】
        先查订单。如果已经不是「待支付」了，说明处理过了，直接返回。

        【为什么加行锁】
        防止两个回调同时进来，都读到「待支付」，都去处理。
        加锁后，第二个会等第一个结束，读到「已支付」，直接返回。

        【参数】
            order_no: 订单号
            channel:  支付渠道
            trade_no: 第三方交易号
            amount:   支付金额
            success:  是否成功
            raw:      原始回调内容（存起来备查）

        【返回】
            PaymentCallbackResult，含 idempotent 标记
        """
        # ── 查订单（加行锁，防止并发）──
        order = await self.order_repo.get_by_order_no(
            order_no,
            with_items=False,
            with_logs=False,
            for_update=True,        # ← 关键：加行锁
        )

        if order is None:
            raise NotFoundError("订单不存在")

        # ── 幂等检查：已经处理过了就直接返回 ──
        if order.status != OrderStatus.PENDING_PAYMENT:
            logger.info(
                "重复回调，跳过处理",
                order_no=order_no,
                current_status=order.status,
            )
            return PaymentCallbackResult(
                order_no=order_no,
                status=order.status,
                idempotent=True,
            )

        # ── 校验金额 ──
        if success and amount != order.pay_amount:
            logger.error(
                "回调金额与订单金额不符",
                order_no=order_no,
                callback_amount=str(amount),
                order_amount=str(order.pay_amount),
            )
            raise PaymentError(
                f"金额不符：回调 {amount}，订单 {order.pay_amount}",
            )

        # ── 更新支付记录 ──
        payment = await self.payment_repo.get_pending(order_no)
        if payment:
            await self.payment_repo.update(
                payment,
                status=PaymentStatus.SUCCESS.value if success else PaymentStatus.FAILED.value,
                trade_no=trade_no,
                raw_callback=raw,
                paid_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S") if success else None,
            )

        # ── 成功才改订单状态 ──
        if success:
            await self.order_repo.update_status(
                order,
                OrderStatus.PAID.value,
                reason=f"{channel} 支付成功",
                operator="payment",
            )
            # 补充支付信息
            await self.order_repo.update(
                order,
                pay_channel=channel,
                paid_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

            logger.info(
                "支付成功，订单状态已更新",
                order_no=order_no,
                channel=channel,
                trade_no=trade_no,
            )

        return PaymentCallbackResult(
            order_no=order_no,
            status=OrderStatus.PAID.value if success else OrderStatus.PENDING_PAYMENT.value,
            idempotent=False,
        )
