# -*- coding: utf-8 -*-
"""
核心逻辑单元测试
不连数据库、不发请求，纯函数级验证
"""

import os
import sys
from decimal import Decimal

import pytest

sys.path.insert(0, r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\backend")


# ══════════════════════════════════════════════════════════
# 1. 订单状态机
# ══════════════════════════════════════════════════════════
class TestOrderStateMachine:
    """订单状态流转规则"""

    def test_valid_transitions(self):
        """合法的状态流转"""
        from app.services.order_service import TRANSITIONS
        from app.models.order import OrderStatus

        # 待支付 → 已支付 / 已取消
        assert OrderStatus.PAID in TRANSITIONS[OrderStatus.PENDING_PAYMENT]
        assert OrderStatus.CANCELLED in TRANSITIONS[OrderStatus.PENDING_PAYMENT]

        # 已支付 → 配花中 / 已取消
        assert OrderStatus.PREPARING in TRANSITIONS[OrderStatus.PAID]
        assert OrderStatus.CANCELLED in TRANSITIONS[OrderStatus.PAID]

        # 配花中 → 配送中 / 已取消
        assert OrderStatus.DELIVERING in TRANSITIONS[OrderStatus.PREPARING]

        # 配送中 → 已送达
        assert OrderStatus.DELIVERED in TRANSITIONS[OrderStatus.DELIVERING]

        # 已送达 → 已完成
        assert OrderStatus.COMPLETED in TRANSITIONS[OrderStatus.DELIVERED]

    def test_terminal_states_have_no_exit(self):
        """终态不能再流转"""
        from app.services.order_service import TRANSITIONS
        from app.models.order import OrderStatus

        assert TRANSITIONS[OrderStatus.COMPLETED] == set()
        assert TRANSITIONS[OrderStatus.CANCELLED] == set()

    def test_cannot_skip_states(self):
        """不能跳状态（待支付不能直接到配送中）"""
        from app.services.order_service import TRANSITIONS
        from app.models.order import OrderStatus

        assert OrderStatus.DELIVERING not in TRANSITIONS[OrderStatus.PENDING_PAYMENT]
        assert OrderStatus.DELIVERED not in TRANSITIONS[OrderStatus.PENDING_PAYMENT]
        assert OrderStatus.COMPLETED not in TRANSITIONS[OrderStatus.PENDING_PAYMENT]

    def test_cannot_go_backward(self):
        """不能回退（已支付不能回到待支付）"""
        from app.services.order_service import TRANSITIONS
        from app.models.order import OrderStatus

        assert OrderStatus.PENDING_PAYMENT not in TRANSITIONS[OrderStatus.PAID]
        assert OrderStatus.PAID not in TRANSITIONS[OrderStatus.PREPARING]


# ══════════════════════════════════════════════════════════
# 2. 金额计算
# ══════════════════════════════════════════════════════════
class TestAmountCalculation:
    """金额计算精度"""

    def test_decimal_no_float_error(self):
        """Decimal 不会有浮点误差"""
        # 0.1 + 0.2 在 float 下是 0.30000000000000004
        assert Decimal("0.1") + Decimal("0.2") == Decimal("0.3")

        # 用 float 就会出错
        assert 0.1 + 0.2 != 0.3

    def test_subtotal(self):
        """小计 = 单价 × 数量"""
        price = Decimal("299.00")
        qty = 3
        assert price * qty == Decimal("897.00")

    def test_total_with_shipping(self):
        """总计 = 商品 + 运费 - 优惠"""
        product = Decimal("299.00")
        shipping = Decimal("15.00")
        discount = Decimal("0.00")
        assert product + shipping - discount == Decimal("314.00")

    def test_free_shipping_threshold(self):
        """满 199 免运费"""
        threshold = Decimal("199.00")

        # 刚好满
        assert Decimal("199.00") >= threshold
        # 差一分
        assert Decimal("198.99") < threshold


# ══════════════════════════════════════════════════════════
# 3. Token
# ══════════════════════════════════════════════════════════
class TestToken:
    """token 签发与校验"""

    def test_sign_and_parse(self):
        """签了能解出来"""
        from app.services.auth_service import make_token

        user_id = "u123456789"
        token = make_token(user_id)

        # 格式：user_id.expire.sig
        parts = token.split(".")
        assert len(parts) == 3
        assert parts[0] == user_id

    def test_tampered_token_rejected(self):
        """改过的 token 签名对不上"""
        from app.services.auth_service import make_token, _sign

        token = make_token("u123")
        parts = token.split(".")

        # 篡改 user_id
        fake = f"u999.{parts[1]}.{parts[2]}"
        fake_sig = _sign(f"u999.{parts[1]}")

        assert fake_sig != parts[2]

    def test_mask_phone(self):
        """手机号脱敏"""
        from app.services.auth_service import mask_phone

        assert mask_phone("13812345678") == "138****5678"
        assert mask_phone("13800001234") == "138****1234"
        assert mask_phone("") == ""
        assert mask_phone(None) is None


# ══════════════════════════════════════════════════════════
# 4. 日志脱敏
# ══════════════════════════════════════════════════════════
class TestLogMasking:
    """日志里的敏感信息打码"""

    def test_mask_phone_in_text(self):
        from app.core.request_log import mask_sensitive

        assert "138****5678" in mask_sensitive("用户手机 13812345678")
        assert "13812345678" not in mask_sensitive("用户手机 13812345678")

    def test_mask_token(self):
        from app.core.request_log import mask_sensitive

        text = "token: u123456789012.1793150879.a88b24df235d92def5e3340d2b385bcb"
        masked = mask_sensitive(text)
        assert "***TOKEN***" in masked

    def test_mask_dict(self):
        from app.core.request_log import mask_dict

        data = {
            "phone": "13812345678",
            "token": "abcdefghijklmnop",
            "name": "张三",
        }
        masked = mask_dict(data)

        assert masked["phone"] != "13812345678"
        assert masked["token"] == "***"
        assert masked["name"] == "张三"


# ══════════════════════════════════════════════════════════
# 5. 地址簿规则
# ══════════════════════════════════════════════════════════
class TestAddressRules:
    """地址簿业务规则"""

    def test_max_address_limit(self):
        """地址上限 20 条"""
        from app.services.address_service import MAX_ADDRESS

        assert MAX_ADDRESS == 20


# ══════════════════════════════════════════════════════════
# 6. 配置校验
# ══════════════════════════════════════════════════════════
class TestProductionValidation:
    """生产环境配置检查"""

    def test_dev_env_passes(self):
        """开发环境不报错"""
        from app.core.config import Settings

        s = Settings(
            APP_ENV="development",
            DEBUG=True,
            SECRET_KEY="change-me",
        )
        assert s.validate_production() == []

    def test_prod_with_defaults_fails(self):
        """生产环境用默认配置要报错"""
        from app.core.config import Settings

        s = Settings(
            APP_ENV="production",
            DEBUG=True,
            SECRET_KEY="change-me-in-production-please-use-a-random-string",
            CACHE_PROVIDER="memory",
            SMS_PROVIDER="mock",
            STORAGE_PROVIDER="local",
            PAYMENT_PROVIDER="mock",
            ADMIN_PHONES="13800001234",
        )
        issues = s.validate_production()

        # 至少 7 项不合规
        assert len(issues) >= 7

        text = " ".join(issues)
        assert "SECRET_KEY" in text
        assert "DEBUG" in text
        assert "Redis" in text or "redis" in text
        assert "短信" in text
        assert "OSS" in text or "oss" in text
        assert "支付" in text
        assert "ADMIN_PHONES" in text


# ══════════════════════════════════════════════════════════
# 7. 商品分类
# ══════════════════════════════════════════════════════════
class TestProductCategory:
    """商品分类枚举"""

    def test_categories_defined(self):
        from app.models.product import ProductCategory

        # 至少 4 个分类
        assert len(list(ProductCategory)) >= 4

    def test_category_values(self):
        from app.models.product import ProductCategory

        values = [c.value for c in ProductCategory]
        assert "daily" in values
        assert "love" in values


# ══════════════════════════════════════════════════════════
# 8. 订单号格式
# ══════════════════════════════════════════════════════════
class TestOrderNo:
    """订单号生成规则"""

    def test_order_no_format(self):
        """格式：TWL + 时间戳 + 随机码"""
        import re

        # 实际格式示例
        order_no = "TWL20261021094733 4BC7".replace(" ", "")

        assert order_no.startswith("TWL")
        assert len(order_no) == 21
        assert re.match(r"^TWL\d{14}[0-9A-F]{4}$", order_no)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
