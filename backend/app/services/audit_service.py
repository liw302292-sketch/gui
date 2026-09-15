"""审计服务：记录谁改了什么、改前改后。"""

from __future__ import annotations

from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.logging import audit_log
from app.core.rate_limit import client_ip
from app.models.audit import AuditLog


def record(
    db: Session,
    *,
    company_id: int | None,
    user_id: int | None,
    user_name: str | None,
    action: str,
    target_type: str = "",
    target_id: int | None = None,
    summary: str | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    request: Request | None = None,
) -> AuditLog:
    entry = AuditLog(
        company_id=company_id,
        user_id=user_id,
        user_name=user_name,
        action=action,
        target_type=target_type,
        target_id=target_id,
        summary=summary,
        before=before or {},
        after=after or {},
        ip_address=client_ip(request) if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(entry)
    audit_log(action, company_id=company_id, user_id=user_id, detail=summary or "")
    return entry

