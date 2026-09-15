"""AI 任务与用量统计。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, id_column, str_column, TimestampMixin


class AITask(Base, TimestampMixin):
    __tablename__ = "ai_tasks"

    id = id_column()
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # requirement_extract / missing_fields / reply_draft / price_explain / price_suggestion
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    # pending / success / failed / retried
    provider: Mapped[str] = mapped_column(String(30), default="deepseek", nullable=False)
    model: Mapped[str] = str_column(80, default="")
    mode: Mapped[str] = mapped_column(String(10), default="mock", nullable=False)

    input_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    output_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Numeric(12, 6), default=0, nullable=False)
    file_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("files.id", ondelete="SET NULL"), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AIUsage(Base, TimestampMixin):
    __tablename__ = "ai_usage"

    id = id_column()
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    task_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("ai_tasks.id", ondelete="SET NULL"), nullable=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model: Mapped[str] = str_column(80, default="")
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Numeric(12, 6), default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="success", nullable=False, index=True)

