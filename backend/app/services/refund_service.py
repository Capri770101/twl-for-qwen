# ============================================================
# 【这个文件是干什么的】
# 退款的业务逻辑。
#
# 【核心职责】
#   1. 校验能不能退（5 条规则）
#   2. 创建退款单
#   3. 审核（通过/拒绝）
#   4. 调支付网关退款
#   5. 失败重试
#
# 【和支付网关的关系】
# 业务逻辑完全不知道网关长什么样。
# 只调 adapter.refund()，拿到结果就记流水。
# 换网关只改 adapter，这个文件一行不改。
# ============================================================

import secrets
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.payment import get_payment_adapter
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.order import Order, OrderStatus
from app.models.payment import Payment
from app.models.refund import REFUND_STATUS_TEXT, Refund, RefundStatus
from app.schemas.refund import RefundCreate, RefundReview

logger = get_logger(__name__)


# ════════════════════════════════════════════════════════════
# 【可退款的订单状态】
# ════════════════════════════════════════════════════════════

REFUNDABLE_STATUS = {
    OrderStatus.PAID.value,
    OrderStatus.PREPARING.value,
    OrderStatus.DELIVERING.value,
    OrderStatus.DELIVERED.value,
    OrderStatus.COMPLETED.value,
}

# 退款时效：送达后多少天内可申请
REFUND_WINDOW_DAYS = 30


def _gen_refund_no() -> str:
    """生成退款单号：RF + 时间 + 4 位随机"""
    return "RF" + datetime.now().strftime("%Y%m%d%H%M%S") + secrets.token_hex(2).upper()


