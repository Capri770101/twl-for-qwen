# ============================================================
# 【这个文件是干什么的】
# 地址簿的请求格式和响应格式。
# ============================================================

from pydantic import Field, field_validator

from app.schemas.common import BaseSchema


class AddressIn(BaseSchema):
    """新增/修改地址的请求"""

    receiver: str = Field(..., min_length=1, max_length=50, description="收件人姓名")
    phone: str = Field(..., description="手机号")
    province: str | None = Field(None, max_length=50, description="省")
    city: str | None = Field(None, max_length=50, description="市")
    district: str | None = Field(None, max_length=50, description="区")
    detail: str = Field(..., min_length=1, max_length=300, description="详细地址")
    tag: str | None = Field(None, max_length=20, description="标签：家/公司/学校")
    is_default: bool = Field(False, description="是否设为默认")

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str) -> str:
        v = v.strip().replace(" ", "").replace("-", "")
        if not v.isdigit() or len(v) != 11 or not v.startswith("1"):
            raise ValueError("手机号格式不对")
        return v


class AddressOut(BaseSchema):
    """地址信息"""

    id: str
    receiver: str
    phone: str
    province: str | None = None
    city: str | None = None
    district: str | None = None
    detail: str
    tag: str | None = None
    is_default: bool = False
    full_address: str = ""


class AddressListOut(BaseSchema):
    """地址列表"""

    items: list[AddressOut]
    total: int
