# ============================================================
# 【这个文件是干什么的】
# 商品相关的接口（HTTP 路由层）。
#
# 【这一层的原则：薄】
# 只做三件事：
#   1. 接收参数
#   2. 调 Service
#   3. 返回结果
#
# 不写任何业务逻辑（算法、判断、规则）。
# 业务逻辑全在 services/product_service.py。
#
# 【为什么要这么分】
# 以后要换 web 框架（比如换成 Django），
# 只重写这一层，业务逻辑一行不用改。
# ============================================================

from fastapi import APIRouter, Query

from app.api.deps import DbDep, ProductServiceDep
from app.repositories import ProductRepository
from app.schemas import (
    ApiResponse,
    DeliveryAvailability,
    PaginatedData,
    ProductBrief,
    ProductCreate,
    ProductOut,
    ProductQuery,
    ProductUpdate,
)

router = APIRouter(prefix="/products", tags=["商品"])


# ════════════════════════════════════════════════════════════
# 【前台接口】
# ════════════════════════════════════════════════════════════

@router.get(
    "",
    response_model=ApiResponse[PaginatedData[ProductBrief]],
    summary="商品列表",
    description="支持按分类筛选、关键词搜索、价格排序、分页",
)
async def list_products(
    service: ProductServiceDep,
    category: str | None = Query(None, description="分类"),
    keyword: str | None = Query(None, description="关键词"),
    min_price: float | None = Query(None, ge=0, description="最低价"),
    max_price: float | None = Query(None, ge=0, description="最高价"),
    sort: str = Query("recommend", description="排序方式"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
):
    """
    【干什么】查商品列表。

    【例子】
        GET /api/v1/products?category=love&sort=price_asc&page=1
        → 告白类的商品，按价格从低到高
    """
    from decimal import Decimal

    query = ProductQuery(
        category=category,
        keyword=keyword,
        min_price=Decimal(str(min_price)) if min_price is not None else None,
        max_price=Decimal(str(max_price)) if max_price is not None else None,
        sort=sort,
        page=page,
        page_size=page_size,
    )

    products, total = await service.list_products(query)

    return ApiResponse(
        data=PaginatedData(
            items=[ProductBrief.model_validate(p) for p in products],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get(
    "/{product_id}",
    response_model=ApiResponse[ProductOut],
    summary="商品详情",
)
async def get_product(product_id: str, service: ProductServiceDep):
    """
    【干什么】查单个商品的完整信息。

    【例子】
        GET /api/v1/products/TW-001
    """
    product = await service.get_product(product_id)
    return ApiResponse(data=ProductOut.model_validate(product))


@router.get(
    "/{product_id}/availability",
    response_model=ApiResponse[DeliveryAvailability],
    summary="配送可用性查询",
    description="查这个商品能不能送到指定城市、运费多少、可选时段",
)
async def check_availability(
    product_id: str,
    service: ProductServiceDep,
    city: str = Query("深圳", description="收货城市"),
    district: str = Query("", description="收货区县"),
):
    """
    【干什么】查能不能送到、运费多少。

    【例子】
        GET /api/v1/products/TW-001/availability?city=深圳&district=南山区
    """
    result = await service.check_availability(
        product_id,
        city=city,
        district=district,
    )
    return ApiResponse(data=result)


@router.get(
    "/meta/categories",
    summary="分类统计",
    description="返回每个分类有多少个在售商品",
)
async def get_categories(service: ProductServiceDep):
    """
    【干什么】统计各分类的商品数量（用于前台筛选栏显示）。
    """
    categories = await service.get_categories()
    return ApiResponse(data=categories)


# ════════════════════════════════════════════════════════════
# 【后台接口】
#
# 【注意】当前没有鉴权。
# 上生产前必须加管理员登录，否则任何人都能改商品。
# ════════════════════════════════════════════════════════════

@router.post(
    "/admin",
    summary="【后台】新建商品",
    description="TODO: 上线前必须加管理员鉴权",
)
async def create_product(
    data: ProductCreate,
    db: DbDep,
):
    """
    【干什么】新建一个商品。

    【当前状态】待加鉴权
    """
    from app.models import Product
    import uuid

    product = Product(
        id="TW" + uuid.uuid4().hex[:8].upper(),
        name=data.name,
        subtitle=data.subtitle,
        price=data.price,
        original_price=data.original_price,
        cover=data.cover,
        images=data.images,
        flowers=data.flowers,
        meaning=data.meaning,
        description=data.description,
        category=data.category,
        status=data.status,
        stock=data.stock,
        sort_order=data.sort_order,
    )

    repo = ProductRepository(db)
    await repo.create(product)

    return ApiResponse(data={"id": product.id})


@router.put(
    "/admin/{product_id}",
    summary="【后台】修改商品",
    description="TODO: 上线前必须加管理员鉴权",
)
async def update_product(
    product_id: str,
    data: ProductUpdate,
    db: DbDep,
):
    """
    【干什么】修改商品（只改传上来的字段）。
    """
    repo = ProductRepository(db)
    product = await repo.get_by_id(product_id, only_on_sale=False)

    if product is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("商品不存在")

    # 只更新传了的字段
    update_data = data.model_dump(exclude_unset=True)
    await repo.update(product, **update_data)

    return ApiResponse(data={"id": product.id})


@router.delete(
    "/admin/{product_id}",
    summary="【后台】删除商品",
    description="TODO: 上线前必须加管理员鉴权",
)
async def delete_product(product_id: str, db: DbDep):
    """
    【干什么】删除商品。

    【建议】
    不要物理删除，用 status='off' 下架。
    物理删除会让历史订单的关联断掉。
    """
    repo = ProductRepository(db)
    product = await repo.get_by_id(product_id, only_on_sale=False)

    if product is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("商品不存在")

    await repo.delete(product)
    return ApiResponse(data={"deleted": product_id})
