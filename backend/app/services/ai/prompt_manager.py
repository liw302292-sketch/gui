"""Prompt 管理器：Prompt 集中存放于 app/prompts，修改 Prompt 不需要改业务代码。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.errors import AppError

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


class PromptNotFoundError(AppError):
    code = "prompt_not_found"
    message = "缺少必要的 AI Prompt 配置，请联系管理员"


class PromptManager:
    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory or PROMPTS_DIR
        self._cache: dict[str, str] = {}

    def path_for(self, name: str) -> Path:
        filename = name if name.endswith(".txt") else f"{name}.txt"
        return self.directory / filename

    def _read(self, name: str) -> str:
        if name not in self._cache:
            path = self.path_for(name)
            if not path.exists():
                raise PromptNotFoundError(f"未找到 Prompt 文件：{path.name}")
            self._cache[name] = path.read_text(encoding="utf-8")
        return self._cache[name]

    def get(self, name: str, **variables: Any) -> str:
        rendered = self._read(name)
        for key, value in variables.items():
            rendered = rendered.replace("{" + key + "}", self._stringify(value))
        return rendered

    def raw(self, name: str) -> str:
        return self._read(name)

    def available(self) -> list[str]:
        return sorted(path.name for path in self.directory.glob("*.txt"))

    def clear_cache(self) -> None:
        self._cache.clear()

    @staticmethod
    def _stringify(value: Any) -> str:
        if value is None:
            return "null"
        if isinstance(value, str):
            return value
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, indent=2, default=str)
        return str(value)


prompt_manager = PromptManager()

