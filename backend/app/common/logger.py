"""统一日志：幂等初始化，避免第三方库把控制台刷爆。"""

import logging
import sys

from app.config import setting

_CONFIGURED = False

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def setup_logging() -> None:
    """进程内只初始化一次，重复调用无副作用。"""
    global _CONFIGURED
    if _CONFIGURED:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt="%H:%M:%S"))

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(setting.LOG_LEVEL.upper())

    # 压制第三方库噪声
    for noisy in ("chromadb", "urllib3", "httpx", "sentence_transformers", "openai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
