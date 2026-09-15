"""Redis 客户端（可选）。

未配置或不可用时自动降级为进程内实现，保证项目零依赖也能运行。
"""

from __future__ import annotations

import logging
import time
from typing import Any

from app.core.config import settings

logger = logging.getLogger("quote_engine.app")

try:  # pragma: no cover - 取决于运行环境
    import redis as redis_lib
except ImportError:  # pragma: no cover
    redis_lib = None  # type: ignore[assignment]


class InMemoryStore:
    """进程内 fallback：支持 incr / expire / get / delete。"""

    def __init__(self) -> None:
        self._data: dict[str, tuple[Any, float | None]] = {}

    def _purge(self, key: str) -> None:
        item = self._data.get(key)
        if item and item[1] is not None and item[1] < time.time():
            self._data.pop(key, None)

    def incr(self, key: str) -> int:
        self._purge(key)
        value, expires = self._data.get(key, (0, None))
        value = int(value) + 1
        self._data[key] = (value, expires)
        return value

    def expire(self, key: str, seconds: int) -> None:
        value, _ = self._data.get(key, (0, None))
        self._data[key] = (value, time.time() + seconds)

    def get(self, key: str) -> Any:
        self._purge(key)
        item = self._data.get(key)
        return item[0] if item else None

    def setex(self, key: str, seconds: int, value: Any) -> None:
        self._data[key] = (value, time.time() + seconds)

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def ttl(self, key: str) -> int:
        self._purge(key)
        item = self._data.get(key)
        if not item or item[1] is None:
            return -1
        return max(int(item[1] - time.time()), 0)


_memory = InMemoryStore()
_redis_client: Any = None
_redis_checked = False


def get_store() -> Any:
    """返回 Redis 客户端或进程内降级实现。"""
    global _redis_client, _redis_checked
    if _redis_checked:
        return _redis_client or _memory
    _redis_checked = True
    if settings.redis_url and redis_lib is not None:
        try:
            client = redis_lib.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=2)
            client.ping()
            _redis_client = client
            logger.info("Redis 已连接：%s", settings.redis_url)
        except Exception as exc:  # pragma: no cover
            logger.warning("Redis 不可用，降级为进程内缓存：%s", exc)
            _redis_client = None
    return _redis_client or _memory


def redis_available() -> bool:
    return get_store() is not _memory

