"""模型基类与公共 Mixin。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Base(DeclarativeBase):
    """所有模型的声明式基类。"""

    type_annotation_map = {dict[str, Any]: JSON, list[str]: JSON}

    def to_dict(self) -> dict[str, Any]:
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, server_default=func.now(), nullable=False
    )


class CompanyScopedMixin:
    """多租户隔离核心：任何业务查询都必须按 company_id 过滤。"""

    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )


def id_column() -> Mapped[int]:
    return mapped_column(Integer, primary_key=True, autoincrement=True)


def str_column(length: int = 100, *, nullable: bool = False, index: bool = False, default: Any = None):
    return mapped_column(String(length), nullable=nullable, index=index, default=default)
