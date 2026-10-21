# ============================================================
# 【这个文件是干什么的】
# 商品接口的请求/响应格式。
#
# 【命名约定】
#   XxxCreate  = 新建时的请求体
#   XxxUpdate  = 修改时的请求体（所有字段可选）
#   XxxOut     = 返回给前端的数据
#   XxxQuery   = 查询参数
# ============================================================

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.common import BaseSchema


# ════════════════════════════════════════════════════════════
# 【查询参数】
# ════════════════════════════════════════════════════════════

class ProductQuery(BaseSchema):
    """商品列表的筛选条件"""

    category: str | None = Field(
        None,
        description="分类：daily/love/birthday/sympathy/business",
    )
    keyword: str | None = Field(
        None,
        max_length=50,
        description="关键词（搜名称、副标题、花语）",
    )
    min_price: Decimal | None = Field(
        None,
        ge=0,
        description="最低价（元）",
    )
    max_price: Decimal | None = Field(
        None,
        ge=0,
        description="最高价（元）",
    )
    sort: str = Field(
        "recommend",
        description="排序：recommend/price_asc/price_desc/newest",
    )
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页条数")


# ════════════════════════════════════════════════════════════
# 【新建商品】
# ════════════════════════════════════════════════════════════

class ProductCreate(BaseSchema):
    """后台新建商品时的请求体"""


    id: str | None = Field(
        None,
        max_length=32,
        description="商品编号。留空则自动生成 TW+8位大写",
    )
    name: str = Field(..., min_length=1, max_length=100, description="商品名称")
    subtitle: str | None = Field(None, max_length=200, description="副标题")
    price: Decimal = Field(..., ge=0, description="售价（元）")
    original_price: Decimal | None = Field(None, ge=0, description="原价（元）")
    cover: str | None = Field(None, max_length=500, description="主图 URL")
    images: list[str] | None = Field(None, description="详情图数组")
    flowers: list[str] | None = Field(None, description="花材清单")
    meaning: str | None = Field(None, description="花语")
    description: str | None = Field(None, description="商品描述")
    category: str = Field("daily", description="分类")
    status: str = Field("on", description="状态：on/off")
    stock: int = Field(999, ge=0, description="库存")
    sort_order: int = Field(0, description="排序权重")


# ════════════════════════════════════════════════════════════
# 【修改商品】
#
# 所有字段都是可选的 —— 只传要改的字段，
# 不传的保持原值。这叫「部分更新」。
# ════════════════════════════════════════════════════════════

class ProductUpdate(BaseSchema):
    """后台修改商品时的请求体（所有字段可选）"""

    name: str | None = Field(None, min_length=1, max_length=100)
    subtitle: str | None = Field(None, max_length=200)
    price: Decimal | None = Field(None, ge=0)
    original_price: Decimal | None = Field(None, ge=0)
    cover: str | None = Field(None, max_length=500)
    images: list[str] | None = None
    flowers: list[str] | None = None
    meaning: str | None = None
    description: str | None = None
    category: str | None = None
    status: str | None = None
    stock: int | None = Field(None, ge=0)
    sort_order: int | None = None


# ════════════════════════════════════════════════════════════
# 【商品返回】
# ════════════════════════════════════════════════════════════

class ProductOut(BaseSchema):
    """返回给前端的商品数据"""

    id: str
    name: str
    subtitle: str | None = None
    price: Decimal
    original_price: Decimal | None = None
    cover: str | None = None
    images: list[str] | None = None
    flowers: list[str] | None = None
    meaning: str | None = None
    description: str | None = None
    category: str
    status: str
    stock: int
    sort_order: int
    is_demo: bool = False
    created_at: datetime


class ProductBrief(BaseSchema):
    """商品简要信息（列表页用，字段少一点，返回快）"""

    id: str
    name: str
    subtitle: str | None = None
    price: Decimal
    original_price: Decimal | None = None
    cover: str | None = None
    flowers: list[str] | None = None
    category: str
    is_demo: bool = False


# ════════════════════════════════════════════════════════════
# 【配送可用性】
# ════════════════════════════════════════════════════════════

class DeliverySlot(BaseSchema):
    """可选的配送时段"""
    time: str = Field(..., description="时段，如 18:00-20:00")
    available: bool = Field(True, description="是否可约")


class DeliveryAvailability(BaseSchema):
    """配送可用性查询结果"""

    available: bool = Field(..., description="能否送达")
    delivery_fee: Decimal = Field(..., description="运费（元）")
    free_shipping_threshold: Decimal = Field(..., description="免运费门槛（元）")
    slots: list[DeliverySlot] = Field(default_factory=list, description="可选时段")
    estimate: str = Field("", description="预计送达时间描述")
    cutoff_time: str | None = Field(None, description="当日下单截止时间")
