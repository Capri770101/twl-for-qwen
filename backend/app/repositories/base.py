# ============================================================
# 【这个文件是干什么的】
# 数据访问层的基类，封装通用的增删改查操作。
#
# 【数据访问层（Repository）是什么】
# 只负责「跟数据库打交道」，不包含任何业务判断。
# 比如：
#   ✅ repo.get_by_id(x)        —— 按 ID 查
#   ✅ repo.create(obj)         —— 插入一条
#   ❌ repo.cancel_order(x)     —— 这是业务逻辑，不该在这一层
#
# 【为什么要有这一层】
# 业务层（Service）直接写 SQL 的话：
#   - 业务代码里混着数据库细节，难读
#   - 换数据库要改很多地方
#   - 没法单独测试业务逻辑
#
# 有了 Repository：
#   - 业务层只调方法名，不关心 SQL
#   - 换数据库只改这一层
#   - 可以给 Repository 做 mock，单独测业务
# ============================================================

from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

# 泛型：T 是任意 ORM 模型类
ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    【干什么】通用 CRUD 基类。

    【子类怎么用】
        class ProductRepository(BaseRepository[Product]):
            def __init__(self, db: AsyncSession):
                super().__init__(Product, db)

    【提供的通用方法】
        get_by_id / get_all / count / create / update / delete / exists
    """

    def __init__(self, model: type[ModelT], db: AsyncSession) -> None:
        """
        【参数】
            model: ORM 模型类（如 Product）
            db:    数据库会话
        """
        self.model = model
        self.db = db

    # ────────────────────────────────────────────────────────
    # 查询
    # ────────────────────────────────────────────────────────

    async def get_by_id(self, id_value: Any) -> ModelT | None:
        """
        【干什么】按主键查一条。

        【返回】
            查到 → 模型对象
            查不到 → None
        """
        stmt = select(self.model).where(self.model.id == id_value)  # type: ignore[attr-defined]
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        stmt: Select | None = None,
    ) -> list[ModelT]:
        """
        【干什么】查列表。

        【参数】
            offset: 跳过多少条（分页用）
            limit:  取多少条
            stmt:   自定义查询语句（不传就查全表）

        【返回】
            模型对象列表
        """
        if stmt is None:
            stmt = select(self.model)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count(self, stmt: Select | None = None) -> int:
        """
        【干什么】数一共多少条。

        【为什么要单独一个方法】
        分页时前端要知道总数。
        如果先查出所有数据再 len()，数据多了会很慢。
        用 SQL 的 COUNT 直接在数据库里算，快得多。
        """
        if stmt is None:
            stmt = select(self.model)
        # 把原查询包一层，用 COUNT 统计
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.db.execute(count_stmt)
        return result.scalar_one()

    async def exists(self, **filters: Any) -> bool:
        """
        【干什么】判断有没有符合条件的记录。

        【例子】
            if await repo.exists(order_no="TWL123"):
                ...
        """
        stmt = select(self.model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        stmt = stmt.limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    # ────────────────────────────────────────────────────────
    # 写入
    # ────────────────────────────────────────────────────────

    async def create(self, obj: ModelT) -> ModelT:
        """
        【干什么】插入一条记录。

        【注意】
        这里只是 add + flush，没有 commit。
        commit 由上层（get_db 依赖）统一处理。
        这样多个操作可以在一个事务里，要么全成功要么全失败。
        """
        self.db.add(obj)
        await self.db.flush()      # 立刻写入（但不提交），拿到自增 ID
        await self.db.refresh(obj)  # 刷新，拿到数据库生成的默认值
        return obj

    async def create_many(self, objs: list[ModelT]) -> list[ModelT]:
        """
        【干什么】批量插入。

        【为什么不用循环 create】
        批量插入只发一次 SQL，快得多。
        比如订单的多个明细，一次插入。
        """
        self.db.add_all(objs)
        await self.db.flush()
        return objs

    async def update(self, obj: ModelT, **fields: Any) -> ModelT:
        """
        【干什么】更新记录的部分字段。

        【例子】
            await repo.update(order, status="paid", paid_at="2026-10-20 14:00:00")

        【注意】
        只更新传进来的字段，没传的保持原值。
        """
        for key, value in fields.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: ModelT) -> None:
        """
        【干什么】删除一条记录。

        【警告】
        物理删除，删了就没了。
        商品这类数据建议用状态字段（status）做软删除，不要物理删。
        """
        await self.db.delete(obj)
        await self.db.flush()

    # ────────────────────────────────────────────────────────
    # 工具
    # ────────────────────────────────────────────────────────

    def apply_filters(self, stmt: Select, **filters: Any) -> Select:
        """
        【干什么】给查询语句加筛选条件。

        【例子】
            stmt = self.apply_filters(select(Product), status="on", category="love")

        【注意】
        值为 None 的筛选项会被跳过（表示"不筛选这个字段"）。
        """
        for key, value in filters.items():
            if value is None:
                continue
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        return stmt
