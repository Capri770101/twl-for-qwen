# ============================================================
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
