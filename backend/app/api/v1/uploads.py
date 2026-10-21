# ============================================================
# 【这个文件是干什么的】
# 图片上传接口。
#
# 【生产级设计】
#   - 必须登录才能上传（防止被刷爆磁盘/OSS 流量）
#   - 存储走适配器（开发=本地磁盘，生产=阿里云 OSS）
#   - 只允许图片格式，限制大小
#   - 文件名随机生成，不用原名（防路径穿越攻击）
# ============================================================

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.adapters.storage import get_storage
from app.api.deps import CurrentUserDep
from app.core.config import settings
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/uploads", tags=["上传"])

# 允许的扩展名
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

# 允许的 MIME 类型
ALLOWED_MIME = {
    "image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif",
}


@router.post("", response_model=ApiResponse[dict], summary="上传图片")
async def upload_image(
    user: CurrentUserDep,
    file: UploadFile = File(...),
) -> ApiResponse[dict]:
    """
    【干什么】接收一个图片文件，存起来，返回访问 URL。

    【必须登录】
    防止匿名用户刷爆磁盘 / OSS 流量。

    【限制】
    只允许 jpg/png/webp/gif，最大 5MB（可配）。
    """
    # 扩展名检查
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"只支持 {', '.join(sorted(ALLOWED_EXT))} 格式")

    # MIME 检查
    if file.content_type and file.content_type not in ALLOWED_MIME:
        raise HTTPException(400, "文件类型不对，只接受图片")

    # 读内容并检查大小
    content = await file.read()

    max_bytes = settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(400, f"文件超过 {settings.UPLOAD_MAX_SIZE_MB}MB")

    if len(content) == 0:
        raise HTTPException(400, "文件是空的")

    # 存（走适配器，开发=本地，生产=OSS）
    storage = get_storage()
    result = await storage.save(content, ext)

    return ApiResponse[dict](data={
        "url": result.url,
        "filename": result.filename,
        "size": result.size,
    })
