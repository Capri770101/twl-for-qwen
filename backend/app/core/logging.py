# ============================================================
# 【这个文件是干什么的】
# 统一的日志系统。所有地方打日志都用这里的 logger。
#
# 【为什么不直接用 print】
# print 只能打在控制台，没法分级、没法搜、没法接监控。
# 结构化日志（JSON）能被日志系统直接解析，方便排查问题。
#
# 【怎么用】
#   from app.core.logging import get_logger
#   logger = get_logger(__name__)
#   logger.info("订单创建成功", order_no="TWL123", amount=29900)
#
# 【两种格式】
#   console = 给人看的（开发环境）
#   json    = 给机器看的（生产环境，接日志收集系统）
# ============================================================

import logging
import sys

import structlog

from app.core.config import settings


def setup_logging() -> None:
    """
    【干什么】初始化日志系统。服务启动时调用一次。

    【做了什么】
    1. 配置标准库 logging（让第三方库的日志也走同一套）
    2. 配置 structlog（我们的业务日志）
    3. 根据环境选格式：开发用彩色控制台，生产用 JSON
    """

    # ── 第一步：配置标准库 logging ──
    # 第三方库（uvicorn、sqlalchemy）用的是标准库 logging，
    # 这里把它们也纳入统一管理。
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL),
    )

    # 降低噪音：这些库的日志太多，只保留警告以上
    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # ── 第二步：配置 structlog ──
    shared_processors = [
        # 加时间戳
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=False),
        # 加调用位置（文件名:行号），排查问题时有用
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
        # 异常堆栈转成字符串
        structlog.processors.format_exc_info,
    ]

    if settings.LOG_FORMAT == "json":
        # 生产环境：输出 JSON，一行一条，方便日志系统采集
        renderer = structlog.processors.JSONRenderer(ensure_ascii=False)
    else:
        # 开发环境：彩色输出，人眼好读
        renderer = structlog.dev.ConsoleRenderer(
            colors=True,
            exception_formatter=structlog.dev.plain_traceback,
        )

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__):
    """
    【干什么】拿一个 logger 对象。

    【参数】
        name: 一般传 __name__，这样日志里能看出是哪个文件打的

    【返回】
        structlog 的 logger
    """
    return structlog.get_logger(name)
