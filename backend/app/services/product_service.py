# ============================================================
# 【这个文件是干什么的】
# 商品的业务逻辑：列表查询、详情、配送可用性判断。
# ============================================================

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.repositories import ProductRepository
from app.schemas import (
    DeliveryAvailability,
    DeliverySlot,
    ProductQuery,
)


class ProductService:
    """【干什么】商品的业务逻辑"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ProductRepository(db)

    # ────────────────────────────────────────────────────────
    # 查询
    # ────────────────────────────────────────────────────────

    async def list_products(self, query: ProductQuery) -> tuple[list, int]:
        """
        【干什么】查商品列表。

        【返回】
            (商品列表, 总数)  —— 总数用来做分页
        """
        products = await self.repo.list_products(query)
        total = await self.repo.count_products(query)
        return products, total

    async def get_product(self, product_id: str, *, only_on_sale: bool = True):
        """
        【干什么】查商品详情。

        【可能抛出】NotFoundError
        """
        product = await self.repo.get_by_id(product_id, only_on_sale=only_on_sale)
        if product is None:
            raise NotFoundError("商品不存在")
        return product

    async def get_categories(self) -> list[dict]:
        """
        【干什么】统计各分类的商品数量。

        【返回】
            [{"key": "love", "count": 3}, ...]
        """
        rows = await self.repo.count_by_category()
        return [{"key": key, "count": count} for key, count in rows]

    # ────────────────────────────────────────────────────────
    # 配送可用性
    # ────────────────────────────────────────────────────────

    async def check_availability(
        self,
        product_id: str,
        *,
        city: str = "深圳",
        district: str = "",
    ) -> DeliveryAvailability:
        """
        【干什么】判断这个商品能不能送到指定城市，运费多少。

        【当前实现是 Mock 逻辑】
            深圳 = 当日达，可选两个时段
            其他城市 = 次日达

        【以后接真实配送范围】
        改成调用履约系统的「配送范围查询」接口。
        改动只在这个方法里，其他代码不用动。

        【参数】
            product_id: 商品 ID
            city:       收货城市
            district:   收货区县
        """
        product = await self.get_product(product_id)

        # 判断是不是深圳（支持中英文）
        is_shenzhen = (
            "深圳" in city
            or city.lower() in ("shenzhen", "sz")
        )

        # 算运费
        threshold = Decimal(settings.FREE_SHIPPING_THRESHOLD) / 100
        base_fee = Decimal(settings.BASE_SHIPPING_FEE) / 100
        fee = Decimal("0.00") if product.price >= threshold else base_fee

        # 时段
        if is_shenzhen:
            slots = [
                DeliverySlot(time="14:00-16:00", available=True),
                DeliverySlot(time="18:00-20:00", available=True),
            ]
            estimate = "今天送达"
            cutoff = "16:00"
        else:
            slots = [DeliverySlot(time="次日 9:00-18:00", available=True)]
            estimate = "次日送达"
            cutoff = None

        return DeliveryAvailability(
            available=True,
            delivery_fee=fee,
            free_shipping_threshold=threshold,
            slots=slots,
            estimate=estimate,
            cutoff_time=cutoff,
        )
