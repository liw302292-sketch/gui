"""文件接口：上传、鉴权读取、删除。真实存储路径永不暴露。"""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, Request, Response, UploadFile
from sqlalchemy import func, select

from app.core.deps import Context, DbSession
from app.core.errors import NotFoundError
from app.core.rate_limit import enforce_rate_limit
from app.core.storage import get_storage
from app.models.file import StoredFile
from app.schemas.common import Message
from app.services import file_service

logger = logging.getLogger("quote_engine.app")

router = APIRouter()

MIME_BY_EXT = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".csv": "text/csv",
    ".txt": "text/plain; charset=utf-8",
}


@router.post("/upload", response_model=dict, summary="上传文件（图片/PDF/Excel）")
async def upload(
    context: Context,
    db: DbSession,
    request: Request,
    file: UploadFile = File(...),
) -> dict:
    enforce_rate_limit(request, bucket="upload", limit=120)
    data = await file.read()
    record = file_service.save_upload(
        db,
        company_id=context.company_id,
        user_id=context.user_id,
        filename=file.filename or "upload.bin",
        content_type=file.content_type,
        data=data,
    )
    return {
        "ok": True,
        "message": "文件上传成功",
        "data": {
            "id": record.id,
            "name": record.original_name,
            "kind": record.kind,
            "size": record.size,
            "url": f"/api/files/{record.id}",
        },
    }


@router.get("", response_model=dict, summary="文件列表")
def list_files(context: Context, db: DbSession, kind: str | None = None, limit: int = 50) -> dict:
    stmt = select(StoredFile).where(StoredFile.company_id == context.company_id)
    if kind:
        stmt = stmt.where(StoredFile.kind == kind)
    files = list(db.scalars(stmt.order_by(StoredFile.created_at.desc()).limit(min(limit, 200))))
    total_size = db.scalar(
        select(func.coalesce(func.sum(StoredFile.size), 0)).where(StoredFile.company_id == context.company_id)
    ) or 0
    return {
        "ok": True,
        "data": {
            "items": [
                {
                    "id": item.id,
                    "name": item.original_name,
                    "kind": item.kind,
                    "size": item.size,
                    "content_type": item.content_type,
                    "url": f"/api/files/{item.id}",
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                }
                for item in files
            ],
            "total_size": int(total_size),
            "quota_mb": context.plan.storage_quota_mb if context.plan else 200,
        },
    }


@router.get("/storage/info", response_model=dict, summary="存储使用情况")
def storage_info(context: Context, db: DbSession) -> dict:
    used = db.scalar(
        select(func.coalesce(func.sum(StoredFile.size), 0)).where(StoredFile.company_id == context.company_id)
    ) or 0
    quota_mb = context.plan.storage_quota_mb if context.plan else 200
    return {
        "ok": True,
        "data": {
            "backend": get_storage().backend,
            "used_bytes": int(used),
            "used_mb": round(int(used) / 1024 / 1024, 2),
            "quota_mb": quota_mb,
            "usage_ratio": round(int(used) / 1024 / 1024 / quota_mb, 4) if quota_mb else 0,
        },
    }


@router.get("/{file_id}", summary="读取文件（企业隔离 + 鉴权）")
def read(file_id: int, context: Context, db: DbSession) -> Response:
    record = file_service.get_file(db, context.company_id, file_id)
    data = file_service.read_file(record)
    content_type = record.content_type or MIME_BY_EXT.get(record.extension, "application/octet-stream")
    headers = {"Cache-Control": "private, max-age=3600"}
    if record.kind != "image":
        headers["Content-Disposition"] = f'inline; filename="{record.original_name}"'
    return Response(content=data, media_type=content_type, headers=headers)


@router.delete("/{file_id}", response_model=Message, summary="删除文件")
def delete(file_id: int, context: Context, db: DbSession) -> Message:
    record = db.get(StoredFile, file_id)
    if not record or record.company_id != context.company_id:
        raise NotFoundError("文件不存在")
    file_service.delete_file(db, record)
    return Message(message="文件已删除")
