# -*- coding: utf-8 -*-
"""生产级整改 Step 2：Provider 抽象（缓存/短信/存储）"""

import os

B = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\backend"

os.makedirs(os.path.join(B, "app/adapters/cache"), exist_ok=True)
os.makedirs(os.path.join(B, "app/adapters/sms"), exist_ok=True)
os.makedirs(os.path.join(B, "app/adapters/storage"), exist_ok=True)


# ══════════════════════════════════════════════════════════
# 1. 缓存适配器（验证码 / 限流 / token 黑名单）
# ══════════════════════════════════════════════════════════
cache_base = '''# ============================================================
# 【这个文件是干什么的】
# 缓存层的统一接口。验证码、限流计数、token 黑名单都存这里。
#
# 【为什么要有这层】
# 开发环境用内存，生产环境用 Redis。
# 上层代码只认这套接口，换实现不用改业务代码。
#
# 【必须实现的方法】
#   get / set / delete / incr / expire
# ============================================================

from abc import ABC, abstractmethod


class BaseCache(ABC):
    """缓存接口"""

    @abstractmethod
    async def get(self, key: str) -> str | None:
        """读一个值，不存在返回 None"""

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        """写一个值，ttl 是过期秒数，None 表示永不过期"""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """删一个键"""

    @abstractmethod
    async def incr(self, key: str, ttl: int | None = None) -> int:
        """
        【干什么】自增计数。

        【用在哪】
        限流：每次请求 +1，超过阈值就拒绝。
        """

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """判断键是否存在"""
'''

with open(os.path.join(B, "app/adapters/cache/base.py"), "w", encoding="utf-8") as f:
    f.write(cache_base)


cache_memory = '''# ============================================================
# 【这个文件是干什么的】
# 内存缓存实现。开发环境用。
#
# 【限制】
#   - 进程重启就丢
#   - 多进程不共享（gunicorn 多 worker 会串）
#
# 【什么时候用】
#   只在开发环境用。生产环境必须换 Redis。
# ============================================================

import time

from app.adapters.cache.base import BaseCache


class MemoryCache(BaseCache):
    """内存缓存"""

    def __init__(self) -> None:
        # {key: (value, expire_ts or None)}
        self._store: dict[str, tuple[str, float | None]] = {}

    def _is_expired(self, expire_ts: float | None) -> bool:
        return expire_ts is not None and time.time() > expire_ts

    async def get(self, key: str) -> str | None:
        item = self._store.get(key)
        if not item:
            return None

        value, expire_ts = item
        if self._is_expired(expire_ts):
            self._store.pop(key, None)
            return None

        return value

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        expire_ts = time.time() + ttl if ttl else None
        self._store[key] = (value, expire_ts)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def incr(self, key: str, ttl: int | None = None) -> int:
        current = await self.get(key)
        new_val = int(current or 0) + 1

        # 保留原有过期时间，没有就新建
        item = self._store.get(key)
        if item and not self._is_expired(item[1]):
            self._store[key] = (str(new_val), item[1])
        else:
            expire_ts = time.time() + ttl if ttl else None
            self._store[key] = (str(new_val), expire_ts)

        return new_val

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None
'''

with open(os.path.join(B, "app/adapters/cache/memory.py"), "w", encoding="utf-8") as f:
    f.write(cache_memory)


cache_redis = '''# ============================================================
# 【这个文件是干什么的】
# Redis 缓存实现。生产环境用。
#
# 【为什么生产必须用 Redis】
#   1. 进程重启不丢验证码
#   2. 多台服务器之间共享
#   3. 支持原子操作，限流计数不会算错
#
# 【依赖】
#   pip install redis
#   并且在 .env 里配 REDIS_URL
# ============================================================

from app.adapters.cache.base import BaseCache


class RedisCache(BaseCache):
    """
    【干什么】Redis 缓存实现。

    【当前状态】
    接口已经写好，但还没接入真实 Redis。
    上线前填 REDIS_URL，装 redis 包，这个类就能用。
    """

    def __init__(self, url: str, password: str = "") -> None:
        self.url = url
        self.password = password
        self._client = None

    async def _get_client(self):
        """懒加载 Redis 客户端"""
        if self._client is None:
            try:
                import redis.asyncio as aioredis
            except ImportError as e:
                raise RuntimeError(
                    "缺少 redis 依赖。请执行：pip install redis"
                ) from e

            self._client = aioredis.from_url(
                self.url,
                password=self.password or None,
                decode_responses=True,
            )
        return self._client

    async def get(self, key: str) -> str | None:
        client = await self._get_client()
        return await client.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        client = await self._get_client()
        if ttl:
            await client.setex(key, ttl, value)
        else:
            await client.set(key, value)

    async def delete(self, key: str) -> None:
        client = await self._get_client()
        await client.delete(key)

    async def incr(self, key: str, ttl: int | None = None) -> int:
        client = await self._get_client()
        val = await client.incr(key)
        if val == 1 and ttl:
            await client.expire(key, ttl)
        return val

    async def exists(self, key: str) -> bool:
        client = await self._get_client()
        return bool(await client.exists(key))
'''

