# ============================================================
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
