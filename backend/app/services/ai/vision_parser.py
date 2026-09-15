"""图片 / 文件 → 结构化需求的解析入口。

真实模式：图片以 base64 作为用户消息输入传给 Vision 模型（仅支持用户消息图片输入）。
Mock 模式：返回确定性结果，保证没有 API Key 也能完整跑通 Demo。
"""

from __future__ import annotations

import logging
import re

from app.core.config import settings
from app.services.ai.deepseek_client import DeepSeekClient
from app.services.ai.prompt_manager import prompt_manager

logger = logging.getLogger("quote_engine.ai")

SUPPORTED_IMAGE_MIME = {"image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"}


def detect_mime(filename: str, content_type: str | None = None) -> str:
    if content_type and content_type.lower() in SUPPORTED_IMAGE_MIME:
        return content_type.lower()
    lowered = filename.lower()
    for mime, extensions in {
        "image/jpeg": (".jpg", ".jpeg"),
        "image/png": (".png",),
        "image/gif": (".gif",),
        "image/webp": (".webp",),
    }.items():
        if lowered.endswith(extensions):
            return mime
    return "image/png"


def extract_numbers(text: str) -> list[str]:
    return re.findall(r"\d+(?:\.\d+)?", text or "")


class VisionParser:
    """只负责「看懂图片」，不参与任何价格计算。"""

    def __init__(self, client: DeepSeekClient | None = None) -> None:
        self.client = client or DeepSeekClient()

    @property
    def model(self) -> str:
        return settings.deepseek_vision_model

    def build_prompt(self, *, requirement_text: str, category_hint: str = "") -> str:
        return prompt_manager.get(
            "quote_extract",
            requirement_text=requirement_text or "（客户未提供文字说明，请从图片中提取全部可见需求信息）",
            category_hint=category_hint or "（无）",
        )


vision_parser = VisionParser()

__all__ = ["VisionParser", "vision_parser", "detect_mime", "extract_numbers", "SUPPORTED_IMAGE_MIME"]

