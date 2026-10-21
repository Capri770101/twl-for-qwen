# ============================================================
# 【这个文件是干什么的】
# 数据库连接管理：建立连接池、提供会话、定义 ORM 基类。
#
# 【为什么用 async】
# FastAPI 是异步框架。如果用同步数据库，
# 每个数据库操作都会卡住整个服务（其他请求排队等）。
# 异步的话，等待数据库时可以处理别的请求。
#
# 【连接池是什么】
# 每次操作数据库都新建连接太慢。
# 连接池预先建好一批连接，用完放回去，下次直接用。
#
# 【怎么用】
#   from app.core.database import get_db
#
#   @router.get("/x")
#   async def handler(db: AsyncSession = Depends(get_db)):
#       result = await db.execute(select(Product))
# ============================================================

from collections.abc import AsyncGenerator
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# ════════════════════════════════════════════════════════════
# 【ORM 基类】
#
# 所有数据库模型都继承它。
# 用了 SQLAlchemy 2.0 的 Mapped 写法（类型注解式）。
# ════════════════════════════════════════════════════════════
class Base(DeclarativeBase):
    """
    【干什么】所有表的基类。

    【为什么建两个时间戳】
    created_at 和 updated_at 几乎每张表都要，
    放在基类里，子类不用重复写。
    """

    # 创建时间：插入时自动填
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )

    # 更新时间：每次修改自动更新
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )


# ════════════════════════════════════════════════════════════
# 【创建引擎】
#
# 引擎 = 连接池的管理者。
# 整个应用只需要一个引擎，全局共享。
# ════════════════════════════════════════════════════════════
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,              # True 会打印所有 SQL（调试用）
    pool_size=settings.DB_POOL_SIZE,    # 常驻连接数
    max_overflow=settings.DB_MAX_OVERFLOW,  # 高峰期最多额外开多少
    pool_recycle=settings.DB_POOL_RECYCLE,  # 连接多久回收（秒）
    pool_pre_ping=True,                 # 取连接前先 ping 一下，防止用死连接
)


# ════════════════════════════════════════════════════════════
# 【会话工厂】
#
# 会话 = 一次数据库操作的上下文。
# expire_on_commit=False 的意思是：commit 之后对象还能访问属性
# （默认 True 会失效，导致访问时报错）。
# ════════════════════════════════════════════════════════════
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# ════════════════════════════════════════════════════════════
# 【FastAPI 依赖注入：拿数据库会话】
#
# 【怎么用】
#   async def handler(db: AsyncSession = Depends(get_db)):
#
# 【它做了什么】
# 请求进来时开一个会话，请求结束自动关闭。
# 出异常会自动回滚。
#
# 【为什么用 yield】
# FastAPI 的依赖注入用 yield 表示"请求前准备，请求后清理"。
# ════════════════════════════════════════════════════════════
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()      # 正常结束，提交
        except Exception:
            await session.rollback()    # 出异常，回滚
            raise
        finally:
            await session.close()


# ════════════════════════════════════════════════════════════
# 【启动时检查数据库能不能连上】
#
# 连不上就直接报错，不要带着问题启动。
# 早发现比晚发现好。
# ════════════════════════════════════════════════════════════
async def check_database_connection() -> bool:
    """
    【干什么】测试数据库连接。

    【返回】
        True = 能连上
        False = 连不上（会打日志）

    【在什么时候调用】
        app/main.py 的 startup 事件里
    """
    from sqlalchemy import text

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info(
            "数据库连接成功",
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            database=settings.POSTGRES_DB,
        )
        return True
    except Exception as exc:
        logger.error(
            "数据库连接失败",
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            database=settings.POSTGRES_DB,
            error=str(exc),
        )
        return False


# ════════════════════════════════════════════════════════════
# 【关闭时释放连接池】
# ════════════════════════════════════════════════════════════
async def close_database() -> None:
    """服务关闭时调用，释放所有连接"""
    await engine.dispose()
    logger.info("数据库连接池已关闭")
