# ============================================================
# 【这个文件是干什么的】
# 所有接口的「请求格式」和「响应格式」定义。
#
# 【Pydantic 模型和 ORM 模型有什么区别】
#   ORM 模型（models/）    = 数据库里的表长什么样
#   Pydantic 模型（schemas/）= 接口收发的数据长什么样
#
# 为什么不能共用一个？
# - 数据库表有内部字段（如 id、created_at），不该暴露给前端
# - 接口可能有组合字段（如 total_amount 由多个字段算出来）
# - 分开之后，改数据库不影响接口格式，改接口不影响数据库
# ============================================================

from datetime import datetime
from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


# ════════════════════════════════════════════════════════════
# 【统一响应格式】
#
# 所有接口都返回这个结构，前端处理起来简单。
#
# 成功：{"code": 0, "message": "ok", "data": {...}}
# 失败：{"code": "NOT_FOUND", "message": "商品不存在"}
# ════════════════════════════════════════════════════════════
class ApiResponse(BaseModel, Generic[T]):
    """
    【干什么】统一响应包装。

    【怎么用】
    return ApiResponse[ProductOut](data=product)
    """
    code: int | str = 0
    message: str = "ok"
    data: T | None = None


class PaginatedData(BaseModel, Generic[T]):
    """分页数据格式"""
    items: list[T]
    total: int
    page: int = 1
    page_size: int = 20


# ════════════════════════════════════════════════════════════
# 【基础配置】
#
# from_attributes=True 的意思是：
# 可以直接把 ORM 对象转成 Pydantic 模型，不用手动读属性。
# ════════════════════════════════════════════════════════════
class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,   # 自动去掉字符串首尾空格
    )
