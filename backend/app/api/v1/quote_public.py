"""在线报价页接口：无需登录，通过随机 token 访问。"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request, Response

from app.core.deps import DbSession
from app.core.errors import AuthError, NotFoundError
from app.core.rate_limit import enforce_rate_limit
from app.models.company import Company
from app.services import pdf_service, quote_service

router = APIRouter()


@router.get("/{token}", response_model=dict, summary="查看公开报价")
def view_quote(
    token: str,
    db: DbSession,
    request: Request,
    password: str | None = Query(default=None),
    track: bool = Query(default=True),
) -> dict:
    enforce_rate_limit(request, bucket="public_quote", limit=120)
    quote = quote_service.get_quote_by_token(db, token)

    if quote.public_access_password_hash and not quote_service.verify_quote_password(quote, password):
        if password:
            raise AuthError("访问密码不正确")
        return {"ok": True, "data": {"requires_password": True, "quote": None, "company": None}}

    if track:
        quote_service.record_view(db, quote, request)

    company = db.get(Company, quote.company_id)
    payload = quote_service.quote_to_client_payload(quote, company=company, include_internal=False)
    return {
        "ok": True,
        "data": {
            "requires_password": False,
            "quote": payload,
            "company": payload.get("company"),
        },
    }


@router.get("/{token}/pdf", summary="下载公开报价单 PDF")
def download_public_pdf(token: str, db: DbSession, request: Request, password: str | None = None) -> Response:
    enforce_rate_limit(request, bucket="public_pdf", limit=60)
    quote = quote_service.get_quote_by_token(db, token)
    if not quote.allow_download:
        raise NotFoundError("该报价单不允许下载，请联系业务员")
    if not quote_service.verify_quote_password(quote, password):
        raise AuthError("访问密码不正确")

    company = db.get(Company, quote.company_id)
    payload = quote_service.quote_to_client_payload(quote, company=company, include_internal=False)
    pdf_bytes = pdf_service.quote_pdf(payload)
    if pdf_bytes:
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{quote.quote_no}.pdf"'},
        )
    return Response(
        content=pdf_service.build_quote_html(payload),
        media_type="text/html; charset=utf-8",
        headers={"X-PDF-Fallback": "print"},
    )


@router.post("/{token}/accept", response_model=dict, summary="客户确认报价（表达成交意向）")
def accept_quote(token: str, db: DbSession, request: Request) -> dict:
    enforce_rate_limit(request, bucket="public_accept", limit=20)
    quote = quote_service.get_quote_by_token(db, token)
    if quote.status not in ("won", "void"):
        quote_service.change_status(db, quote, "following")
        from app.models.customer import Notification  # noqa: PLC0415

        db.add(
            Notification(
                company_id=quote.company_id,
                user_id=quote.owner_user_id,
                type="quote_accepted",
                title="客户已确认报价",
                content=f"{quote.customer_name or '客户'} 在线确认了报价 {quote.quote_no}，请尽快跟进签约。",
                link=f"/app/quotes/{quote.id}",
            )
        )
        db.flush()
    return {"ok": True, "message": "已收到您的确认，业务员会尽快与您联系。"}

