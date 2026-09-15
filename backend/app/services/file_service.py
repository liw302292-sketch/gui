"""文件上传与读取：校验、隔离存储、鉴权访问。"""

from __future__ import annotations

import io
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, NotFoundError
from app.core.storage import StorageError, get_storage, sanitize_filename, validate_upload
from app.models.file import StoredFile

logger = logging.getLogger("quote_engine.app")


class FileError(AppError):
    code = "file_error"
    message = "文件处理失败"


KIND_BY_EXTENSION = {
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".gif": "image",
    ".webp": "image",
    ".pdf": "pdf",
    ".xlsx": "sheet",
    ".xls": "sheet",
    ".csv": "sheet",
    ".txt": "text",
}


def save_upload(
    db: Session,
    *,
    company_id: int,
    user_id: int | None,
    filename: str,
    content_type: str | None,
    data: bytes,
    kind: str | None = None,
) -> StoredFile:
    safe_name = sanitize_filename(filename)
    try:
        extension = validate_upload(safe_name, content_type, len(data))
    except StorageError as exc:
        raise FileError(str(exc)) from exc

    try:
        stored = get_storage().save(company_id=company_id, filename=safe_name, data=data)
    except Exception as exc:  # pragma: no cover - 存储异常
        logger.exception("文件保存失败")
        raise FileError("文件保存失败，请稍后重试") from exc

    record = StoredFile(
        company_id=company_id,
        user_id=user_id,
        original_name=safe_name,
        stored_name=f"{stored.checksum}{extension}",
        storage_key=stored.key,
        storage_backend=stored.backend,
        content_type=content_type or "application/octet-stream",
        extension=extension,
        size=stored.size,
        checksum=stored.checksum,
        kind=kind or KIND_BY_EXTENSION.get(extension, "other"),
    )
    db.add(record)
    db.flush()
    return record


def get_file(db: Session, company_id: int, file_id: int, *, allow_public: bool = False) -> StoredFile:
    record = db.get(StoredFile, file_id)
    if not record:
        raise NotFoundError("文件不存在或已被删除")
    if record.company_id != company_id and not allow_public:
        raise NotFoundError("文件不存在或已被删除")
    return record


def read_file(record: StoredFile) -> bytes:
    try:
        return get_storage().read(record.storage_key)
    except Exception as exc:
        logger.exception("读取文件失败: %s", record.storage_key)
        raise FileError("文件读取失败，请重新上传") from exc


def delete_file(db: Session, record: StoredFile) -> None:
    get_storage().delete(record.storage_key)
    db.delete(record)


def extract_spreadsheet(data: bytes) -> list[dict[str, Any]]:
    """读取 Excel / CSV，用于产品批量导入。"""
    from openpyxl import load_workbook  # noqa: PLC0415

    rows: list[dict[str, Any]] = []
    workbook = load_workbook(io.BytesIO(data), data_only=True)
    sheet = workbook.active
    if sheet is None:
        return rows
    headers = [str(cell.value).strip() if cell.value is not None else "" for cell in sheet[1]]
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if row is None or all(value is None for value in row):
            continue
        rows.append({headers[index]: row[index] for index in range(min(len(headers), len(row)))})
    return rows


def extract_pdf_text(data: bytes, max_pages: int = 10) -> str:
    from pypdf import PdfReader  # noqa: PLC0415

    reader = PdfReader(io.BytesIO(data))
    chunks: list[str] = []
    for page in reader.pages[:max_pages]:
        try:
            chunks.append(page.extract_text() or "")
        except Exception:  # pragma: no cover
            continue
    return "\n".join(chunk for chunk in chunks if chunk).strip()

