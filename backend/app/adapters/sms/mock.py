# ============================================================
# 【这个文件是干什么的】
# Mock 短信实现。开发环境用。
#
# 【干什么】
#   不真发短信，只把验证码打到日志里，
#   同时通过返回值把验证码给前端（方便测试）。
#
# 【生产环境必须禁用】
#   config 里的 validate_production 会拦住。
# ============================================================

import structlog

from app.adapters.sms.base import BaseSms, SmsResult


class MockSms(BaseSms):
    """假短信"""

    def __init__(self) -> None:
        self.logger = structlog.get_logger(__name__)

    async def send_code(self, phone: str, code: str) -> SmsResult:
        # 打日志（脱敏）
        masked = f"{phone[:3]}****{phone[-4:]}" if len(phone) == 11 else phone
        self.logger.info("【Mock短信】", phone=masked, code=code)

        return SmsResult(
            success=True,
            message="已发送（开发环境，验证码见日志）",
            code=code,
        )
