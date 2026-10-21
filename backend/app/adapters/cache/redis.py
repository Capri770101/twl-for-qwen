# ============================================================
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
