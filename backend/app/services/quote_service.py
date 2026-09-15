"""报价业务服务：需求 → 规则引擎计算 → 报价单 → 版本 → 公开链接 → 访问追踪。"""

from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal
from typing import Any

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ConflictError, NotFoundError
from app.core.rate_limit import client_ip, hash_ip
from app.core.security import generate_public_token, hash_password, verify_password
from app.models.base import utcnow
from app.models.company import Company
from app.models.customer import Customer, Followup, Notification
from app.models.quote import Quote, QuoteItem, QuoteTemplate, QuoteVersion, QuoteView
from app.services import numbering
from app.services.pricing.pricing_engine import pricing_engine
from app.services.pricing.schemas import QuoteInput, QuoteItemInput

logger = logging.getLogger("quote_engine.app")

TIER_LABELS = {"economy": "经济版", "standard": "标准版", "premium": "高级版"}
QUOTE_STATUS_LABELS = {
    "draft": "草稿",
    "sent": "已发送",
    "viewed": "已查看",
    "following": "待跟进",
    "won": "已成交",
    "void": "已作废",
}


# ----------------------------------------------------------------------
# 需求 → 报价项输入
# ----------------------------------------------------------------------
def requirement_items_to_input(requirement: dict[str, Any]) -> list[QuoteItemInput]:
    items: list[QuoteItemInput] = []
    for raw in requirement.get("items") or []:
        unit = raw.get("unit") or "平方米"
        items.append(
            QuoteItemInput(
                product_id=raw.get("product_id"),
                product_name=raw.get("product_name") or raw.get("category") or "未命名产品",
                category_name=raw.get("category"),
                spec=raw.get("spec"),
                unit=unit,
                quantity=raw.get("quantity") or 1,
                width=raw.get("width"),
                height=raw.get("height"),
                depth=raw.get("depth"),
                weight=raw.get("weight"),
                unit_price=raw.get("unit_price"),
                cost_price=raw.get("cost_price"),
                loss_rate=raw.get("loss_rate"),
                labor_cost=raw.get("labor_cost"),
                transport_cost=raw.get("transport_cost"),
                other_cost=raw.get("other_cost"),
                remark=raw.get("remark"),
                match_confidence=raw.get("match_confidence"),
            )
        )
    return items


def _apply_items(db: Session, quote: Quote, calculation) -> None:  # noqa: ANN001
    for existing in list(quote.items):
        db.delete(existing)
    db.flush()
    for index, item in enumerate(calculation.items):
        quote.items.append(
            QuoteItem(
                company_id=quote.company_id,
                product_id=item.product_id,
                plan_level=item.plan_level,
                category_name=item.category_name,
                product_name=item.product_name,
                spec=item.spec,
                unit=item.unit,
                quantity=item.quantity,
                width=item.width,
                height=item.height,
                depth=item.depth,
                weight=item.weight,
                unit_price=item.unit_price,
                cost_price=item.cost_price,
                material_cost=item.material_cost,
                loss_rate=item.loss_rate,
                loss_cost=item.loss_cost,
                labor_cost=item.labor_cost,
                transport_cost=item.transport_cost,
                other_cost=item.other_cost,
                total_cost=item.total_cost,
                subtotal=item.subtotal,
                profit_margin=item.profit_margin,
                final_price=item.final_price,
                rounding_adjustment=item.rounding_adjustment,
                formula=item.formula,
                breakdown=item.breakdown,
                match_confidence=item.match_confidence,
                remark=item.remark,
                sort_order=index,
            )
        )


