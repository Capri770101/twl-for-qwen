# ============================================================
# 【这个文件是干什么的】
# 售后工单的数据访问层。
# ============================================================

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Ticket
from app.repositories.base import BaseRepository


class TicketRepository(BaseRepository[Ticket]):
    """【干什么】售后工单的数据库操作"""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Ticket, db)

    async def get_by_ticket_no(self, ticket_no: str) -> Ticket | None:
        """【干什么】按工单号查"""
        stmt = select(Ticket).where(Ticket.ticket_no == ticket_no)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_order(self, order_no: str) -> list[Ticket]:
        """【干什么】查一个订单的所有工单（可能有多张）"""
        stmt = (
            select(Ticket)
            .where(Ticket.order_no == order_no)
            .order_by(Ticket.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def build_list_stmt(self, status: str | None = None) -> Select:
        """【干什么】拼列表查询语句"""
        stmt = select(Ticket)
        if status:
            stmt = stmt.where(Ticket.status == status)
        return stmt.order_by(Ticket.created_at.desc())

    async def list_tickets(
        self,
        status: str | None = None,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Ticket]:
        """【干什么】查工单列表"""
        stmt = self.build_list_stmt(status).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_open(self) -> int:
        """
        【干什么】数待处理的工单数（后台看板用）。

        【什么叫待处理】
        状态是 submitted（已提交）或 processing（处理中）。
        """
        from sqlalchemy import func

        stmt = (
            select(func.count(Ticket.id))
            .where(Ticket.status.in_(["submitted", "processing"]))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()
