"""报价接口：创建、识别结果确认、重算、发送、版本、审计、PDF。"""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Query, Request, Response
from sqlalchemy import func, or_, select

from app.core.config import settings
from app.core.deps import Context, DbSession, check_ai_quota
from app.core.errors import ConflictError, NotFoundError
from app.models.company import Company
from app.models.quote import Quote, QuoteItem, QuoteVersion
from app.schemas.common import Message
from app.schemas.quote import (
    QuoteCreateRequest,
    QuoteDetail,
    QuoteItemOut,
    QuoteListItem,
    QuoteRecalculateRequest,
    QuoteSendRequest,
    QuoteStatusRequest,
    QuoteUpdateRequest,
)
from app.services import audit_service, pdf_service, plan_service, quote_service
from app.services.pricing.schemas import QuoteItemInput

router = APIRouter()


def _get_quote(db: DbSession, context: Context, quote_id: int) -> Quote:
    quote = db.get(Quote, quote_id)
    if not quote or quote.company_id != context.company_id:
        raise NotFoundError("报价单不存在")
    return quote


def _item_out(item: QuoteItem) -> QuoteItemOut:
    return QuoteItemOut(
        id=item.id,
        product_id=item.product_id,
        category_name=item.category_name,
        product_name=item.product_name,
        spec=item.spec,
        unit=item.unit,
        quantity=float(item.quantity or 0),
        width=float(item.width) if item.width is not None else None,
        height=float(item.height) if item.height is not None else None,
        depth=float(item.depth) if item.depth is not None else None,
        unit_price=float(item.unit_price or 0),
        cost_price=float(item.cost_price or 0),
        material_cost=float(item.material_cost or 0),
        loss_cost=float(item.loss_cost or 0),
        labor_cost=float(item.labor_cost or 0),
        transport_cost=float(item.transport_cost or 0),
        other_cost=float(item.other_cost or 0),
        total_cost=float(item.total_cost or 0),
        subtotal=float(item.subtotal or 0),
        profit_margin=float(item.profit_margin or 0),
        final_price=float(item.final_price or 0),
        formula=item.formula,
        breakdown=item.breakdown or {},
        match_confidence=float(item.match_confidence) if item.match_confidence is not None else None,
        remark=item.remark,
    )


def _detail(quote: Quote) -> QuoteDetail:
    public_url = (
        f"{settings.app_url.rstrip('/')}/quote/{quote.public_token}" if quote.public_token else None
    )
    return QuoteDetail(
        id=quote.id,
        quote_no=quote.quote_no,
        version_no=quote.version_no,
        project_name=quote.project_name,
        customer_name=quote.customer_name,
        customer_id=quote.customer_id,
        status=quote.status,
        status_label=quote_service.QUOTE_STATUS_LABELS.get(quote.status, quote.status),
        currency=quote.currency,
        subtotal=float(quote.subtotal or 0),
        discount_amount=float(quote.discount_amount or 0),
        tax_rate=float(quote.tax_rate or 0),
        tax_amount=float(quote.tax_amount or 0),
        total_amount=float(quote.total_amount or 0),
        total_cost=float(quote.total_cost or 0),
        gross_profit=float(quote.gross_profit or 0),
        gross_margin=float(quote.gross_margin or 0),
        tiers=quote.tiers or {},
        notes=quote.notes,
        payment_terms=quote.payment_terms,
        service_terms=quote.service_terms,
        requirement_text=quote.requirement_text,
        requirement_json=quote.requirement_json or {},
        missing_fields=quote.missing_fields or [],
        confidence=float(quote.confidence) if quote.confidence is not None else None,
        valid_until=quote.valid_until,
        public_token=quote.public_token,
        public_url=public_url,
        allow_download=quote.allow_download,
        view_count=quote.view_count,
        first_viewed_at=quote.first_viewed_at,
        last_viewed_at=quote.last_viewed_at,
        created_at=quote.created_at,
        sent_at=quote.sent_at,
        won_at=quote.won_at,
        items=[_item_out(item) for item in quote.items],
    )


