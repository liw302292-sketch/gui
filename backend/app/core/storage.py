"""文件存储抽象：local（默认）/ s3 兼容对象存储。

安全约束：上传文件的真实路径永不返回给前端，一律通过后端鉴权接口访问。
"""

from __future__ import annotations

import hashlib
import logging
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger("quote_engine.app")

SAFE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf", ".xlsx", ".xls", ".csv", ".txt"}
BLOCKED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".sh", ".ps1", ".js", ".vbs", ".jar", ".msi", ".dll", ".php", ".py", ".html", ".htm", ".svg",
}
ALLOWED_MIME_PREFIXES = ("image/", "application/pdf", "application/vnd.openxmlformats", "application/vnd.ms-excel", "text/csv", "text/plain")

MAX_UPLOAD_BYTES = settings.max_upload_mb * 1024 * 1024


class StorageError(Exception):
    """存储层异常（由 file_service 转换为友好业务错误）。"""


def sanitize_filename(filename: str) -> str:
    """文件名清洗：去掉路径、控制字符与危险字符。"""
    name = Path(filename or "file").name
    name = re.sub(r"[\\/:\*\?\"<>\|\x00-\x1f]", "_", name)
    name = name.strip(". ")
    if not name:
        name = "file"
    return name[:180]


def validate_upload(filename: str, content_type: str | None, size: int) -> str:
    """校验扩展名 / MIME / 大小，返回安全扩展名。"""
    safe_name = sanitize_filename(filename)
    extension = Path(safe_name).suffix.lower()
    if extension in BLOCKED_EXTENSIONS:
        raise StorageError("该文件类型不被支持，请上传图片、PDF 或 Excel 文件")
    if extension not in SAFE_EXTENSIONS:
        raise StorageError("仅支持 JPG / PNG / WEBP / GIF / PDF / XLSX / CSV 文件")
    if size <= 0:
        raise StorageError("上传的文件是空文件")
    if size > MAX_UPLOAD_BYTES:
        raise StorageError(f"文件大小不能超过 {settings.max_upload_mb} MB")
    if content_type and not content_type.lower().startswith(ALLOWED_MIME_PREFIXES):
        raise StorageError("文件内容类型不被支持")
    return extension


@dataclass
class StoredObject:
    key: str
    backend: str
    size: int
    checksum: str


class LocalStorage:
    backend = "local"

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or settings.storage_dir

    def _absolute(self, key: str) -> Path:
        candidate = (self.base_dir / key).resolve()
        base = self.base_dir.resolve()
        if not str(candidate).startswith(str(base)):
            raise StorageError("非法的存储路径")
        return candidate

    def save(self, *, company_id: int, filename: str, data: bytes) -> StoredObject:
        extension = Path(filename).suffix.lower()
        key = f"company_{company_id}/{uuid.uuid4().hex}{extension}"
        target = self._absolute(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return StoredObject(
            key=key,
            backend=self.backend,
            size=len(data),
            checksum=hashlib.sha256(data).hexdigest()[:32],
        )

    def read(self, key: str) -> bytes:
        return self._absolute(key).read_bytes()

    def delete(self, key: str) -> None:
        try:
            self._absolute(key).unlink(missing_ok=True)
        except OSError as exc:  # pragma: no cover
            logger.warning("删除本地文件失败 %s: %s", key, exc)

    def exists(self, key: str) -> bool:
        return self._absolute(key).exists()

    @property
    def quota_used_mb(self) -> float:  # pragma: no cover - 运维辅助
        total = sum(path.stat().st_size for path in self.base_dir.rglob("*") if path.is_file())
        return round(total / 1024 / 1024, 2)


class S3Storage:
    """S3 兼容对象存储（MinIO / 阿里云 OSS / 腾讯云 COS）。"""

    backend = "s3"

    def __init__(self) -> None:
        import boto3  # noqa: PLC0415

        self.client = boto3.client(
            "s3",
            endpoint_url=settings.storage_endpoint or None,
            region_name=settings.storage_region,
            aws_access_key_id=settings.storage_access_key or None,
            aws_secret_access_key=settings.storage_secret_key or None,
        )
        self.bucket = settings.storage_bucket

    def save(self, *, company_id: int, filename: str, data: bytes) -> StoredObject:
        extension = Path(filename).suffix.lower()
        key = f"company_{company_id}/{uuid.uuid4().hex}{extension}"
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data)
        return StoredObject(key=key, backend=self.backend, size=len(data), checksum=hashlib.sha256(data).hexdigest()[:32])

    def read(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()

    def delete(self, key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except Exception as exc:  # pragma: no cover
            logger.warning("删除对象存储文件失败 %s: %s", key, exc)

    def exists(self, key: str) -> bool:  # pragma: no cover
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    @property
    def quota_used_mb(self) -> float:  # pragma: no cover
        return 0.0


def get_storage() -> LocalStorage | S3Storage:
    if settings.storage_backend == "s3" and settings.storage_access_key:
        try:
            return S3Storage()
        except Exception as exc:  # pragma: no cover
            logger.warning("S3 初始化失败，回退本地存储：%s", exc)
    return LocalStorage()


storage = get_storage()

