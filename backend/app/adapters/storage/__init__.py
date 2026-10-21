# ============================================================
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
