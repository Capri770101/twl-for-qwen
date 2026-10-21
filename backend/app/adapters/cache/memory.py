# ============================================================
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
