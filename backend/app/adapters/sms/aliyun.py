# ============================================================
# 【这个文件是干什么的】
# 阿里云短信实现。生产环境用。
#
# 【当前状态】
# 接口已经写好，但还没接入真实 SDK。
# 上线前要做的事：
#   1. pip install alibabacloud_dysmsapi20170525
#   2. 在阿里云控制台申请短信签名和模板
#   3. 在 .env 里填 ALIYUN_SMS_KEY_ID / KEY_SECRET / SIGN_NAME / TEMPLATE_CODE
#   4. 把下面 send_code 里的 TODO 补上
#
# 【为什么要提前写这个空壳】
# 让上线时的改动局限在这一个文件里，不用动业务代码。
# ============================================================

import structlog

from app.adapters.sms.base import BaseSms, SmsResult


class AliyunSms(BaseSms):
    """阿里云短信"""

    def __init__(
        self,
        key_id: str,
        key_secret: str,
        sign_name: str,
        template_code: str,
    ) -> None:
        self.key_id = key_id
        self.key_secret = key_secret
        self.sign_name = sign_name
        self.template_code = template_code
        self.logger = structlog.get_logger(__name__)

    async def send_code(self, phone: str, code: str) -> SmsResult:
        """
        【干什么】调阿里云短信 API 发验证码。

        【怎么实现】
        1. 装 SDK：pip install alibabacloud_dysmsapi20170525
        2. 构造 Client（用 key_id / key_secret）
        3. 调 SendSms，传 phone / sign_name / template_code / template_param={"code": code}
        4. 检查返回的 Code == "OK"

        【参考文档】
        https://help.aliyun.com/document_detail/419273.html
        """
        masked = f"{phone[:3]}****{phone[-4:]}" if len(phone) == 11 else phone

        # TODO: 上线时替换成真实调用
        self.logger.warning(
            "阿里云短信未接入，这是占位实现",
            phone=masked,
        )

        return SmsResult(
            success=False,
            message="阿里云短信未接入，请先完成 AliyunSms.send_code 的实现",
        )
