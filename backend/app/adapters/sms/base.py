# ============================================================
# 【这个文件是干什么的】
# 短信服务的统一接口。
#
# 【为什么要有这层】
# 开发环境没法真发短信（要花钱、要备案签名），
# 用 mock 实现把验证码打印出来。
# 上线换成阿里云/腾讯云，业务代码不用改。
# ============================================================

from abc import ABC, abstractmethod


class SmsResult:
    """发送结果"""

    def __init__(self, success: bool, message: str = "", code: str = "") -> None:
        self.success = success
        self.message = message
        self.code = code  # mock 专用：返回生成的验证码


class BaseSms(ABC):
    """短信接口"""

    @abstractmethod
    async def send_code(self, phone: str, code: str) -> SmsResult:
        """
        【干什么】发验证码短信。

        【参数】
            phone: 手机号
            code:  验证码内容

        【返回】
            SmsResult(success, message)
        """
