# ============================================================
# 【这个文件是干什么的】
# 集中管理所有配置项。数据库地址、密钥、端口这些，全在这里读。
#
# 【为什么要单独一个文件】
# 硬编码在代码里的配置，换个环境就要改代码。
# 全部集中在这，改环境只改 .env 文件，代码不动。
#
# 【怎么用】
#   from app.core.config import settings
#   print(settings.POSTGRES_HOST)
#
# 【配置从哪来】
# 优先级：环境变量 > .env 文件 > 这里的默认值
# ============================================================

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    【干什么】所有配置项的定义。

    【怎么加新配置】
    在这里加一个字段，写上类型和默认值，然后在 .env.example 里加上对应说明。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ────────────────────────────────────────────────────────
    # 应用
    # ────────────────────────────────────────────────────────
    APP_NAME: str = "跳舞兰 H5 电商系统"
    APP_VERSION: str = "1.0.0"
    APP_ENV: Literal["development", "testing", "production"] = "development"
    DEBUG: bool = True

    # 服务监听地址
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # 接口路径前缀（版本化）
    API_V1_PREFIX: str = "/api/v1"

    # ────────────────────────────────────────────────────────
    # 数据库（PostgreSQL）
    #
    # 【为什么要这么多字段分开写】
    # 拼 URL 方便，也方便单独读取某一项做日志。
    # ────────────────────────────────────────────────────────
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "tiaowulan"
    POSTGRES_PASSWORD: str = "twl_dev_2026"
    POSTGRES_DB: str = "tiaowulan"

    # 连接池配置
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> str:
        """异步连接串（给 SQLAlchemy async 用）"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL_SYNC(self) -> str:
        """同步连接串（给 Alembic 迁移用）"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ────────────────────────────────────────────────────────
    # 跨域
    #
    # 【生产环境必须收紧】
    # 填具体域名，不要用 *。用逗号分隔。
    # 例：https://h5.tiaowulan.com,https://www.tiaowulan.com
    # ────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # ────────────────────────────────────────────────────────
    # 安全
    # ────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-please-use-a-random-string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天

    # ────────────────────────────────────────────────────────
    # 业务参数
    # ────────────────────────────────────────────────────────
    # 订单超时时间（分钟）—— 超过这个时间没支付自动取消
    ORDER_EXPIRE_MINUTES: int = 30

    # 免运费门槛（分）—— 满这个金额免运费
    FREE_SHIPPING_THRESHOLD: int = 19900

    # 基础运费（分）
    BASE_SHIPPING_FEE: int = 1500


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

    # ────────────────────────────────────────────────────────
    # 外部系统（适配器选择）
    #
    # 【mock = 假实现，real = 真实对接】
    # 改这里就能切换，不用改代码。
    # ────────────────────────────────────────────────────────
    PAYMENT_PROVIDER: Literal["mock", "wechat", "alipay"] = "mock"
    FULFILLMENT_PROVIDER: Literal["mock", "real"] = "mock"
    DATASOURCE_PROVIDER: Literal["mock", "real"] = "mock"

    # ────────────────────────────────────────────────────────
    # 外部系统地址（接真实时填）
    # ────────────────────────────────────────────────────────
    FULFILLMENT_API_URL: str = ""
    FULFILLMENT_API_KEY: str = ""

    DATASOURCE_API_URL: str = ""
    DATASOURCE_API_KEY: str = ""

    # 微信支付
    WECHAT_PAY_MCH_ID: str = ""
    WECHAT_PAY_APP_ID: str = ""
    WECHAT_PAY_KEY: str = ""

    # 支付宝
    ALIPAY_APP_ID: str = ""
    ALIPAY_PRIVATE_KEY: str = ""
    ALIPAY_PUBLIC_KEY: str = ""

    # ────────────────────────────────────────────────────────
    # 日志
    # ────────────────────────────────────────────────────────
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    LOG_FORMAT: Literal["json", "console"] = "console"


@lru_cache
def get_settings() -> Settings:
    """
    【干什么】获取配置单例。

    【为什么要 lru_cache】
    Settings() 每次都会读 .env 文件，慢。
    加了这个装饰器，第一次读完之后就缓存，后面直接返回同一个对象。
    """
    return Settings()


# 全局配置对象，直接 import 用
settings = get_settings()
