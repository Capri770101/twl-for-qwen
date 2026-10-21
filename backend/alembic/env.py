# ============================================================
# 【这个文件是干什么的】
# Alembic 的运行环境配置。Alembic 执行任何命令都会先跑这个文件。
#
# 【它做了三件事】
# 1. 从 settings 读数据库连接串（不写死在 alembic.ini 里）
# 2. 导入所有 ORM 模型（Alembic 才能看到表结构）
# 3. 配置「自动生成迁移」的规则
# ============================================================

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# 把项目根目录加到 Python 路径
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings

# 【重要】必须导入所有模型，否则 Alembic 看不到表
from app.core.database import Base
import app.models  # noqa: F401  ← 这一行的作用就是触发所有模型的导入

# Alembic 的配置对象
config = context.config

# 从 settings 读连接串，覆盖 alembic.ini 里的占位值
# 【注意】用同步连接串，Alembic 不支持 async 驱动
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目标元数据 —— Alembic 通过它知道表结构
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    【干什么】离线模式：只生成 SQL 文件，不实际连数据库。

    【什么时候用】
    生产环境不方便直连数据库时，生成 SQL 交给 DBA 执行。
    命令：alembic upgrade head --sql > migration.sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,           # 比较字段类型变化
        compare_server_default=True,  # 比较默认值变化
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    【干什么】在线模式：直接连数据库执行迁移。

    【什么时候用】
    开发和日常部署都用这个。
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# 根据运行模式选择
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
