# -*- coding: utf-8 -*-
"""生产级整改 Step 4：管理员鉴权 + 接口保护"""

import os, re

B = r"D:\DeepSeek-Harness\WorkSpace\跳舞兰\backend"


# ══════════════════════════════════════════════════════════
# 1. deps.py 加 require_admin
# ══════════════════════════════════════════════════════════
deps_path = os.path.join(B, "app/api/deps.py")
html = open(deps_path, encoding="utf-8").read()

admin_dep = '''

async def require_admin(user: CurrentUserDep) -> User:
    """
    【干什么】要求当前用户是管理员。

    【为什么单独一个依赖】
    后台接口全部要走这个，避免漏加。
    漏加一个就是数据泄露。
    """
    if not getattr(user, "is_admin", False):
        raise BusinessError("需要管理员权限", code="FORBIDDEN", status_code=403)
    return user


AdminDep = Annotated[User, Depends(require_admin)]
'''

if "AdminDep" not in html:
    html = html.rstrip() + admin_dep + "\n"
    open(deps_path, "w", encoding="utf-8").write(html)
    print("  deps.py: 加 AdminDep")


# ══════════════════════════════════════════════════════════
# 2. auth.py 路由：适配新 send_code + logout 作废 token
# ══════════════════════════════════════════════════════════
auth_router = '''# ============================================================
# 【这个文件是干什么的】
# 登录相关的接口。
#
# 【生产级设计】
#   - 验证码走短信适配器（开发 mock / 生产阿里云）
#   - 三重限流（手机号间隔、日限、IP 时限）
#   - 验证码只在非生产环境返回给前端
#   - 退出登录把 token 加入黑名单，立即失效
# ============================================================

from fastapi import APIRouter, Header, Request

from app.api.deps import CurrentUserDep, DbDep
from app.core.config import settings
from app.schemas.auth import LoginIn, LoginOut, SendCodeIn, SendCodeOut, UserOut
from app.schemas.common import ApiResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


def _client_ip(request: Request) -> str:
    """
    【干什么】取真实客户端 IP。

    【为什么要看 X-Forwarded-For】
    部署在 Nginx 后面时，request.client.host 拿到的是 Nginx 的 IP。
    真实 IP 在 X-Forwarded-For 头的第一个。
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


@router.post("/send-code", response_model=ApiResponse[SendCodeOut], summary="发送验证码")
async def send_code(payload: SendCodeIn, request: Request) -> ApiResponse[SendCodeOut]:
    """
    【干什么】给手机号发验证码。

    【限流】
    同一手机号 60 秒 1 次，每天 10 次；同一 IP 每小时 20 次。

    【开发环境】
    验证码放在 dev_code 里返回，方便测试。
    生产环境这个字段是 None。
    """
    ok, message, dev_code = await auth_service.send_code(
        payload.phone, _client_ip(request)
    )

    return ApiResponse[SendCodeOut](
        data=SendCodeOut(
            phone=auth_service.mask_phone(payload.phone),
            expires_in=300,
            dev_code=dev_code,
        )
    )


@router.post("/login", response_model=ApiResponse[LoginOut], summary="登录")
async def login(payload: LoginIn, db: DbDep) -> ApiResponse[LoginOut]:
    """
    【干什么】校验验证码，登录或自动注册。

    【防爆破】
    同一手机号连续失败 5 次，锁 15 分钟。
    """
    # 先查是不是被锁了
    await auth_service.check_login_attempts(payload.phone)

    # 校验验证码
    try:
        await auth_service.verify_code(payload.phone, payload.code)
    except Exception:
        await auth_service.record_login_fail(payload.phone)
        raise

    # 登录成功，清失败计数
    await auth_service.clear_login_fail(payload.phone)

    # 找用户或建用户
    user, is_new = await auth_service.get_or_create_user(db, payload.phone)

    # 签 token
    token = auth_service.make_token(user.id)

    return ApiResponse[LoginOut](
        data=LoginOut(
            token=token,
            user=UserOut(**auth_service.user_to_dict(user)),
            is_new=is_new,
        )
    )


@router.get("/me", response_model=ApiResponse[UserOut], summary="当前用户")
async def me(user: CurrentUserDep) -> ApiResponse[UserOut]:
    """查当前登录用户的信息"""
    return ApiResponse[UserOut](data=UserOut(**auth_service.user_to_dict(user)))


@router.post("/logout", response_model=ApiResponse[dict], summary="退出登录")
async def logout(
    user: CurrentUserDep,
    authorization: str | None = Header(None),
) -> ApiResponse[dict]:
    """
    【干什么】退出登录。

    【做了什么】
    把当前 token 加入黑名单，立即失效。
    即使有人拿到了这个 token，也用不了了。
    """
    if authorization and settings.TOKEN_BLACKLIST_ENABLED:
        parts = authorization.split()
        if len(parts) == 2:
            await auth_service.revoke_token(parts[1])

    return ApiResponse[dict](data={"message": "已退出"})
'''

with open(os.path.join(B, "app/api/v1/auth.py"), "w", encoding="utf-8") as f:
    f.write(auth_router)
print("  api/v1/auth.py: 重写（限流 + 黑名单）")


# ══════════════════════════════════════════════════════════
# 3. admin.py 全部接口加 AdminDep
# ══════════════════════════════════════════════════════════
p = os.path.join(B, "app/api/v1/admin.py")
html = open(p, encoding="utf-8").read()

