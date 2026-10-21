# -*- coding: utf-8 -*-
"""生产级整改 Step 1：配置强化 + User.is_admin + 后台鉴权"""

import os

B = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\backend"


# ══════════════════════════════════════════════════════════
# 1. config.py 追加生产配置项
# ══════════════════════════════════════════════════════════
cfg_path = os.path.join(B, "app/core/config.py")
html = open(cfg_path, encoding="utf-8").read()

extra_cfg = '''
    # ────────────────────────────────────────────────────────
    # 【生产环境安全配置】
    # ────────────────────────────────────────────────────────

    # 允许手机号自助注册为管理员（上线前必须清空）
    ADMIN_PHONES: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def admin_phones_list(self) -> list[str]:
        return [p.strip() for p in self.ADMIN_PHONES.split(",") if p.strip()]

    # ────────────────────────────────────────────────────────
    # 【限流】
    #
    # 【为什么要限流】
    # 发验证码、登录、下单这些接口不限制的话，
    # 有人可以刷短信（花钱）、刷单（占库存）。
    # ────────────────────────────────────────────────────────

    # 发验证码：同一手机号 N 秒内只能发 1 次
    SMS_INTERVAL_SECONDS: int = 60

    # 发验证码：同一手机号每天最多发几次
    SMS_DAILY_LIMIT: int = 10

    # 发验证码：同一 IP 每小时最多发几次
    SMS_IP_HOURLY_LIMIT: int = 20

    # 登录：同一手机号 N 分钟内最多试错几次
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCK_MINUTES: int = 15

    # 下单：同一 IP 每小时最多下几单
    ORDER_IP_HOURLY_LIMIT: int = 30

    # ────────────────────────────────────────────────────────
    # 【验证码存储】
    #
    # memory = 进程内存（开发环境，重启丢失）
    # redis  = Redis（生产环境必须用这个）
    # ────────────────────────────────────────────────────────
    CACHE_PROVIDER: Literal["memory", "redis"] = "memory"

    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    REDIS_PASSWORD: str = ""

    # ────────────────────────────────────────────────────────
    # 【短信服务商】
    #
    # mock  = 假发送，验证码直接返回给前端（仅开发环境）
    # aliyun = 阿里云短信
    # tencent = 腾讯云短信
    # ────────────────────────────────────────────────────────
    SMS_PROVIDER: Literal["mock", "aliyun", "tencent"] = "mock"

    ALIYUN_SMS_KEY_ID: str = ""
    ALIYUN_SMS_KEY_SECRET: str = ""
    ALIYUN_SMS_SIGN_NAME: str = ""
    ALIYUN_SMS_TEMPLATE_CODE: str = ""

    TENCENT_SMS_SECRET_ID: str = ""
    TENCENT_SMS_SECRET_KEY: str = ""
    TENCENT_SMS_SDK_APP_ID: str = ""
    TENCENT_SMS_SIGN_NAME: str = ""
    TENCENT_SMS_TEMPLATE_ID: str = ""

    # ────────────────────────────────────────────────────────
    # 【文件存储】
    #
    # local = 本地磁盘（开发环境）
    # oss   = 阿里云 OSS
    # cos   = 腾讯云 COS
    # ────────────────────────────────────────────────────────
    STORAGE_PROVIDER: Literal["local", "oss", "cos"] = "local"

    OSS_ENDPOINT: str = ""
    OSS_BUCKET: str = ""
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_PUBLIC_URL: str = ""

    # 上传大小上限（MB）
    UPLOAD_MAX_SIZE_MB: int = 5

    # ────────────────────────────────────────────────────────
    # 【Token】
    # ────────────────────────────────────────────────────────

    # token 有效期（分钟）。生产环境建议 120（2 小时）+ refresh token
    TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # 是否启用 token 黑名单（退出登录后立即失效）
    TOKEN_BLACKLIST_ENABLED: bool = True

    # ────────────────────────────────────────────────────────
    # 【安全响应头】
    # ────────────────────────────────────────────────────────

    # 是否启用 HSTS（只在 HTTPS 下有意义的）
    SECURITY_HEADERS_ENABLED: bool = True

    # 允许的前端域名（生产环境填真实域名）
    ALLOWED_HOSTS: str = "*"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allowed_hosts_list(self) -> list[str]:
        return [h.strip() for h in self.ALLOWED_HOSTS.split(",") if h.strip()]

    # ────────────────────────────────────────────────────────
    # 【生产环境检查】
    # ────────────────────────────────────────────────────────

    def validate_production(self) -> list[str]:
        """
        【干什么】检查生产环境配置是否合规。

        【返回】
            问题列表。空列表 = 没问题。

        【为什么要有这个】
            启动时检查，不合规直接拒绝启动，
            比上线后出问题强。
        """
        issues = []

        if self.APP_ENV != "production":
            return issues

        # 密钥不能是默认值
        if "change-me" in self.SECRET_KEY or len(self.SECRET_KEY) < 32:
            issues.append("SECRET_KEY 必须换成至少 32 位的随机字符串")

        # 不能开 DEBUG
        if self.DEBUG:
            issues.append("生产环境必须关闭 DEBUG")

        # CORS 不能是 *
        if "*" in self.cors_origins_list:
            issues.append("CORS_ORIGINS 不能包含 *，必须填具体域名")

        # 验证码不能用内存
        if self.CACHE_PROVIDER == "memory":
            issues.append("生产环境验证码必须用 Redis（CACHE_PROVIDER=redis）")

        # 短信不能用 mock
        if self.SMS_PROVIDER == "mock":
            issues.append("生产环境必须接入真实短信服务商")

        # 存储不能用 local
        if self.STORAGE_PROVIDER == "local":
            issues.append("生产环境文件存储必须用 OSS/COS（多机不共享本地磁盘）")

        # 支付不能用 mock
        if self.PAYMENT_PROVIDER == "mock":
            issues.append("生产环境必须接入真实支付网关")

        # 自助管理员必须关掉
        if self.admin_phones_list:
            issues.append("ADMIN_PHONES 上线前必须清空（否则任何人填这个手机号就是管理员）")

        return issues
'''

# 插到 "外部系统（适配器选择）" 之前
marker = "    # ────────────────────────────────────────────────────────\n    # 外部系统（适配器选择）"
if "ADMIN_PHONES" not in html:
    html = html.replace(marker, extra_cfg + "\n" + marker, 1)
    open(cfg_path, "w", encoding="utf-8").write(html)
    print("  config.py: 追加生产安全配置")


# ══════════════════════════════════════════════════════════
# 2. User 模型加 is_admin
# ══════════════════════════════════════════════════════════
user_path = os.path.join(B, "app/models/user.py")
html = open(user_path, encoding="utf-8").read()

if "is_admin" not in html:
    html = html.replace(
        '''    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        comment="是否启用",
    )''',
        '''    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        comment="是否启用",
    )

    is_admin: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        index=True,
        comment="是否管理员（能进后台）",
    )'''
    )
    open(user_path, "w", encoding="utf-8").write(html)
    print("  models/user.py: 加 is_admin 字段")


print("\nStep 1 完成")