with open(os.path.join(B, "app/adapters/cache/redis.py"), "w", encoding="utf-8") as f:
    f.write(cache_redis)


cache_init = '''# ============================================================
# 【这个文件是干什么的】
# 根据配置返回对应的缓存实例。
#
# 【怎么切换】
# 改 .env 里的 CACHE_PROVIDER=memory 或 redis
# ============================================================

from functools import lru_cache

from app.adapters.cache.base import BaseCache
from app.adapters.cache.memory import MemoryCache
from app.adapters.cache.redis import RedisCache
from app.core.config import settings


@lru_cache
def get_cache() -> BaseCache:
    """返回当前配置对应的缓存实例"""
    if settings.CACHE_PROVIDER == "redis":
        return RedisCache(settings.REDIS_URL, settings.REDIS_PASSWORD)
    return MemoryCache()


__all__ = ["BaseCache", "MemoryCache", "RedisCache", "get_cache"]
'''

with open(os.path.join(B, "app/adapters/cache/__init__.py"), "w", encoding="utf-8") as f:
    f.write(cache_init)

print("  adapters/cache/ (base + memory + redis + __init__)")


# ══════════════════════════════════════════════════════════
# 2. 短信适配器
# ══════════════════════════════════════════════════════════
sms_base = '''# ============================================================
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
'''

with open(os.path.join(B, "app/adapters/sms/base.py"), "w", encoding="utf-8") as f:
    f.write(sms_base)


sms_mock = '''# ============================================================
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
'''

with open(os.path.join(B, "app/adapters/sms/mock.py"), "w", encoding="utf-8") as f:
    f.write(sms_mock)


sms_aliyun = '''# ============================================================
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
'''

with open(os.path.join(B, "app/adapters/sms/aliyun.py"), "w", encoding="utf-8") as f:
    f.write(sms_aliyun)


sms_init = '''# ============================================================
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
'''

with open(os.path.join(B, "app/adapters/sms/__init__.py"), "w", encoding="utf-8") as f:
    f.write(sms_init)

print("  adapters/sms/ (base + mock + aliyun + __init__)")


# ══════════════════════════════════════════════════════════
# 3. 存储适配器
# ══════════════════════════════════════════════════════════
storage_base = '''# ============================================================
# 【这个文件是干什么的】
# 文件存储的统一接口。
#
# 【为什么要有这层】
# 开发环境存本地磁盘，生产环境存 OSS。
# 多台服务器部署时，本地磁盘不共享，图片会 404。
# ============================================================

from abc import ABC, abstractmethod


class StorageResult:
    """上传结果"""

    def __init__(self, url: str, filename: str, size: int) -> None:
        self.url = url
        self.filename = filename
        self.size = size


class BaseStorage(ABC):
    """存储接口"""

    @abstractmethod
    async def save(self, content: bytes, ext: str) -> StorageResult:
        """
        【干什么】保存一个文件。

        【参数】
            content: 文件内容
            ext:     扩展名（含点，如 ".jpg"）

        【返回】
            StorageResult(url, filename, size)
        """

    @abstractmethod
    async def delete(self, filename: str) -> None:
        """删除一个文件"""
'''

with open(os.path.join(B, "app/adapters/storage/base.py"), "w", encoding="utf-8") as f:
    f.write(storage_base)