# 加 import
if "AdminDep" not in html:
    html = html.replace(
        "from app.api.deps import",
        "from app.api.deps import AdminDep, "
    ) if "from app.api.deps import" in html else html

    # 如果原来没有 deps import，加一行
    if "AdminDep" not in html:
        html = html.replace(
            "from fastapi import APIRouter",
            "from fastapi import APIRouter\n\nfrom app.api.deps import AdminDep"
        )

# 给每个 async def 加 admin 参数
# 匹配: async def xxx(...) -> ...:
# 插入 admin: AdminDep 作为第一个参数
def add_admin_param(m):
    func_sig = m.group(0)
    # 如果已经有 AdminDep 或 CurrentUserDep 就跳过
    if "AdminDep" in func_sig or "CurrentUserDep" in func_sig:
        return func_sig

    # 在第一个参数位置插入
    if "()" in func_sig:
        return func_sig.replace("()", "(admin: AdminDep)")
    # 有参数的情况：(xxx: Type) -> (admin: AdminDep, xxx: Type)
    return re.sub(r"\((\w+: )", r"(admin: AdminDep, \1", func_sig, count=1)

# 只处理带 @router 装饰器的函数
html = re.sub(
    r"(?<=@router\.(?:get|post|put|delete)\([^\)]*\)\n)async def \w+\([^)]*\)",
    add_admin_param,
    html,
)

open(p, "w", encoding="utf-8").write(html)
print("  api/v1/admin.py: 加 AdminDep")


# ══════════════════════════════════════════════════════════
# 4. articles.py admin 接口加 AdminDep
# ══════════════════════════════════════════════════════════
p = os.path.join(B, "app/api/v1/articles.py")
html = open(p, encoding="utf-8").read()

if "AdminDep" not in html:
    html = html.replace(
        "from app.api.deps import DbDep",
        "from app.api.deps import AdminDep, DbDep"
    )

    # 给 admin 接口加参数
    html = html.replace(
        "async def list_all_articles(\n    db: DbDep,",
        "async def list_all_articles(\n    admin: AdminDep,\n    db: DbDep,"
    )
    html = html.replace(
        "async def create_article(payload: ArticleIn, db: DbDep) -> ApiResponse[ArticleDetailOut]:",
        "async def create_article(\n    payload: ArticleIn,\n    admin: AdminDep,\n    db: DbDep,\n) -> ApiResponse[ArticleDetailOut]:"
    )
    html = html.replace(
        "async def update_article(\n    article_id: str,\n    payload: ArticleIn,\n    db: DbDep,",
        "async def update_article(\n    article_id: str,\n    payload: ArticleIn,\n    admin: AdminDep,\n    db: DbDep,"
    )
    html = html.replace(
        "async def delete_article(article_id: str, db: DbDep) -> ApiResponse[dict]:",
        "async def delete_article(\n    article_id: str,\n    admin: AdminDep,\n    db: DbDep,\n) -> ApiResponse[dict]:"
    )
    open(p, "w", encoding="utf-8").write(html)
    print("  api/v1/articles.py: admin 接口加鉴权")


# ══════════════════════════════════════════════════════════
# 5. settings.py PUT 加 AdminDep
# ══════════════════════════════════════════════════════════
p = os.path.join(B, "app/api/v1/settings.py")
html = open(p, encoding="utf-8").read()

if "AdminDep" not in html:
    html = html.replace(
        "from app.api.deps import DbDep",
        "from app.api.deps import AdminDep, DbDep"
    )
    html = html.replace(
        "async def save_delivery(payload: DeliverySetting, db: DbDep) -> ApiResponse[DeliverySetting]:",
        "async def save_delivery(\n    payload: DeliverySetting,\n    admin: AdminDep,\n    db: DbDep,\n) -> ApiResponse[DeliverySetting]:"
    )
    open(p, "w", encoding="utf-8").write(html)
    print("  api/v1/settings.py: PUT 加鉴权")


# ══════════════════════════════════════════════════════════
# 6. uploads.py 用 storage provider + 加登录
# ══════════════════════════════════════════════════════════
uploads_router = '''# ============================================================
# 【这个文件是干什么的】
# 图片上传接口。
#
# 【生产级设计】
#   - 必须登录才能上传（防止被刷爆磁盘）
#   - 存储走适配器（开发=本地，生产=OSS）
#   - 只允许图片，限制大小
#   - 文件名随机生成，不用原名（防路径穿越）
# ============================================================

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.adapters.storage import get_storage
from app.api.deps import CurrentUserDep
from app.core.config import settings
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/uploads", tags=["上传"])

# 允许的格式
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

# 允许的 MIME
ALLOWED_MIME = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
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
    # 扩展名
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"只支持 {', '.join(sorted(ALLOWED_EXT))} 格式")

    # MIME
    if file.content_type and file.content_type not in ALLOWED_MIME:
        raise HTTPException(400, "文件类型不对，只接受图片")

    # 读内容
    content = await file.read()

    max_bytes = settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(400, f"文件超过 {settings.UPLOAD_MAX_SIZE_MB}MB")

    if len(content) == 0:
        raise HTTPException(400, "文件是空的")

    # 存
    storage = get_storage()
    result = await storage.save(content, ext)

    return ApiResponse[dict](data={
        "url": result.url,
        "filename": result.filename,
        "size": result.size,
    })
'''

with open(os.path.join(B, "app/api/v1/uploads.py"), "w", encoding="utf-8") as f:
    f.write(uploads_router)
print("  api/v1/uploads.py: 重写（鉴权 + Storage Provider）")

print("\nStep 4 完成")
