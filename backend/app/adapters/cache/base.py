# ============================================================
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
