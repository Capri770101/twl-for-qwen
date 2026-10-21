# ============================================================
# 【这个文件是干什么的】
# 后端服务的入口。启动这个文件，整个 API 服务就跑起来了。
#
# 【启动命令】
#   uvicorn app.main:app --reload --port 8000
#   或者
#   python -m app.main
#
# 【启动后会发生什么】
#   1. 初始化日志
#   2. 检查数据库能不能连上（连不上直接退出，不要带病运行）
#   3. 挂载中间件（CORS、请求日志）
#   4. 挂载路由（/api/v1/*）
#   5. 注册异常处理器
#   6. 开始监听端口
#
# 【启动后能访问】
#   http://127.0.0.1:8000/docs      → 接口文档（能直接点着测）
#   http://127.0.0.1:8000/health    → 健康检查
#   http://127.0.0.1:8000/api/v1/... → 所有接口
#
# 【跟其他文件的关系】
# 它是总入口，把 app/api/、app/core/、app/adapters/ 全部串起来。
# ============================================================

import sys
import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import check_database_connection, close_database
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging

# 初始化日志（必须最先做，后面的代码才能打日志）
setup_logging()
logger = get_logger(__name__)


# ════════════════════════════════════════════════════════════
# 【生命周期管理】
#
# FastAPI 的 lifespan 机制：
#   yield 之前 = 启动时执行
#   yield 之后 = 关闭时执行
#
# 比旧的 @app.on_event("startup") 更好，能保证成对出现。
# ════════════════════════════════════════════════════════════
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    【干什么】管理服务的启动和关闭。
    """
    # ── 启动 ──
    logger.info(
        "服务启动中",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        env=settings.APP_ENV,
    )

    # 检查数据库
    db_ok = await check_database_connection()
    if not db_ok:
        logger.error("数据库连接失败，服务无法启动")
        logger.error(
            "请检查：",
            hint="1. PostgreSQL 服务是否在运行",
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            db=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
        )
        # 【重要】连不上就直接退出，不要带病运行
        sys.exit(1)

    logger.info(
        "服务启动完成",
        docs="http://127.0.0.1:8000/docs",
        api=settings.API_V1_PREFIX,
    )

    # ── 启动后台任务：订单超时自动取消 ──
    from app.services import order_task

    order_task.start()

    yield   # ← 服务在这期间运行

    # ── 关闭 ──
    logger.info("服务正在关闭")

    # 先停后台任务
    await order_task.stop()

    await close_database()
    logger.info("服务已关闭")


# ════════════════════════════════════════════════════════════
# 【创建应用】
# ════════════════════════════════════════════════════════════
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## 跳舞兰 H5 电商系统 · 接口文档

### 接口分组
- **商品** `/api/v1/products` —— 商品列表、详情、配送查询
- **订单** `/api/v1/orders` —— 下单、查询、取消、状态推进
- **支付** `/api/v1/payments` —— 发起支付、回调处理
- **售后** `/api/v1/tickets` —— 提交工单、客服回复
- **履约** `/api/v1/deliveries` —— 推送订单、状态回传
- **后台** `/api/v1/admin` —— 数据看板、全部订单、日志

### 统一响应格式
```json
{"code": 0, "message": "ok", "data": {...}}
```

### 错误格式
```json
{"code": "NOT_FOUND", "message": "商品不存在", "detail": null}
```
    """,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)


