# ============================================================
# 【这个文件是干什么的】
# 支付记录和配送单的数据访问层。
# ============================================================

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Delivery, Payment, PaymentStatus
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """【干什么】支付记录的数据库操作"""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Payment, db)

    async def list_by_order(self, order_no: str) -> list[Payment]:
        """【干什么】查一个订单的所有支付尝试（最新的在前）"""
        stmt = (
            select(Payment)
            .where(Payment.order_no == order_no)
            .order_by(Payment.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_pending(self, order_no: str) -> Payment | None:
        """
        【干什么】查这个订单当前有没有「待支付」的记录。

        【什么时候用】
        用户再次点「去支付」时，如果有未完成的支付单，可以复用。
        """
        stmt = (
            select(Payment)
            .where(Payment.order_no == order_no)
            .where(Payment.status == PaymentStatus.PENDING.value)
            .order_by(Payment.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_trade_no(self, trade_no: str) -> Payment | None:
        """
        【干什么】按第三方交易号查支付记录。

        【什么时候用】
        收到回调时，可以通过交易号反查是哪一笔支付。
        """
        stmt = select(Payment).where(Payment.trade_no == trade_no).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


class DeliveryRepository(BaseRepository[Delivery]):
    """【干什么】配送单的数据库操作"""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Delivery, db)

    async def get_latest_by_order(self, order_no: str) -> Delivery | None:
        """【干什么】查一个订单最近一次推送记录"""
        stmt = (
            select(Delivery)
            .where(Delivery.order_no == order_no)
            .order_by(Delivery.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
