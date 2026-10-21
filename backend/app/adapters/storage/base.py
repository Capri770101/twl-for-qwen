# ============================================================
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