class RefundService:
    """退款服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ══════════════════════════════════════════════════════
    # 【申请退款】
    # ══════════════════════════════════════════════════════

    async def create_refund(
        self,
        data: RefundCreate,
        user_id: str | None = None,
    ) -> Refund:
        """
        【干什么】创建退款申请。

        【校验五条】
        1. 订单存在
        2. 订单状态可退
        3. 退款金额 ≤ 实付 − 已退
        4. 没有待处理的退款单
        5. 在退款时效内
        """
        # ── 1. 订单存在 ──
        result = await self.db.execute(
            select(Order).where(Order.order_no == data.order_no)
        )
        order = result.scalar_one_or_none()

        if not order:
            raise NotFoundError(f"订单 {data.order_no} 不存在")

        # ── 2. 状态可退 ──
        if order.status not in REFUNDABLE_STATUS:
            raise ConflictError(
                f"订单当前状态「{order.status}」不能退款"
            )

        # ── 3. 金额校验 ──
        refunded_total = await self._get_refunded_total(data.order_no)
        remaining = Decimal(str(order.pay_amount)) - refunded_total

        if remaining <= 0:
            raise ConflictError("这笔订单已经全额退款")

        if data.amount > remaining:
            raise ValidationError(
                f"退款金额 {data.amount} 超过可退金额 {remaining}"
            )

        # ── 4. 没有待处理的退款单 ──
        result = await self.db.execute(
            select(Refund).where(
                Refund.order_no == data.order_no,
                Refund.status.in_([RefundStatus.PENDING, RefundStatus.APPROVED]),
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise ConflictError(
                f"这笔订单有未处理的退款单（{existing.refund_no}）"
            )

        # ── 5. 退款时效 ──
        if order.status in (OrderStatus.DELIVERED.value, OrderStatus.COMPLETED.value):
            # 送达/完成时间从日志里找，找不到就用创建时间
            base_time = order.created_at
            if order.paid_at:
                try:
                    base_time = datetime.strptime(order.paid_at, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass

            if datetime.utcnow() - base_time > timedelta(days=REFUND_WINDOW_DAYS):
                raise ConflictError(f"超过 {REFUND_WINDOW_DAYS} 天退款时效")

        # ── 创建 ──
        refund = Refund(
            id="rfd" + secrets.token_hex(10),
            refund_no=_gen_refund_no(),
            order_no=data.order_no,
            ticket_no=data.ticket_no,
            user_id=user_id,
            amount=data.amount,
            order_amount=Decimal(str(order.pay_amount)),
            status=RefundStatus.PENDING,
            reason=data.reason,
            channel=order.pay_channel,
            is_demo=order.is_demo,
        )

        self.db.add(refund)
        await self.db.flush()

        logger.info(
            "refund_created",
            refund_no=refund.refund_no,
            order_no=data.order_no,
            amount=str(data.amount),
        )

        return refund

    # ============================================================
    # 【审核】
    # ============================================================

    async def review_refund(
        self,
        refund_no: str,
        review: RefundReview,
        operator: str,
    ) -> Refund:
        """
        【干什么】审核退款。

        【通过时做什么】
        1. 改状态为 approved
        2. 调支付网关退款
        3. 成功 → refunded，失败 → failed
        """
        result = await self.db.execute(
            select(Refund).where(Refund.refund_no == refund_no)
        )
        refund = result.scalar_one_or_none()

        if not refund:
            raise NotFoundError(f"退款单 {refund_no} 不存在")

        if refund.status != RefundStatus.PENDING:
            raise ConflictError(
                f"退款单状态是「{REFUND_STATUS_TEXT.get(refund.status, refund.status)}」，不能再审核"
            )

        # ── 拒绝 ──
        if not review.approve:
            if not review.reject_reason:
                raise ValidationError("拒绝时必须填理由")

            refund.status = RefundStatus.REJECTED
            refund.reject_reason = review.reject_reason
            refund.operator = operator
            refund.reviewed_at = datetime.utcnow()

            await self.db.flush()

            logger.info("refund_rejected", refund_no=refund_no, operator=operator)

            return refund

        # ── 通过 ──
        # 可以调整金额（比如只退部分）
        if review.adjusted_amount is not None:
            if review.adjusted_amount > refund.amount:
                raise ValidationError("调整后金额不能超过申请金额")
            refund.amount = review.adjusted_amount

        refund.status = RefundStatus.APPROVED
        refund.operator = operator
        refund.reviewed_at = datetime.utcnow()

        await self.db.flush()

        # ── 调网关退款 ──
        await self._execute_refund(refund)

        return refund

    # ============================================================
    # 【重试退款】
    # ============================================================

    async def retry_refund(self, refund_no: str) -> Refund:
        """退款失败后重试"""
        result = await self.db.execute(
            select(Refund).where(Refund.refund_no == refund_no)
        )
        refund = result.scalar_one_or_none()

        if not refund:
            raise NotFoundError(f"退款单 {refund_no} 不存在")

        if refund.status != RefundStatus.FAILED:
            raise ConflictError("只有失败的退款单能重试")

        refund.status = RefundStatus.APPROVED
        refund.error_message = None

        await self.db.flush()

        await self._execute_refund(refund)

        return refund

    # ============================================================
    # 【内部：调网关】
    # ============================================================

    async def _execute_refund(self, refund: Refund) -> None:
        """
        【干什么】调支付网关退款。

        【失败怎么办】
        不抛异常，把状态改成 failed，记录错误。
        这样后台能看到失败的退款单，手动重试。
        """
        adapter = get_payment_adapter()

        try:
            result = await adapter.refund(
                order_no=refund.order_no,
                amount=refund.amount,
                reason=refund.reason,
            )

            if result.get("success"):
                refund.status = RefundStatus.REFUNDED
                refund.external_ref = result.get("refund_no") or result.get("external_ref")
                refund.refunded_at = datetime.utcnow()
                refund.error_message = None

                logger.info(
                    "refund_success",
                    refund_no=refund.refund_no,
                    external_ref=refund.external_ref,
                )
            else:
                refund.status = RefundStatus.FAILED
                refund.error_message = result.get("message") or "网关返回失败"

                logger.warning(
                    "refund_failed",
                    refund_no=refund.refund_no,
                    error=refund.error_message,
                )

        except NotImplementedError:
            # 网关不支持退款
            refund.status = RefundStatus.FAILED
            refund.error_message = "当前支付渠道不支持退款"
            logger.error("refund_not_supported", refund_no=refund.refund_no)

        except Exception as e:
            refund.status = RefundStatus.FAILED
            refund.error_message = f"{type(e).__name__}: {e}"
            logger.exception("refund_exception", refund_no=refund.refund_no)

        await self.db.flush()

    # ============================================================
    # 【查询】
    # ============================================================

    async def _get_refunded_total(self, order_no: str) -> Decimal:
        """查这笔订单已退多少"""
        result = await self.db.execute(
            select(func.coalesce(func.sum(Refund.amount), 0)).where(
                Refund.order_no == order_no,
                Refund.status.in_([RefundStatus.APPROVED, RefundStatus.REFUNDED]),
            )
        )
        return Decimal(str(result.scalar() or 0))

    async def get_refund(self, refund_no: str) -> Refund:
        """查退款单"""
        result = await self.db.execute(
            select(Refund).where(Refund.refund_no == refund_no)
        )
        refund = result.scalar_one_or_none()

        if not refund:
            raise NotFoundError(f"退款单 {refund_no} 不存在")

        return refund

    async def list_refunds(
        self,
        status: str | None = None,
        order_no: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Refund], int]:
        """退款单列表"""
        stmt = select(Refund)

        if status:
            stmt = stmt.where(Refund.status == status)
        if order_no:
            stmt = stmt.where(Refund.order_no == order_no)

        # 总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # 分页
        stmt = stmt.order_by(Refund.applied_at.desc())
        stmt = stmt.offset((page - 1) * size).limit(size)

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return list(items), total

    async def get_order_refunds(self, order_no: str) -> list[Refund]:
        """查某笔订单的所有退款单"""
        result = await self.db.execute(
            select(Refund)
            .where(Refund.order_no == order_no)
            .order_by(Refund.applied_at.desc())
        )
        return list(result.scalars().all())
