# ============================================================
# 【这个文件是干什么的】
# 订单接口的请求/响应格式。
#
# 【这个文件的重要性】
# 订单是系统的核心，这里的字段定义直接决定前端能拿到什么数据。
# 改之前要考虑清楚，因为涉及前后端联调。
# ============================================================

from datetime import datetime
from decimal import Decimal

from pydantic import Field, field_validator

from app.schemas.common import BaseSchema


# ════════════════════════════════════════════════════════════
# 【下单请求】
# ════════════════════════════════════════════════════════════

class OrderItemIn(BaseSchema):
    """订单里的一件商品"""

    product_id: str = Field(..., description="商品 ID")
    qty: int = Field(1, ge=1, le=99, description="数量")


class ReceiverInfo(BaseSchema):
    """收花人信息"""

    name: str = Field(..., min_length=1, max_length=50, description="姓名")
    phone: str = Field(..., description="手机号")
    province: str | None = Field(None, max_length=50, description="省")
    city: str | None = Field(None, max_length=50, description="市")
    district: str | None = Field(None, max_length=50, description="区")
    detail: str = Field(..., min_length=1, max_length=300, description="详细地址")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """
        【干什么】校验手机号格式。

        【为什么在这校验】
        在下单入口就拦住，不要等到后面才发现格式不对。
        """
        v = v.strip().replace(" ", "").replace("-", "")
        if not v.isdigit() or len(v) != 11 or not v.startswith("1"):
            raise ValueError("手机号格式不正确，应为 11 位数字")
        return v


class OrderCreate(BaseSchema):
    """下单请求"""

    items: list[OrderItemIn] = Field(..., min_length=1, description="购买的商品")
    receiver: ReceiverInfo = Field(..., description="收花人信息")
    delivery_date: str | None = Field(None, description="配送日期，如 2026-10-21")
    delivery_slot: str | None = Field(None, description="配送时段，如 18:00-20:00")
    card_message: str | None = Field(None, max_length=500, description="贺卡留言")
    anonymous: bool = Field(False, description="是否匿名")
    remark: str | None = Field(None, max_length=500, description="订单备注")

    @field_validator("items")
    @classmethod
    def validate_items(cls, v: list[OrderItemIn]) -> list[OrderItemIn]:
        """
        【干什么】检查同一个商品有没有重复提交。

        【为什么】
        同一商品提交两次，库存会扣两次，但用户可能只是想改数量。
        合并成一个更合理。
        """
        seen: dict[str, int] = {}
        for item in v:
            seen[item.product_id] = seen.get(item.product_id, 0) + item.qty
        return [OrderItemIn(product_id=pid, qty=q) for pid, q in seen.items()]


# ════════════════════════════════════════════════════════════
# 【下单响应】
# ════════════════════════════════════════════════════════════

class AmountDetail(BaseSchema):
    """金额明细"""

    product: Decimal = Field(..., description="商品总额（元）")
    delivery_fee: Decimal = Field(..., description="运费（元）")
    discount: Decimal = Field(..., description="优惠（元）")
    total: Decimal = Field(..., description="应付总额（元）")


class OrderCreateResult(BaseSchema):
    """下单成功返回"""

    order_no: str = Field(..., description="订单号")
    status: str = Field(..., description="订单状态")
    amount: AmountDetail = Field(..., description="金额明细")
    expire_at: str = Field(..., description="支付截止时间")
    ttl_seconds: int = Field(..., description="剩余支付时间（秒）")


# ════════════════════════════════════════════════════════════
# 【订单查询响应】
# ════════════════════════════════════════════════════════════

class OrderItemOut(BaseSchema):
    """订单明细"""

    product_id: str
    product_name: str
    product_cover: str | None = None
    price: Decimal
    qty: int
    subtotal: Decimal


class TimelineItem(BaseSchema):
    """状态时间线的一项"""

    status: str = Field(..., description="状态值")
    status_text: str = Field(..., description="状态中文名")
    reason: str | None = Field(None, description="变化原因")
    operator: str = Field(..., description="操作方")
    time: str = Field(..., description="发生时间")


class OrderOut(BaseSchema):
    """订单详情（返回给前端）"""

    id: str
    order_no: str
    status: str
    status_text: str
    total_amount: Decimal
    delivery_fee: Decimal
    discount_amount: Decimal
    pay_amount: Decimal
    receiver: str
    phone: str
    province: str | None = None
    city: str | None = None
    district: str | None = None
    address_detail: str
    delivery_date: str | None = None
    delivery_slot: str | None = None
    card_message: str | None = None
    anonymous: bool = False
    is_demo: bool = False
    pay_channel: str | None = None
    paid_at: str | None = None
    expire_at: str | None = None
    created_at: datetime
    items: list[OrderItemOut] = Field(default_factory=list)
    timeline: list[TimelineItem] = Field(default_factory=list)

    @property
    def full_address(self) -> str:
        """
        【干什么】把省市区和详细地址拼成一个完整地址。

        【为什么写成 property】
        前端经常要显示完整地址，
        在服务端算好，前端直接用，不用每次自己拼。
        """
        parts = [self.province, self.city, self.district, self.address_detail]
        return "".join(p for p in parts if p)


class OrderBrief(BaseSchema):
    """订单简要信息（列表页用）"""

    order_no: str
    status: str
    status_text: str
    pay_amount: Decimal
    receiver: str
    delivery_date: str | None = None
    delivery_slot: str | None = None
    created_at: datetime
    items_summary: str = Field("", description="商品摘要，如「晨光序曲 ×1」")


# ════════════════════════════════════════════════════════════
# 【订单列表查询条件】
# ════════════════════════════════════════════════════════════

class OrderQuery(BaseSchema):
    """订单列表的筛选条件"""

    status: str | None = Field(None, description="按状态筛选")
    order_no: str | None = Field(None, description="按订单号搜索")
    phone: str | None = Field(None, description="按收花人电话搜索")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
