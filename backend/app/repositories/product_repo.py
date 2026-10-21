# ============================================================
# 【这个文件是干什么的】
# 商品的数据访问层：只负责跟数据库打交道。
#
# 【这一层不做什么】
# - 不算价格
# - 不判断库存够不够
# - 不做业务决策
# 这些都在 services/product_service.py 里。
# ============================================================

from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product, ProductStatus
from app.repositories.base import BaseRepository
from app.schemas import ProductQuery


class ProductRepository(BaseRepository[Product]):
    """
    【干什么】商品的数据库操作。

    【怎么用】
        repo = ProductRepository(db)
        products = await repo.list_products(query)
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Product, db)

    # ────────────────────────────────────────────────────────
    # 查询
    # ────────────────────────────────────────────────────────

    async def get_by_id(self, product_id: str, *, only_on_sale: bool = False) -> Product | None:
        """
        【干什么】按 ID 查商品。

        【参数】
            product_id:   商品 ID
            only_on_sale: True 表示只查上架的（前台用），False 表示都查（后台用）
        """
        stmt = select(Product).where(Product.id == product_id)
        if only_on_sale:
            stmt = stmt.where(Product.status == ProductStatus.ON.value)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def build_list_stmt(self, query: ProductQuery) -> Select:
        """
        【干什么】根据筛选条件拼出查询语句。

        【为什么单独抽出来】
        列表查询和计数查询要用同一个条件，
        抽出来可以复用，避免两处不一致。
        """
        stmt = select(Product).where(Product.status == ProductStatus.ON.value)

        # 分类
        if query.category and query.category != "all":
            stmt = stmt.where(Product.category == query.category)

        # 关键词：名称 / 副标题 / 花语 三个字段都搜
        if query.keyword:
            kw = f"%{query.keyword}%"
            stmt = stmt.where(
                or_(
                    Product.name.ilike(kw),
                    Product.subtitle.ilike(kw),
                    Product.meaning.ilike(kw),
                )
            )

        # 价格区间
        if query.min_price is not None:
            stmt = stmt.where(Product.price >= query.min_price)
        if query.max_price is not None:
            stmt = stmt.where(Product.price <= query.max_price)

        # 排序
        if query.sort == "price_asc":
            stmt = stmt.order_by(Product.price.asc())
        elif query.sort == "price_desc":
            stmt = stmt.order_by(Product.price.desc())
        elif query.sort == "newest":
            stmt = stmt.order_by(Product.created_at.desc())
        else:
            # 默认：按排序权重，权重相同的按创建时间倒序
            stmt = stmt.order_by(Product.sort_order.asc(), Product.created_at.desc())

        return stmt

    async def list_products(self, query: ProductQuery) -> list[Product]:
        """【干什么】查商品列表（分页）"""
        stmt = self.build_list_stmt(query)
        offset = (query.page - 1) * query.page_size
        stmt = stmt.offset(offset).limit(query.page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_products(self, query: ProductQuery) -> int:
        """【干什么】数符合条件的商品总数（分页用）"""
        stmt = self.build_list_stmt(query)
        return await self.count(stmt)

    async def list_admin(self, *, limit: int = 200) -> list[Product]:
        """
        【干什么】后台商品列表（包含下架的）。
        """
        stmt = (
            select(Product)
            .order_by(Product.sort_order.asc(), Product.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_category(self) -> list[tuple[str, int]]:
        """
        【干什么】统计每个分类有多少个在售商品。

        【返回】
            [("love", 3), ("daily", 2), ...]
        """
        from sqlalchemy import func

        stmt = (
            select(Product.category, func.count(Product.id))
            .where(Product.status == ProductStatus.ON.value)
            .group_by(Product.category)
        )
        result = await self.db.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    # ────────────────────────────────────────────────────────
    # 库存
    # ────────────────────────────────────────────────────────

    async def decrease_stock(self, product_id: str, qty: int) -> bool:
        """
        【干什么】扣减库存。

        【参数】
            product_id: 商品 ID
            qty:        扣多少

        【返回】
            True  = 扣成功
            False = 库存不够，没扣

        【为什么用 SQL 直接减，而不是先查再改】
        先查再改会有并发问题：
            A 查询：库存 1
            B 查询：库存 1
            A 扣减：库存 0
            B 扣减：库存 -1  ← 超卖了！

        用 UPDATE ... WHERE stock >= qty 是原子操作，
        数据库保证同一时刻只有一个能成功。

        【注意】
        这里用的是同步的 SQL 表达式更新，
        配合 WHERE 条件保证不会扣成负数。
        """
        from sqlalchemy import update

        stmt = (
            update(Product)
            .where(Product.id == product_id)
            .where(Product.stock >= qty)
            .values(stock=Product.stock - qty)
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def increase_stock(self, product_id: str, qty: int) -> None:
        """
        【干什么】加回库存。

        【什么时候用】
        订单取消、支付超时，要把之前扣掉的库存加回来。
        """
        from sqlalchemy import update

        stmt = (
            update(Product)
            .where(Product.id == product_id)
            .values(stock=Product.stock + qty)
        )
        await self.db.execute(stmt)
