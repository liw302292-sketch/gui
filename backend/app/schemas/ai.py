"""AI 相关 Schema。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ExtractTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    file_id: int | None = None


class MissingFieldsRequest(BaseModel):
    requirement: dict[str, Any]


class ReplyRequest(BaseModel):
    requirement: dict[str, Any]
    quote: dict[str, Any]
    style: str = Field(default="professional", pattern="^(professional|concise|closing)$")


class ExplainRequest(BaseModel):
    quote: dict[str, Any]
    question: str = Field(default="为什么这么贵？", max_length=1000)


class SuggestRequest(BaseModel):
    requirement: dict[str, Any]
    category: str | None = None


class AIResult(BaseModel):
    ok: bool = True
    mode: str = "mock"
    model: str | None = None
    result: dict[str, Any] = Field(default_factory=dict)
    usage: dict[str, Any] | None = None

