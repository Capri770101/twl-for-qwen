# ============================================================
# 【这个文件是干什么的】
# 根据配置返回对应的短信实例。
#
# 【怎么切换】
# 改 .env 里的 SMS_PROVIDER=mock / aliyun / tencent
# ============================================================

from functools import lru_cache

from app.adapters.sms.base import BaseSms, SmsResult
from app.adapters.sms.mock import MockSms
from app.core.config import settings


@lru_cache
def get_sms() -> BaseSms:
    """返回当前配置对应的短信实例"""
    if settings.SMS_PROVIDER == "aliyun":
        from app.adapters.sms.aliyun import AliyunSms

        return AliyunSms(
            key_id=settings.ALIYUN_SMS_KEY_ID,
            key_secret=settings.ALIYUN_SMS_KEY_SECRET,
            sign_name=settings.ALIYUN_SMS_SIGN_NAME,
            template_code=settings.ALIYUN_SMS_TEMPLATE_CODE,
        )

    # 默认 mock
    return MockSms()


__all__ = ["BaseSms", "SmsResult", "MockSms", "get_sms"]
