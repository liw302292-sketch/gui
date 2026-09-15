"""日志配置：application / ai / error / audit 四类日志。"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from app.core.config import settings

LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)-28s | %(message)s"

AI_LOGGER = "quote_engine.ai"
AUDIT_LOGGER = "quote_engine.audit"
ERROR_LOGGER = "quote_engine.error"
APP_LOGGER = "quote_engine.app"


def _handler(for_file: bool) -> logging.Handler:
    if for_file and settings.log_to_file:
        handler: logging.Handler = RotatingFileHandler(
            settings.log_path / "app.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
    else:
        handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    return handler


class _MemoryLogHandler(logging.Handler):
    """进程内环形日志缓冲，供管理员后台“日志/异常”页面读取。"""

    def __init__(self, capacity: int = 500) -> None:
        super().__init__()
        self.capacity = capacity
        self.records: list[dict[str, str]] = []

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.records.append(
                {
                    "time": self.format(record),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "path": getattr(record, "pathname", ""),
                    "line": str(getattr(record, "lineno", "")),
                }
            )
            if len(self.records) > self.capacity:
                del self.records[: len(self.records) - self.capacity]
        except Exception:  # pragma: no cover - 日志失败不能影响业务
            pass

    def snapshot(self, level: str | None = None, limit: int = 200) -> list[dict[str, str]]:
        items = self.records
        if level:
            items = [item for item in items if item["level"] == level]
        return list(reversed(items))[:limit]


memory_log_handler = _MemoryLogHandler()
memory_log_handler.setFormatter(logging.Formatter("%(asctime)s"))


def setup_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(settings.log_level.upper())
    root.addHandler(_handler(for_file=False))
    if settings.log_to_file:
        root.addHandler(_handler(for_file=True))
    root.addHandler(memory_log_handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    # 中文字体子集化时 fontTools 会对 .ttc 集合字体输出无意义的告警，这里静音。
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    logging.getLogger(AI_LOGGER).setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def audit_log(action: str, *, company_id: int | None, user_id: int | None, detail: str = "") -> None:
    logging.getLogger(AUDIT_LOGGER).info(
        "action=%s company=%s user=%s %s", action, company_id, user_id, detail
    )