def recalculate(
    db: Session,
    *,
    quote: Quote,
    item_inputs: list[QuoteItemInput],
    rounding_mode: str | None = None,
    tax_rate: Decimal | None = None,
    discount_amount: Decimal | None = None,
    global_margin: Decimal | None = None,
    tier: str = "standard",
    with_tiers: bool = True,
) -> Quote:
    """重新计算报价。价格永远由规则引擎产生。"""
    company = db.get(Company, quote.company_id)
    rounding_mode = rounding_mode or (company.rounding_mode if company else "10")

    payload = QuoteInput(
        items=item_inputs,
        rounding_mode=rounding_mode,
        discount_amount=discount_amount if discount_amount is not None else Decimal(str(quote.discount_amount or 0)),
        tax_rate=tax_rate if tax_rate is not None else Decimal(str(quote.tax_rate or 0)),
        global_margin=global_margin,
    )

    calculation = pricing_engine.calculate(db, quote.company_id, payload, tier=tier)

    if with_tiers:
        tier_results = pricing_engine.calculate_tiers(db, quote.company_id, payload)
        quote.tiers = {
            level: {
                "level": level,
                "name": result.name,
                "total_amount": float(result.total_amount),
                "total_cost": float(result.total_cost),
                "gross_margin": float(result.gross_margin),
            }
            for level, result in tier_results.items()
        }

    _apply_items(db, quote, calculation)
    quote.subtotal = calculation.subtotal
    quote.discount_amount = calculation.discount_amount
    quote.tax_rate = calculation.tax_rate
    quote.tax_amount = calculation.tax_amount
    quote.total_amount = calculation.total_amount
    quote.total_cost = calculation.total_cost
    quote.gross_profit = calculation.gross_profit
    quote.gross_margin = calculation.gross_margin
    db.flush()
    return quote


def create_quote(
    db: Session,
    *,
    company_id: int,
    user_id: int | None,
    requirement: dict[str, Any],
    requirement_text: str = "",
    customer_id: int | None = None,
    template_id: int | None = None,
    project_name: str | None = None,
    customer_name: str | None = None,
    ai_task_id: int | None = None,
    industry_id: str = "advertising",
    source: str = "manual",
) -> Quote:
    company = db.get(Company, company_id)
    if company is None:
        raise NotFoundError("企业不存在")

    if customer_name and not customer_id:
        customer = db.scalar(
            select(Customer).where(Customer.company_id == company_id, Customer.name == customer_name).limit(1)
        )
        if customer is None:
            customer = Customer(
                company_id=company_id,
                name=customer_name,
                status="new",
                source="AI识别",
                owner_user_id=user_id,
            )
            db.add(customer)
            db.flush()
        customer_id = customer.id

    template = None
    if template_id:
        template = db.get(QuoteTemplate, template_id)
    if template is None:
        template = db.scalar(
            select(QuoteTemplate)
            .where(QuoteTemplate.company_id == company_id)
            .order_by(QuoteTemplate.is_default.desc(), QuoteTemplate.id.asc())
        )

    quote = Quote(
        company_id=company_id,
        industry_id=industry_id,
        customer_id=customer_id,
        template_id=template.id if template else None,
        owner_user_id=user_id,
        ai_task_id=ai_task_id,
        quote_no=numbering.generate_quote_no(db, company_id),
        project_name=project_name or requirement.get("project_name") or "未命名项目",
        customer_name=customer_name or requirement.get("customer_name"),
        status="draft",
        notes=None,
        requirement_text=requirement_text,
        requirement_json=requirement,
        missing_fields=requirement.get("missing_fields") or [],
        confidence=requirement.get("confidence"),
        payment_terms=template.payment_terms if template else company.default_payment_terms,
        service_terms=template.service_terms if template else company.default_service_terms,
        valid_until=utcnow() + timedelta(days=company.default_quote_valid_days or 15),
        public_token=None,
    )
    db.add(quote)
    db.flush()

    item_inputs = requirement_items_to_input(requirement)
    if not item_inputs:
        raise ConflictError("需求中没有可报价的项目，请先补充产品与数量信息")

    recalculate(db, quote=quote, item_inputs=item_inputs)
    _create_version(db, quote, user_id=user_id, change_note="创建报价")
    db.flush()
    logger.info("报价已创建 company=%s quote_no=%s source=%s", company_id, quote.quote_no, source)
    return quote


