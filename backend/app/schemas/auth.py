# ============================================================
# 【这个文件是干什么的】
# 登录相关的请求格式和响应格式。
#
# 【登录流程】
#   1. 前端调 /auth/send-code，传手机号
#   2. 后端生成 6 位验证码（开发环境直接返回，正式环境发短信）
#   3. 前端调 /auth/login，传手机号 + 验证码
#   4. 后端校验通过，创建/查找用户，返回 token
#   5. 前端把 token 存起来，后续请求带在 Authorization 头里
# ============================================================

from pydantic import Field, field_validator

from app.schemas.common import BaseSchema


class SendCodeIn(BaseSchema):
    """发送验证码的请求"""

    phone: str = Field(..., description="手机号")

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str) -> str:
        """校验手机号格式：11 位数字，1 开头"""
        v = v.strip().replace(" ", "").replace("-", "")
        if not v.isdigit() or len(v) != 11 or not v.startswith("1"):
            raise ValueError("手机号格式不对")
        return v


class SendCodeOut(BaseSchema):
    """发送验证码的响应"""

    phone: str = Field(..., description="手机号（脱敏）")
    expires_in: int = Field(..., description="有效期（秒）")
    dev_code: str | None = Field(None, description="【开发环境】验证码，正式环境为空")


class LoginIn(BaseSchema):
    """登录请求"""

    phone: str = Field(..., description="手机号")
    code: str = Field(..., min_length=4, max_length=6, description="验证码")

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str) -> str:
        v = v.strip().replace(" ", "").replace("-", "")
        if not v.isdigit() or len(v) != 11 or not v.startswith("1"):
            raise ValueError("手机号格式不对")
        return v


class UserOut(BaseSchema):
    """用户信息"""

    id: str = Field(..., description="用户 ID")
    phone: str | None = Field(None, description="手机号（脱敏）")
    nickname: str | None = Field(None, description="昵称")
    avatar: str | None = Field(None, description="头像")
    is_admin: bool = Field(False, description="是否管理员")
    created_at: str | None = Field(None, description="注册时间")


class LoginOut(BaseSchema):
    """登录成功的响应"""

    token: str = Field(..., description="登录凭证，后续请求放在 Authorization: Bearer <token>")
    user: UserOut = Field(..., description="用户信息")
    is_new: bool = Field(False, description="是否新注册用户")
