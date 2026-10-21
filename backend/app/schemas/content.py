# ============================================================
# 【这个文件是干什么的】
# 文章和配置的请求/响应格式。
# ============================================================

from pydantic import Field

from app.schemas.common import BaseSchema


# ── 文章 ──

class ArticleIn(BaseSchema):
    """新增/修改文章的请求"""

    slug: str = Field(..., min_length=1, max_length=120, description="网址短名")
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    summary: str | None = Field(None, max_length=500, description="摘要")
    content: str = Field("", description="正文")
    cover: str | None = Field(None, max_length=500, description="封面图")
    category: str | None = Field(None, max_length=40, description="分类")
    meaning: str | None = Field(None, max_length=300, description="花语一句话")
    tags: list[str] | None = Field(None, description="标签")
    faq: list[dict] | None = Field(None, description="FAQ 数组")
    status: str = Field("draft", description="draft/published/archived")
    seo_title: str | None = Field(None, max_length=200)
    seo_description: str | None = Field(None, max_length=500)
    sort_weight: int = Field(0, description="排序权重")


class ArticleOut(BaseSchema):
    """文章信息（列表用，不含正文）"""

    id: str
    slug: str
    title: str
    summary: str | None = None
    cover: str | None = None
    category: str | None = None
    meaning: str | None = None
    tags: list | None = None
    status: str = "draft"
    view_count: int = 0


class ArticleDetailOut(ArticleOut):
    """文章详情（含正文和 FAQ）"""

    content: str = ""
    faq: list | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    sort_weight: int = 0


class ArticleListOut(BaseSchema):
    items: list[ArticleOut]
    total: int


# ── 配置 ──

class DeliverySetting(BaseSchema):
    """配送规则"""

    free_shipping_threshold: float = Field(199, description="免运费门槛（元）")
    base_shipping_fee: float = Field(15, description="基础运费（元）")
    remote_shipping_fee: float = Field(25, description="偏远地区运费（元）")
    same_city_hours: int = Field(2, description="同城配送时效（小时）")
    cutoff_hour: int = Field(16, description="当日达截止时间（点）")
    delivery_slots: list[str] = Field(
        default_factory=lambda: ["14:00-16:00", "18:00-20:00"],
        description="可选配送时段",
    )
    payment_timeout_minutes: int = Field(30, description="订单支付超时（分钟）")
    service_hours: str = Field("9:00-21:00", description="客服时间")