storage_local = '''# ============================================================
# 【这个文件是干什么的】
# 本地磁盘存储。开发环境用。
#
# 【存在哪】
#   backend/static/uploads/
#
# 【访问路径】
#   /uploads/xxxxx.jpg
#
# 【限制】
#   多台服务器之间不共享。生产环境必须换 OSS。
# ============================================================

import secrets
from pathlib import Path

from app.adapters.storage.base import BaseStorage, StorageResult


class LocalStorage(BaseStorage):
    """本地磁盘存储"""

    def __init__(self, upload_dir: Path) -> None:
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, content: bytes, ext: str) -> StorageResult:
        filename = f"{secrets.token_hex(12)}{ext}"
        path = self.upload_dir / filename

        with open(path, "wb") as f:
            f.write(content)

        return StorageResult(
            url=f"/uploads/{filename}",
            filename=filename,
            size=len(content),
        )

    async def delete(self, filename: str) -> None:
        path = self.upload_dir / filename
        if path.exists():
            path.unlink()
'''

with open(os.path.join(B, "app/adapters/storage/local.py"), "w", encoding="utf-8") as f:
    f.write(storage_local)


storage_oss = '''# ============================================================
# 【这个文件是干什么的】
# 阿里云 OSS 存储。生产环境用。
#
# 【当前状态】
# 接口已经写好，但还没接真实 SDK。
# 上线前要做的事：
#   1. pip install oss2
#   2. 在阿里云控制台创建 Bucket，配好访问权限
#   3. 在 .env 里填 OSS_ENDPOINT / OSS_BUCKET / OSS_ACCESS_KEY_ID / OSS_ACCESS_KEY_SECRET / OSS_PUBLIC_URL
#   4. 把下面 save 里的 TODO 补上
# ============================================================

import secrets

import structlog

from app.adapters.storage.base import BaseStorage, StorageResult


class OssStorage(BaseStorage):
    """阿里云 OSS 存储"""

    def __init__(
        self,
        endpoint: str,
        bucket: str,
        key_id: str,
        key_secret: str,
        public_url: str,
    ) -> None:
        self.endpoint = endpoint
        self.bucket = bucket
        self.key_id = key_id
        self.key_secret = key_secret
        self.public_url = public_url.rstrip("/")
        self.logger = structlog.get_logger(__name__)

    async def save(self, content: bytes, ext: str) -> StorageResult:
        """
        【干什么】上传到 OSS。

        【怎么实现】
        1. 装 SDK：pip install oss2
        2. 构造 oss2.Auth(key_id, key_secret)
        3. 构造 oss2.Bucket(auth, endpoint, bucket)
        4. bucket.put_object(filename, content)
        5. 返回 public_url + "/" + filename

        【参考文档】
        https://help.aliyun.com/document_detail/32068.html
        """
        filename = f"{secrets.token_hex(12)}{ext}"

        # TODO: 上线时替换成真实上传
        self.logger.warning("阿里云 OSS 未接入，这是占位实现", filename=filename)

        raise RuntimeError("阿里云 OSS 未接入，请先完成 OssStorage.save 的实现")

    async def delete(self, filename: str) -> None:
        """删除 OSS 上的文件"""
        # TODO: bucket.delete_object(filename)
        self.logger.warning("阿里云 OSS 未接入，删除已跳过", filename=filename)
'''

with open(os.path.join(B, "app/adapters/storage/oss.py"), "w", encoding="utf-8") as f:
    f.write(storage_oss)


storage_init = '''# ============================================================
# 【这个文件是干什么的】
# 根据配置返回对应的存储实例。
# ============================================================

from functools import lru_cache
from pathlib import Path

from app.adapters.storage.base import BaseStorage, StorageResult
from app.adapters.storage.local import LocalStorage
from app.core.config import settings


@lru_cache
def get_storage() -> BaseStorage:
    """返回当前配置对应的存储实例"""
    if settings.STORAGE_PROVIDER == "oss":
        from app.adapters.storage.oss import OssStorage

        return OssStorage(
            endpoint=settings.OSS_ENDPOINT,
            bucket=settings.OSS_BUCKET,
            key_id=settings.OSS_ACCESS_KEY_ID,
            key_secret=settings.OSS_ACCESS_KEY_SECRET,
            public_url=settings.OSS_PUBLIC_URL,
        )

    # 默认本地
    backend_dir = Path(__file__).resolve().parent.parent.parent.parent
    return LocalStorage(backend_dir / "static" / "uploads")


__all__ = ["BaseStorage", "StorageResult", "LocalStorage", "get_storage"]
'''

with open(os.path.join(B, "app/adapters/storage/__init__.py"), "w", encoding="utf-8") as f:
    f.write(storage_init)

print("  adapters/storage/ (base + local + oss + __init__)")

print("\nStep 2 完成")
