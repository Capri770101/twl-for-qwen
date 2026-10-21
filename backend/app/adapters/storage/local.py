# ============================================================
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