def _snapshot(quote: Quote) -> dict[str, Any]:
    return {
        "quote_no": quote.quote_no,
        "project_name": quote.project_name,
        "customer_name": quote.customer_name,
        "status": quote.status,
        "total_amount": float(quote.total_amount or 0),
        "total_cost": float(quote.total_cost or 0),
        "gross_profit": float(quote.gross_profit or 0),
        "gross_margin": float(quote.gross_margin or 0),
        "tiers": quote.tiers,
        "items": [
            {
                "product_name": item.product_name,
                "category_name": item.category_name,
                "spec": item.spec,
                "unit": item.unit,
                "quantity": float(item.quantity or 0),
                "width": float(item.width) if item.width is not None else None,
                "height": float(item.height) if item.height is not None else None,
                "unit_price": float(item.unit_price or 0),
                "cost_price": float(item.cost_price or 0),
                "total_cost": float(item.total_cost or 0),
                "final_price": float(item.final_price or 0),
                "profit_margin": float(item.profit_margin or 0),
                "formula": item.formula,
                "breakdown": item.breakdown,
            }
            for item in quote.items
        ],
    }


def _create_version(db: Session, quote: Quote, *, user_id: int | None, change_note: str | None) -> QuoteVersion:
    latest = db.scalar(
        select(func.max(QuoteVersion.version_no)).where(QuoteVersion.quote_id == quote.id)
    ) or 0
    version = QuoteVersion(
        company_id=quote.company_id,
        quote_id=quote.id,
        version_no=int(latest) + 1,
        total_amount=quote.total_amount,
        total_cost=quote.total_cost,
        gross_margin=quote.gross_margin,
        tiers=quote.tiers,
        snapshot=_snapshot(quote),
        change_note=change_note,
        created_by=user_id,
    )
    db.add(version)
    quote.version_no = version.version_no
    db.flush()
    return version


def update_quote(
    db: Session,
    *,
    quote: Quote,
    user_id: int | None,
    item_inputs: list[QuoteItemInput] | None = None,
    fields: dict[str, Any] | None = None,
    change_note: str | None = None,
) -> Quote:
    """修改报价：字段更新 + 重新计算 + 生成新版本。"""
    fields = fields or {}
    before = _snapshot(quote)

    for key in ("project_name", "notes", "payment_terms", "service_terms", "customer_name", "status"):
        if key in fields and fields[key] is not None:
            setattr(quote, key, fields[key])
    if "valid_until" in fields and fields["valid_until"]:
        quote.valid_until = fields["valid_until"]
    if "allow_download" in fields and fields["allow_download"] is not None:
        quote.allow_download = bool(fields["allow_download"])

    if item_inputs is not None:
        recalculate(
            db,
            quote=quote,
            item_inputs=item_inputs,
            rounding_mode=fields.get("rounding_mode"),
            tax_rate=fields.get("tax_rate"),
            discount_amount=fields.get("discount_amount"),
            global_margin=fields.get("global_margin"),
        )
    db.flush()

    after = _snapshot(quote)
    if before != after:
        _create_version(db, quote, user_id=user_id, change_note=change_note or "修改报价")
    db.flush()
    return quote


def mark_sent(db: Session, quote: Quote, *, valid_days: int | None = None, password: str | None = None) -> str:
    """发送报价：生成公开 token（随机、不可预测），返回公开链接。"""
    token = quote.public_token or generate_public_token()
    quote.public_token = token
    company = db.get(Company, quote.company_id)
    days = valid_days or (company.default_quote_valid_days if company else 15) or 15
    quote.public_token_expires_at = utcnow() + timedelta(days=days)
    if valid_days:
        quote.valid_until = utcnow() + timedelta(days=valid_days)
    quote.sent_at = quote.sent_at or utcnow()
    if password:
        quote.public_access_password_hash = hash_password(password)
    if quote.status == "draft":
        quote.status = "sent"
    db.flush()
    return f"{settings.app_url.rstrip('/')}/quote/{token}"


def ensure_public_token(db: Session, quote: Quote, *, valid_days: int | None = None) -> str:
    if not quote.public_token:
        mark_sent(db, quote, valid_days=valid_days)
    return f"{settings.app_url.rstrip('/')}/quote/{quote.public_token}"


def get_quote_by_token(db: Session, token: str) -> Quote:
    quote = db.scalar(select(Quote).where(Quote.public_token == token))
    if not quote:
        raise NotFoundError("报价单不存在或链接已失效")
    if quote.public_token_expires_at and quote.public_token_expires_at < utcnow():
        raise NotFoundError("报价单已过期，请联系您的业务员重新获取")
    if quote.status == "void":
        raise NotFoundError("该报价单已作废")
    return quote


