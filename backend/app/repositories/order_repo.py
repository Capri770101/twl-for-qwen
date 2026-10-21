# ============================================================
# 【这个文件是干什么的】
# 订单的数据访问层。
#
# 【这一层的关键设计】
# 1. 查订单时用「行锁」防止并发冲突
# 2. 状态变化必须同时写日志
# 3. 一个订单的创建是一个事务（主表 + 明细 + 扣库存，要么全成功要么全失败）
# ============================================================

from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Order, OrderItem, OrderLog, OrderStatus
from app.repositories.base import BaseRepository
from app.schemas import OrderQuery


class OrderRepository(BaseRepository[Order]):
    """
    【干什么】订单的数据库操作。
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Order, db)

    # ────────────────────────────────────────────────────────
    # 查询
    # ────────────────────────────────────────────────────────

    async def get_by_order_no(
        self,
        order_no: str,
        *,
        with_items: bool = True,
        with_logs: bool = True,
        for_update: bool = False,
    ) -> Order | None:
        """
        【干什么】按订单号查订单。

        【参数】
            order_no:   订单号
            with_items: 是否带出商品明细
            with_logs:  是否带出状态日志
            for_update: 是否加行锁

        【for_update 是干什么的】
        加行锁 = 锁住这一行，其他事务不能改，直到当前事务结束。
        什么时候要用？
          - 改订单状态时（防止两个请求同时改）
          - 扣库存时

        什么时候不用？
          - 只是查询展示

        【为什么加锁很重要】
        场景：用户连点两次「取消订单」
          请求 A 读到状态 pending_payment
          请求 B 读到状态 pending_payment
          请求 A 改成 cancelled
          请求 B 也改成 cancelled  ← 日志写了两条，库存回加了两次

        加锁后，B 会等 A 结束，读到已取消状态，就不会重复处理。
        """
        stmt = select(Order).where(Order.order_no == order_no)

        if with_items:
            stmt = stmt.options(selectinload(Order.items))
        if with_logs:
            stmt = stmt.options(selectinload(Order.logs))
        if for_update:
            stmt = stmt.with_for_update()

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def build_list_stmt(self, query: OrderQuery) -> Select:
        """【干什么】根据筛选条件拼查询语句"""
        stmt = select(Order).options(selectinload(Order.items))

        if query.status:
            stmt = stmt.where(Order.status == query.status)
        if query.order_no:
            stmt = stmt.where(Order.order_no.ilike(f"%{query.order_no}%"))
        if query.phone:
            stmt = stmt.where(Order.phone == query.phone)

        # 最新的在前面
        stmt = stmt.order_by(Order.created_at.desc())
        return stmt

    async def list_orders(self, query: OrderQuery) -> list[Order]:
        """【干什么】查订单列表（分页）"""
        stmt = self.build_list_stmt(query)
        offset = (query.page - 1) * query.page_size
        stmt = stmt.offset(offset).limit(query.page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_orders(self, query: OrderQuery) -> int:
        """【干什么】数订单总数"""
        stmt = self.build_list_stmt(query)
        return await self.count(stmt)

    async def list_by_user(self, user_id: str, *, limit: int = 50) -> list[Order]:
        """【干什么】查某个用户的订单"""
        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ────────────────────────────────────────────────────────
    # 创建
    # ────────────────────────────────────────────────────────

    async def create_order_with_items(
        self,
        order: Order,
        items: list[OrderItem],
    ) -> Order:
        """
        【干什么】一次创建订单主表 + 所有明细。

        【为什么放在一个方法里】
        订单和明细必须同时存在。
        如果主表创建成功、明细失败，就是一脏数据。
        在一起插入，事务统一处理。
        """
        self.db.add(order)
        await self.db.flush()      # 先插入主表，拿到 ID

        # 把明细挂到订单上
        for item in items:
            item.order_id = order.id

        self.db.add_all(items)
        await self.db.flush()
        await self.db.refresh(order)

        return order

    # ────────────────────────────────────────────────────────
    # 状态与日志
    # ────────────────────────────────────────────────────────

    async def update_status(
        self,
        order: Order,
        to_status: str,
        *,
        reason: str = "",
        operator: str = "system",
    ) -> Order:
        """
        【干什么】改订单状态，同时记一条日志。

        【为什么状态和日志必须一起改】
        只改状态不记日志，出问题查不到。
        只记日志不改状态，数据不一致。
        两个必须原子操作。

        【注意】
        这个方法只负责「改」，不负责「判断能不能改」。
        能不能改（白名单校验）在 service 层做。
        """
        from_status = order.status

        # 改状态
        order.status = to_status
        await self.db.flush()

        # 记日志
        log = OrderLog(
            order_id=order.id,
            order_no=order.order_no,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            operator=operator,
        )
        self.db.add(log)
        await self.db.flush()

        return order

    async def add_log(
        self,
        order: Order,
        to_status: str,
        *,
        from_status: str | None = None,
        reason: str = "",
        operator: str = "system",
        extra: dict | None = None,
    ) -> OrderLog:
        """
        【干什么】只记日志，不改状态。

        【什么时候用】
        创建订单时：状态是 pending_payment，但"从什么状态"是空的。
        """
        log = OrderLog(
            order_id=order.id,
            order_no=order.order_no,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            operator=operator,
            extra=extra,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    # ────────────────────────────────────────────────────────
    # 超时处理
    # ────────────────────────────────────────────────────────

    async def find_expired_orders(self, now_str: str) -> list[Order]:
        """
        【干什么】找出超时未支付的订单。

        【什么时候用】
        定时任务调这个，把超时的订单取消掉，库存加回去。

        【当前状态】
        方法写好了，但定时任务还没接。
        周五之前可以先手动触发，或者上线后加 cron。
        """
        stmt = (
            select(Order)
            .where(Order.status == OrderStatus.PENDING_PAYMENT.value)
            .where(Order.expire_at.isnot(None))
            .where(Order.expire_at < now_str)
            .options(selectinload(Order.items))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ────────────────────────────────────────────────────────
    # 统计（后台看板用）
    # ────────────────────────────────────────────────────────

    async def get_stats(self) -> dict:
        """
        【干什么】统计后台看板需要的数字。
        """
        # 总订单数
        total = await self.db.execute(select(func.count(Order.id)))
        orders_total = total.scalar_one()

        # 已支付订单数
        paid = await self.db.execute(
            select(func.count(Order.id)).where(Order.paid_at.isnot(None))
        )
        orders_paid = paid.scalar_one()

        # 累计营收
        revenue = await self.db.execute(
            select(func.coalesce(func.sum(Order.pay_amount), 0)).where(
                Order.paid_at.isnot(None)
            )
        )
        total_revenue = revenue.scalar_one()

        # 今日订单数
        today = await self.db.execute(
            select(func.count(Order.id)).where(
                func.date(Order.created_at) == func.current_date()
            )
        )
        orders_today = today.scalar_one()

        # 各状态分布
        by_status = await self.db.execute(
            select(Order.status, func.count(Order.id)).group_by(Order.status)
        )
        status_dist = {row[0]: row[1] for row in by_status.all()}

        return {
            "orders_total": orders_total,
            "orders_paid": orders_paid,
            "orders_today": orders_today,
            "revenue": Decimal(total_revenue),
            "by_status": status_dist,
        }