# ════════════════════════════════════════════════════════════
# 【中间件：跨域】
#
# 【什么是跨域】
# 浏览器安全策略：A 网站的页面不能直接请求 B 网站的接口。
# 开发时前端跑在 3000 端口、后端跑在 8000，属于跨域，需要允许。
#
# 【生产环境要收紧】
# .env 里把 CORS_ORIGINS 改成自己的域名，不要用 *
# ════════════════════════════════════════════════════════════
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ════════════════════════════════════════════════════════════
# 【中间件：请求日志】
#
# 【干什么】
# 每个请求记录：方法、路径、状态码、耗时。
#
# 【为什么要有】
# 出问题时能查到：哪个接口慢了、哪个接口报错了。
# ════════════════════════════════════════════════════════════
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    【干什么】给每个请求分配 ID、记录耗时、脱敏日志。

    【为什么要请求 ID】
    一个请求可能打多行日志（进入、查库、出错）。
    有了统一 ID 才能串起来排查。
    """
    from app.core.request_log import mask_sensitive

    # 用客户端传的，没有就新建
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    start = time.time()

    response = await call_next(request)

    duration_ms = round((time.time() - start) * 1000, 2)

    # 只记录 API 请求，静态资源不记（太多）
    if request.url.path.startswith(settings.API_V1_PREFIX):
        log_method = logger.warning if response.status_code >= 400 else logger.info
        log_method(
            "请求",
            method=request.method,
            path=mask_sensitive(request.url.path),
            status=response.status_code,
            duration_ms=duration_ms,
        )

    # 响应头带上，方便前端报错时提供
    response.headers["X-Process-Time"] = str(duration_ms)
    response.headers["X-Request-Id"] = request_id
    return response


# ════════════════════════════════════════════════════════════
# 【注册异常处理器】
# ════════════════════════════════════════════════════════════
register_exception_handlers(app)


# ════════════════════════════════════════════════════════════
# 【挂载路由】
# ════════════════════════════════════════════════════════════
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# ════════════════════════════════════════════════════════════
# 【健康检查】
#
# 【干什么】
# 部署后监控系统定时访问这个地址，确认服务活着。
# 返回 200 就是正常。
# ════════════════════════════════════════════════════════════
@app.get("/health", tags=["系统"], summary="健康检查")
async def health_check():
    """
    【干什么】确认服务在运行。

    【返回】
        {"status": "ok", "service": "...", "version": "..."}
    """
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
    }


# ════════════════════════════════════════════════════════════
# 【静态托管】
#
# 【目录约定】
#   项目根/
#   ├── frontend/            前端（页面 + js + images）
#   └── backend/
#       ├── app/             后端代码
#       └── static/uploads/  用户上传的文件（运行时产生）
#
# 【为什么要挂在这里】
# 前端是静态 HTML，从 file:// 打开调 /api/v1 会有跨域问题。
# 挂到同一个端口（8000）下，前后端同源，没有跨域。
#
# 【访问方式】
#   http://127.0.0.1:8000/                → 首页
#   http://127.0.0.1:8000/shop.html       → 商城
#   http://127.0.0.1:8000/js/api.js       → 前端接口封装
#   http://127.0.0.1:8000/images/xx.png   → 商品图
#   http://127.0.0.1:8000/uploads/xx.png  → 用户上传的图
#   http://127.0.0.1:8000/api/v1/...      → 接口
#
# 【挂载顺序很重要】
# 1. /api/v1（已在上面注册）
# 2. /uploads（用户上传，必须先于 / 挂载）
# 3. /（前端根目录，最后挂载，兜底）
# ════════════════════════════════════════════════════════════
from pathlib import Path

from fastapi.staticfiles import StaticFiles

# main.py 在 backend/app/ 下
# .parent      = backend/app
# .parent.parent = backend
BACKEND_DIR = Path(__file__).resolve().parent.parent

# 项目根 = backend 的上一级
PROJECT_ROOT = BACKEND_DIR.parent

# 前端目录
FRONTEND_DIR = PROJECT_ROOT / "frontend"
FRONTEND_DIR.mkdir(exist_ok=True)

# 用户上传目录（运行时数据，留在 backend 下）
UPLOAD_DIR = BACKEND_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 先挂 uploads（子路径要在 / 之前挂，否则被拦截）
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# 再挂前端根目录（兜底）
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


# ════════════════════════════════════════════════════════════
# 【直接运行】
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