def verify_quote_password(quote: Quote, password: str | None) -> bool:
    if not quote.public_access_password_hash:
        return True
    if not password:
        return False
    return verify_password(password, quote.public_access_password_hash)


def _device_type(user_agent: str | None) -> str:
    agent = (user_agent or "").lower()
    if "ipad" in agent or "tablet" in agent:
        return "tablet"
    if any(keyword in agent for keyword in ("iphone", "android", "micromessenger", "mobile")):
        return "mobile"
    if agent:
        return "desktop"
    return "unknown"


def record_view(db: Session, quote: Quote, request: Request | None = None) -> QuoteView:
    """记录客户查看行为：首次/最近时间、次数、设备类型。"""
    is_first = quote.view_count == 0
    now = utcnow()
    quote.view_count = (quote.view_count or 0) + 1
    quote.first_viewed_at = quote.first_viewed_at or now
    quote.last_viewed_at = now
    if quote.status in ("sent", "draft"):
        quote.status = "viewed"

    user_agent = request.headers.get("user-agent") if request else None
    view = QuoteView(
        company_id=quote.company_id,
        quote_id=quote.id,
        version_no=quote.version_no,
        viewed_at=now,
        ip_hash=hash_ip(client_ip(request)) if request else None,
        user_agent=user_agent,
        device_type=_device_type(user_agent),
        referer=request.headers.get("referer") if request else None,
        is_first_view=is_first,
    )
    db.add(view)

    if is_first:
        db.add(
            Notification(
                company_id=quote.company_id,
                user_id=quote.owner_user_id,
                type="quote_viewed",
                title="客户查看了报价",
                content=f"{quote.customer_name or '客户'} 查看了报价单 {quote.quote_no}",
                link=f"/app/quotes/{quote.id}",
                meta={"quote_id": quote.id, "device": view.device_type},
            )
        )
    db.flush()
    return view


def change_status(
    db: Session, quote: Quote, status: str, *, user_id: int | None = None, note: str | None = None
) -> Quote:
    if status not in QUOTE_STATUS_LABELS:
        raise ConflictError("报价状态不合法")
    quote.status = status
    if status == "won" and not quote.won_at:
        quote.won_at = utcnow()
        _on_won(db, quote)
    if note:
        quote.notes = (quote.notes or "") + f"\n[{utcnow():%Y-%m-%d %H:%M}] {note}"
    db.flush()
    return quote


def _on_won(db: Session, quote: Quote) -> None:
    """成交后更新客户统计。"""
    if not quote.customer_id:
        return
    customer = db.get(Customer, quote.customer_id)
    if not customer:
        return
    customer.deal_count = (customer.deal_count or 0) + 1
    customer.total_amount = (customer.total_amount or 0) + (quote.total_amount or 0)
    customer.status = "won"
    customer.last_contact_at = utcnow()


def touch_customer_quote_stats(db: Session, customer_id: int | None) -> None:
    if not customer_id:
        return
    customer = db.get(Customer, customer_id)
    if not customer:
        return
    customer.quote_count = (customer.quote_count or 0) + 1
    customer.last_contact_at = utcnow()
    if customer.status == "new":
        customer.status = "quoted"


