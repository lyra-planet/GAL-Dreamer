"""
日志工具模块
提供统一的日志接口
"""
import sys
from pathlib import Path
from loguru import logger
from typing import Optional

from .config import config


class Logger:
    """日志管理器"""

    def __init__(self):
        self._setup_logger()

    def _setup_logger(self):
        """配置日志系统"""
        # 移除默认的handler
        logger.remove()

        # 控制台输出
        if config.LOG_CONSOLE:
            logger.add(
                sys.stderr,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                level=config.LOG_LEVEL,
                colorize=True,
                backtrace=True,
                diagnose=True
            )

        # 文件输出
        log_file = Path(config.LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=config.LOG_LEVEL,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            backtrace=True,
            diagnose=True
        )

    def get_logger(self, name: Optional[str] = None):
        """获取logger实例"""
        if name:
            return logger.bind(name=name)
        return logger


# 创建全局日志实例
log_manager = Logger()
log = log_manager.get_logger()


if __name__ == "__main__":
    # 测试日志
    log.debug("这是debug日志")
    log.info("这是info日志")
    log.warning("这是warning日志")
    log.error("这是error日志")
    log.critical("这是critical日志")
