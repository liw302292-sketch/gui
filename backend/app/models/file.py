"""上传文件元数据。真实路径永不暴露给前端。"""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, id_column, str_column, TimestampMixin


class StoredFile(Base, TimestampMixin):
    __tablename__ = "files"

    id = id_column()
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    original_name: Mapped[str] = str_column(300)
    stored_name: Mapped[str] = str_column(300)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)  # 相对 key，不是绝对路径
    storage_backend: Mapped[str] = mapped_column(String(20), default="local", nullable=False)
    content_type: Mapped[str] = str_column(120, default="application/octet-stream")
    extension: Mapped[str] = str_column(20, default="")
    size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    checksum: Mapped[str | None] = str_column(64, nullable=True)
    kind: Mapped[str] = mapped_column(String(30), default="image", nullable=False)  # image/pdf/sheet/logo
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