# ----------------------------------------------------------------------
# 序列化
# ----------------------------------------------------------------------
def quote_to_client_payload(
    quote: Quote, *, company: Company | None = None, include_internal: bool = False
) -> dict[str, Any]:
    """客户端payload：绝不包含成本、利润率、毛利。"""
    payload: dict[str, Any] = {
        "id": quote.id,
        "quote_no": quote.quote_no,
        "version_no": quote.version_no,
        "project_name": quote.project_name,
        "customer_name": quote.customer_name,
        "status": quote.status,
        "status_label": QUOTE_STATUS_LABELS.get(quote.status, quote.status),
        "currency": quote.currency,
        "subtotal": float(quote.subtotal or 0),
        "discount_amount": float(quote.discount_amount or 0),
        "tax_rate": float(quote.tax_rate or 0),
        "tax_amount": float(quote.tax_amount or 0),
        "total_amount": float(quote.total_amount or 0),
        "tiers": quote.tiers or {},
        "items": [
            {
                "id": item.id,
                "product_name": item.product_name,
                "category_name": item.category_name,
                "spec": item.spec,
                "unit": item.unit,
                "quantity": float(item.quantity or 0),
                "width": float(item.width) if item.width is not None else None,
                "height": float(item.height) if item.height is not None else None,
                "unit_price": float(item.unit_price or 0),
                "subtotal": float(item.subtotal or 0),
                "final_price": float(item.final_price or 0),
                "remark": item.remark,
            }
            for item in quote.items
        ],
        "notes": quote.notes,
        "payment_terms": quote.payment_terms,
        "service_terms": quote.service_terms,
        "valid_until": quote.valid_until.isoformat() if quote.valid_until else None,
        "created_at": quote.created_at.isoformat() if quote.created_at else None,
        "allow_download": quote.allow_download,
        "view_count": quote.view_count,
        "company": {
            "name": company.name if company else None,
            "contact_name": company.contact_name if company else None,
            "contact_phone": company.contact_phone if company else None,
            "contact_wechat": company.contact_wechat if company else None,
            "address": company.address if company else None,
            "logo_url": f"/api/files/{company.logo_file_id}" if company and company.logo_file_id else None,
        },
    }
    if include_internal:
        payload["internal"] = {
            "total_cost": float(quote.total_cost or 0),
            "gross_profit": float(quote.gross_profit or 0),
            "gross_margin": float(quote.gross_margin or 0),
            "missing_fields": quote.missing_fields or [],
            "confidence": float(quote.confidence) if quote.confidence is not None else None,
            "items": [
                {
                    "id": item.id,
                    "product_name": item.product_name,
                    "cost_price": float(item.cost_price or 0),
                    "material_cost": float(item.material_cost or 0),
                    "loss_cost": float(item.loss_cost or 0),
                    "labor_cost": float(item.labor_cost or 0),
                    "transport_cost": float(item.transport_cost or 0),
                    "other_cost": float(item.other_cost or 0),
                    "total_cost": float(item.total_cost or 0),
                    "profit_margin": float(item.profit_margin or 0),
                    "formula": item.formula,
                    "breakdown": item.breakdown,
                    "match_confidence": float(item.match_confidence) if item.match_confidence is not None else None,
                }
                for item in quote.items
            ],
        }
    return payload


def quote_ai_payload(quote: Quote) -> dict[str, Any]:
    """给 AI 的报价摘要：不含成本，避免 AI 输出内部信息。"""
    return {
        "quote_no": quote.quote_no,
        "project_name": quote.project_name,
        "total_amount": float(quote.total_amount or 0),
        "items": [
            {
                "product_name": item.product_name,
                "unit": item.unit,
                "quantity": float(item.quantity or 0),
                "final_price": float(item.final_price or 0),
            }
            for item in quote.items
        ],
        "tiers": quote.tiers or {},
    }


def list_quote_versions(db: Session, quote: Quote) -> list[dict[str, Any]]:
    versions = db.scalars(
        select(QuoteVersion).where(QuoteVersion.quote_id == quote.id).order_by(QuoteVersion.version_no.desc())
    )
    return [
        {
            "id": version.id,
            "version_no": version.version_no,
            "total_amount": float(version.total_amount or 0),
            "gross_margin": float(version.gross_margin or 0),
            "change_note": version.change_note,
            "created_by": version.created_by,
            "created_at": version.created_at.isoformat() if version.created_at else None,
        }
        for version in versions
    ]


def add_followup(
    db: Session,
    *,
    company_id: int,
    customer_id: int,
    user_id: int | None,
    quote_id: int | None = None,
    content: str = "",
    status: str = "communicating",
    next_followup_at=None,  # noqa: ANN001
    channel: str = "wechat",
) -> Followup:
    followup = Followup(
        company_id=company_id,
        customer_id=customer_id,
        quote_id=quote_id,
        user_id=user_id,
        status=status,
        content=content,
        next_followup_at=next_followup_at,
        channel=channel,
    )
    db.add(followup)
    customer = db.get(Customer, customer_id)
    if customer:
        customer.status = status
        customer.last_contact_at = utcnow()
        customer.next_followup_at = next_followup_at
    db.flush()
    return followup
