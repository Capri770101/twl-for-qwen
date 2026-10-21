# ============================================================
# 【这个文件是干什么的】
# 售后工单和履约推送的业务逻辑。
# ============================================================

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.fulfillment import FulfillmentError, get_fulfillment_adapter
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models import Delivery, DeliveryStatus, OrderStatus, Ticket, TicketStatus
from app.repositories import DeliveryRepository, OrderRepository, TicketRepository
from app.schemas import (
    DeliveryNotifyResult,
    TicketCreate,
    TicketCreateResult,
    TicketReply,
)

logger = get_logger(__name__)


class TicketService:
    """【干什么】售后工单的业务逻辑"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = TicketRepository(db)
        self.order_repo = OrderRepository(db)

    @staticmethod
    def generate_ticket_no() -> str:
        """【干什么】生成工单号：TK + 时间 + 3位随机"""
        return (
            "TK"
            + datetime.now().strftime("%Y%m%d%H%M%S")
            + uuid.uuid4().hex[:3].upper()
        )

    async def create_ticket(self, data: TicketCreate) -> TicketCreateResult:
        """
        【干什么】提交售后申请。

        【做了什么】
            1. 检查订单存在
            2. 检查这个订单是不是已经有一张在处理中的工单（防止重复提交）
            3. 生成工单号，写库
            4. 返回工单号和预计响应时间

        【可能抛出】
            NotFoundError  订单不存在
            ConflictError  已有处理中的工单
        """
        order = await self.order_repo.get_by_order_no(
            data.order_no,
            with_items=False,
            with_logs=False,
        )
        if order is None:
            raise NotFoundError("订单不存在")

        # 防止重复提交：同一个订单不能有两张未处理的工单
        existing = await self.repo.list_by_order(data.order_no)
        for t in existing:
            if t.status in (TicketStatus.SUBMITTED.value, TicketStatus.PROCESSING.value):
                raise ConflictError(
                    "这个订单已有处理中的工单",
                    detail={"ticket_no": t.ticket_no},
                )

        ticket_no = self.generate_ticket_no()

        ticket = Ticket(
            id="t" + uuid.uuid4().hex,
            ticket_no=ticket_no,
            order_id=order.id,
            order_no=data.order_no,
            type=data.type,
            reason=data.reason,
            images=data.images,
            status=TicketStatus.SUBMITTED.value,
            contact_phone=data.contact_phone or order.phone,
        )
        await self.repo.create(ticket)

        logger.info(
            "售后工单已创建",
            ticket_no=ticket_no,
            order_no=data.order_no,
            type=data.type,
        )

        return TicketCreateResult(
            ticket_no=ticket_no,
            status=TicketStatus.SUBMITTED.value,
            message="售后申请已提交，客服将在 2 小时内联系你",
            expected_response_time="2 小时",
        )

    async def get_ticket(self, ticket_no: str) -> Ticket:
        """【干什么】查工单。可能抛出 NotFoundError"""
        ticket = await self.repo.get_by_ticket_no(ticket_no)
        if ticket is None:
            raise NotFoundError("工单不存在")
        return ticket

    async def reply_ticket(self, ticket_no: str, data: TicketReply) -> Ticket:
        """
        【干什么】客服回复工单。

        【做了什么】
            1. 查工单
            2. 更新回复内容、处理方案、状态
            3. 如果是 resolved，记录解决时间
        """
        ticket = await self.get_ticket(ticket_no)

        update_fields = {
            "reply": data.reply,
            "status": data.status,
            "solution": data.solution,
        }

        if data.status == TicketStatus.RESOLVED.value:
            update_fields["resolved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        await self.repo.update(ticket, **update_fields)

        logger.info(
            "工单已回复",
            ticket_no=ticket_no,
            status=data.status,
            solution=data.solution,
        )

        return ticket


class DeliveryService:
    """【干什么】履约推送的业务逻辑"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.order_repo = OrderRepository(db)
        self.delivery_repo = DeliveryRepository(db)
        self.adapter = get_fulfillment_adapter()

    async def notify_fulfillment(self, order_no: str) -> DeliveryNotifyResult:
        """
        【干什么】把已支付的订单推给履约方。

        【做了什么】
            1. 检查订单存在且是「已支付」
            2. 组装推送内容
            3. 调适配器推送
            4. 记一条配送单
            5. 订单状态改成「配花中」
            6. 记日志

        【可能抛出】
            NotFoundError   订单不存在
            ConflictError   订单状态不是已支付
            ValidationError 推送失败
        """
        order = await self.order_repo.get_by_order_no(
            order_no,
            with_items=True,
            with_logs=False,
        )
        if order is None:
            raise NotFoundError("订单不存在")

        if order.status != OrderStatus.PAID:
            raise ConflictError(
                f"订单状态是「{order.status}」，只有「已支付」才能推送履约",
                detail={"status": order.status},
            )

        # ── 组装推送内容 ──
        payload = {
            "order_no": order.order_no,
            "receiver": order.receiver,
            "phone": order.phone,
            "address": "".join(filter(None, [
                order.province, order.city, order.district, order.address_detail,
            ])),
            "delivery_date": order.delivery_date,
            "delivery_slot": order.delivery_slot,
            "card_message": order.card_message,
            "anonymous": order.anonymous,
            "remark": order.remark,
            "items": [
                {
                    "product_id": item.product_id,
                    "name": item.product_name,
                    "qty": item.qty,
                }
                for item in order.items
            ],
        }

        # ── 创建配送单记录 ──
        delivery = Delivery(
            id="d" + uuid.uuid4().hex,
            order_id=order.id,
            order_no=order.order_no,
            provider="mock" if self.adapter.__class__.__name__.startswith("Mock") else "real",
            status=DeliveryStatus.PENDING.value,
            payload=payload,
        )
        await self.delivery_repo.create(delivery)

        # ── 调适配器推送 ──
        try:
            result = await self.adapter.push_order(payload)
        except FulfillmentError as exc:
            # 推送失败：记录错误，不改订单状态
            await self.delivery_repo.update(
                delivery,
                status=DeliveryStatus.FAILED.value,
                error_message=exc.message,
            )
            logger.error(
                "履约推送失败",
                order_no=order_no,
                error=exc.message,
            )
            raise ValidationError(f"推送履约失败: {exc.message}") from exc

        # ── 推送成功：更新配送单 + 订单状态 ──
        await self.delivery_repo.update(
            delivery,
            status=DeliveryStatus.SENT.value,
            external_ref=result.get("external_ref"),
            response=result,
            sent_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        await self.order_repo.update_status(
            order,
            OrderStatus.PREPARING.value,
            reason="已推送履约方",
            operator="delivery",
        )

        logger.info(
            "订单已推送履约方",
            order_no=order_no,
            external_ref=result.get("external_ref"),
        )

        return DeliveryNotifyResult(
            delivery_id=delivery.id,
            order_no=order_no,
            status=DeliveryStatus.SENT.value,
            provider=delivery.provider,
            external_ref=result.get("external_ref"),
            message=result.get("message", ""),
        )

    async def handle_callback(self, order_no: str, status: str) -> None:
        """
        【干什么】处理履约方的状态回调。

        【参数】
            order_no: 订单号
            status:   delivering（出发了）/ delivered（送到了）

        【做了什么】
            1. 校验状态合法性
            2. 改订单状态
            3. 改配送单状态
            4. 记日志
        """
        if status not in ("delivering", "delivered"):
            raise ValidationError("status 只能是 delivering 或 delivered")

        order = await self.order_repo.get_by_order_no(
            order_no,
            with_items=False,
            with_logs=False,
        )
        if order is None:
            raise NotFoundError("订单不存在")

        # 用状态机校验，确保不会跳步（复用 OrderService 的白名单校验）
        from app.services.order_service import OrderService

        order_service = OrderService(self.db)
        await order_service.transition_status(
            order_no,
            status,
            reason="履约方回调",
            operator="delivery",
        )

        # 同步更新配送单状态
        delivery = await self.delivery_repo.get_latest_by_order(order_no)
        if delivery:
            await self.delivery_repo.update(
                delivery,
                status=status,
            )

        logger.info(
            "履约状态已更新",
            order_no=order_no,
            status=status,
        )