@router.get("", response_model=dict, summary="报价列表")
def list_quotes(
    context: Context,
    db: DbSession,
    keyword: str | None = None,
    status: str | None = None,
    customer_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
) -> dict:
    stmt = select(Quote).where(Quote.company_id == context.company_id)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            or_(Quote.quote_no.ilike(like), Quote.project_name.ilike(like), Quote.customer_name.ilike(like))
        )
    if status:
        stmt = stmt.where(Quote.status == status)
    if customer_id:
        stmt = stmt.where(Quote.customer_id == customer_id)

    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    quotes = list(
        db.scalars(stmt.order_by(Quote.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    )
    item_counts = dict(
        db.execute(
            select(QuoteItem.quote_id, func.count(QuoteItem.id))
            .where(QuoteItem.quote_id.in_([quote.id for quote in quotes] or [0]))
            .group_by(QuoteItem.quote_id)
        ).all()
    )

    stats = db.execute(
        select(
            func.count(Quote.id),
            func.coalesce(func.sum(Quote.total_amount), 0),
            func.coalesce(func.sum(Quote.total_cost), 0),
        ).where(Quote.company_id == context.company_id)
    ).one()
    won = db.execute(
        select(
            func.count(Quote.id),
            func.coalesce(func.sum(Quote.total_amount), 0),
        ).where(Quote.company_id == context.company_id, Quote.status == "won")
    ).one()

    return {
        "ok": True,
        "data": {
            "items": [
                QuoteListItem(
                    id=quote.id,
                    quote_no=quote.quote_no,
                    project_name=quote.project_name,
                    customer_name=quote.customer_name,
                    customer_id=quote.customer_id,
                    status=quote.status,
                    status_label=quote_service.QUOTE_STATUS_LABELS.get(quote.status, quote.status),
                    total_amount=float(quote.total_amount or 0),
                    total_cost=float(quote.total_cost or 0),
                    gross_margin=float(quote.gross_margin or 0),
                    version_no=quote.version_no,
                    view_count=quote.view_count,
                    item_count=int(item_counts.get(quote.id, 0)),
                    created_at=quote.created_at,
                    valid_until=quote.valid_until,
                    last_viewed_at=quote.last_viewed_at,
                    public_token=quote.public_token,
                    source=quote.requirement_json.get("source") if quote.requirement_json else None,
                ).model_dump()
                for quote in quotes
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "summary": {
                "quote_count": int(stats[0] or 0),
                "quote_amount": float(stats[1] or 0),
                "total_cost": float(stats[2] or 0),
                "won_count": int(won[0] or 0),
                "won_amount": float(won[1] or 0),
            },
        },
    }


@router.post("", response_model=dict, summary="创建报价（AI 识别结果确认后调用）")
def create_quote(payload: QuoteCreateRequest, context: Context, db: DbSession, request: Request) -> dict:
    plan_service.enforce_plan_limits(db, context.company_id, context.plan)
    if not payload.items:
        raise ConflictError("报价项目不能为空，请先补充产品与数量")

    requirement = payload.model_dump(exclude={"rounding_mode", "tax_rate", "discount_amount", "global_margin"})
    requirement["source"] = "ai" if payload.requirement_text else "manual"

    quote = quote_service.create_quote(
        db,
        company_id=context.company_id,
        user_id=context.user_id,
        requirement=requirement,
        requirement_text=payload.requirement_text or "",
        customer_id=payload.customer_id,
        customer_name=payload.customer_name,
        template_id=payload.template_id,
        project_name=payload.project_name,
        industry_id=payload.industry_id or context.company.industry_id,
        source="ai" if payload.requirement_text else "manual",
    )
    if payload.rounding_mode or payload.tax_rate is not None or payload.discount_amount is not None or payload.global_margin is not None:
        quote_service.recalculate(
            db,
            quote=quote,
            item_inputs=quote_service.requirement_items_to_input(requirement),
            rounding_mode=payload.rounding_mode,
            tax_rate=Decimal(str(payload.tax_rate)) if payload.tax_rate is not None else None,
            discount_amount=Decimal(str(payload.discount_amount)) if payload.discount_amount is not None else None,
            global_margin=Decimal(str(payload.global_margin)) if payload.global_margin is not None else None,
        )
    quote_service.touch_customer_quote_stats(db, quote.customer_id)

    audit_service.record(
        db,
        company_id=context.company_id,
        user_id=context.user_id,
        user_name=context.user.name,
        action="quote.create",
        target_type="quote",
        target_id=quote.id,
        summary=f"创建报价 {quote.quote_no}，金额 ¥{float(quote.total_amount or 0):,.2f}",
        after={"total_amount": float(quote.total_amount or 0)},
        request=request,
    )
    return {"ok": True, "message": "报价已生成", "data": _detail(quote).model_dump()}


@router.get("/{quote_id}", response_model=dict, summary="报价详情（含成本明细）")
def get_quote(quote_id: int, context: Context, db: DbSession) -> dict:
    quote = _get_quote(db, context, quote_id)
    return {"ok": True, "data": _detail(quote).model_dump()}


@router.put("/{quote_id}", response_model=dict, summary="更新报价（人工校正后重新计算）")
def update_quote(
    quote_id: int, payload: QuoteUpdateRequest, context: Context, db: DbSession, request: Request
) -> dict:
    quote = _get_quote(db, context, quote_id)
    before = {"total_amount": float(quote.total_amount or 0)}

    item_inputs = None
    if payload.items is not None:
        item_inputs = [
            QuoteItemInput(
                product_id=item.product_id,
                product_name=item.product_name,
                category_name=item.category,
                spec=item.spec,
                unit=item.unit,
                quantity=item.quantity,
                width=item.width,
                height=item.height,
                depth=item.depth,
                weight=item.weight,
                unit_price=item.unit_price,
                cost_price=item.cost_price,
                loss_rate=item.loss_rate,
                labor_cost=item.labor_cost,
                transport_cost=item.transport_cost,
                other_cost=item.other_cost,
                remark=item.remark,
            )
            for item in payload.items
        ]

    fields = payload.model_dump(
        exclude={"items", "change_note"}, exclude_unset=True
    )
    if fields.get("customer_id"):
        quote.customer_id = fields["customer_id"]
        quote.customer_name = payload.customer_name

    quote_service.update_quote(
        db,
        quote=quote,
        user_id=context.user_id,
        item_inputs=item_inputs,
        fields=fields,
        change_note=payload.change_note,
    )
    audit_service.record(
        db,
        company_id=context.company_id,
        user_id=context.user_id,
        user_name=context.user.name,
        action="quote.update",
        target_type="quote",
        target_id=quote.id,
        summary=f"修改报价 {quote.quote_no}：¥{before['total_amount']:,.2f} → ¥{float(quote.total_amount or 0):,.2f}",
        before=before,
        after={"total_amount": float(quote.total_amount or 0)},
        request=request,
    )
    return {"ok": True, "message": "报价已更新", "data": _detail(quote).model_dump()}


@router.post("/{quote_id}/recalculate", response_model=dict, summary="重新计算报价")
def recalculate(quote_id: int, payload: QuoteRecalculateRequest, context: Context, db: DbSession) -> dict:
    quote = _get_quote(db, context, quote_id)
    item_inputs = [
        QuoteItemInput(
            product_id=item.product_id,
            product_name=item.product_name,
            category_name=item.category,
            spec=item.spec,
            unit=item.unit,
            quantity=item.quantity,
            width=item.width,
            height=item.height,
            depth=item.depth,
            weight=item.weight,
            unit_price=item.unit_price,
            cost_price=item.cost_price,
            loss_rate=item.loss_rate,
            labor_cost=item.labor_cost,
            transport_cost=item.transport_cost,
            other_cost=item.other_cost,
            remark=item.remark,
        )
        for item in payload.items
    ]
    quote_service.recalculate(
        db,
        quote=quote,
        item_inputs=item_inputs,
        rounding_mode=payload.rounding_mode,
        tax_rate=Decimal(str(payload.tax_rate)) if payload.tax_rate is not None else None,
        discount_amount=Decimal(str(payload.discount_amount)) if payload.discount_amount is not None else None,
        global_margin=Decimal(str(payload.global_margin)) if payload.global_margin is not None else None,
    )
    return {"ok": True, "message": "已按最新规则重新计算", "data": _detail(quote).model_dump()}


@router.post("/{quote_id}/send", response_model=dict, summary="生成公开报价链接")
def send_quote(quote_id: int, payload: QuoteSendRequest, context: Context, db: DbSession) -> dict:
    quote = _get_quote(db, context, quote_id)
    url = quote_service.mark_sent(db, quote, valid_days=payload.valid_days, password=payload.password)
    audit_service.record(
        db,
        company_id=context.company_id,
        user_id=context.user_id,
        user_name=context.user.name,
        action="quote.send",
        target_type="quote",
        target_id=quote.id,
        summary=f"发送报价 {quote.quote_no}",
    )
    return {
        "ok": True,
        "message": "公开报价链接已生成",
        "data": {
            "public_token": quote.public_token,
            "public_url": url,
            "expires_at": quote.public_token_expires_at.isoformat() if quote.public_token_expires_at else None,
            "requires_password": bool(quote.public_access_password_hash),
        },
    }


@router.post("/{quote_id}/status", response_model=dict, summary="变更报价状态")
def change_status(quote_id: int, payload: QuoteStatusRequest, context: Context, db: DbSession) -> dict:
    quote = _get_quote(db, context, quote_id)
    quote_service.change_status(db, quote, payload.status, user_id=context.user_id, note=payload.note)
    audit_service.record(
        db,
        company_id=context.company_id,
        user_id=context.user_id,
        user_name=context.user.name,
        action="quote.status",
        target_type="quote",
        target_id=quote.id,
        summary=f"报价 {quote.quote_no} 状态变更为 {payload.status}",
        after={"status": payload.status},
    )
    return {"ok": True, "message": "状态已更新", "data": _detail(quote).model_dump()}


@router.get("/{quote_id}/versions", response_model=dict, summary="报价版本历史")
def versions(quote_id: int, context: Context, db: DbSession) -> dict:
    quote = _get_quote(db, context, quote_id)
    items = quote_service.list_quote_versions(db, quote)
    snapshot = db.scalar(
        select(QuoteVersion.snapshot).where(QuoteVersion.quote_id == quote.id).order_by(QuoteVersion.version_no.desc()).limit(1)
    )
    return {"ok": True, "data": {"versions": items, "latest_snapshot": snapshot or {}}}


@router.get("/{quote_id}/audit", response_model=dict, summary="报价审计日志")
def audit_trail(quote_id: int, context: Context, db: DbSession) -> dict:
    from app.models.audit import AuditLog  # noqa: PLC0415

    _get_quote(db, context, quote_id)
    logs = list(
        db.scalars(
            select(AuditLog)
            .where(
                AuditLog.company_id == context.company_id,
                AuditLog.target_type == "quote",
                AuditLog.target_id == quote_id,
            )
            .order_by(AuditLog.created_at.desc())
            .limit(100)
        )
    )
    return {
        "ok": True,
        "data": [
            {
                "id": log.id,
                "action": log.action,
                "user_name": log.user_name,
                "summary": log.summary,
                "before": log.before,
                "after": log.after,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }


@router.get("/{quote_id}/pdf", summary="下载报价单 PDF")
def download_pdf(quote_id: int, context: Context, db: DbSession) -> Response:
    quote = _get_quote(db, context, quote_id)
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


@router.delete("/{quote_id}", response_model=Message, summary="作废报价")
def void_quote(quote_id: int, context: Context, db: DbSession) -> Message:
    quote = _get_quote(db, context, quote_id)
    quote.status = "void"
    db.flush()
    audit_service.record(
        db,
        company_id=context.company_id,
        user_id=context.user_id,
        user_name=context.user.name,
        action="quote.void",
        target_type="quote",
        target_id=quote.id,
        summary=f"作废报价 {quote.quote_no}",
    )
    return Message(message="报价已作废")

