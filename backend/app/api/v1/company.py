"""企业接口：设置、行业模板、Dashboard、统计分析。"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.deps import Context, DbSession, OwnerContext
from app.industry.registry import industry_registry
from app.models.company import Company
from app.schemas.common import Message
from app.schemas.company import CompanyDetail, CompanyUpdate
from app.services import analytics_service, audit_service, provisioning
from app.services.ai.usage_tracker import usage_tracker

router = APIRouter()


def _to_detail(company: Company) -> CompanyDetail:
    return CompanyDetail(
        id=company.id,
        name=company.name,
        short_name=company.short_name,
        industry_id=company.industry_id,
        contact_name=company.contact_name,
        contact_phone=company.contact_phone,
        contact_wechat=company.contact_wechat,
        address=company.address,
        credit_code=company.credit_code,
        default_tax_rate=float(company.default_tax_rate or 0),
        default_profit_margin=float(company.default_profit_margin or 0),
        default_quote_valid_days=company.default_quote_valid_days,
        default_payment_terms=company.default_payment_terms,
        default_service_terms=company.default_service_terms,
        default_footer=company.default_footer,
        rounding_mode=company.rounding_mode,
        quote_no_prefix=company.quote_no_prefix,
        ai_monthly_quota=company.ai_monthly_quota,
        logo_file_id=company.logo_file_id,
        status=company.status,
    )


@router.get("", response_model=dict, summary="获取企业设置")
def get_company(context: Context) -> dict:
    return {"ok": True, "data": _to_detail(context.company).model_dump()}


@router.put("", response_model=dict, summary="更新企业设置")
def update_company(payload: CompanyUpdate, context: OwnerContext, db: DbSession) -> dict:
    company = context.company
    before = _to_detail(company).model_dump(mode="json")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if value is not None and hasattr(company, key):
            setattr(company, key, value)
    db.flush()
    audit_service.record(
        db,
        company_id=company.id,
        user_id=context.user_id,
        user_name=context.user.name,
        action="company.update",
        target_type="company",
        target_id=company.id,
        summary="更新企业设置",
        before=before,
        after=_to_detail(company).model_dump(mode="json"),
    )
    return {"ok": True, "message": "企业设置已保存", "data": _to_detail(company).model_dump()}


@router.get("/industries", response_model=dict, summary="行业模板列表")
def list_industries(db: DbSession) -> dict:
    provisioning.ensure_industries(db)
    return {"ok": True, "data": industry_registry.summaries()}


@router.get("/dashboard", response_model=dict, summary="工作台数据")
def dashboard(context: Context, db: DbSession) -> dict:
    data = analytics_service.dashboard(db, company_id=context.company_id, user_name=context.user.name or "老板")
    data["ai_usage"] = usage_tracker.monthly_usage(db, context.company_id)
    data["company"] = {"id": context.company.id, "name": context.company.name, "plan": context.plan.name if context.plan else None}
    return {"ok": True, "data": data}


@router.get("/analytics", response_model=dict, summary="经营数据统计")
def analytics(
    context: Context,
    db: DbSession,
    period: str = Query(default="month", pattern="^(day|week|month)$"),
) -> dict:
    return {
        "ok": True,
        "data": analytics_service.company_analytics(db, company_id=context.company_id, period=period),
    }


@router.get("/notifications", response_model=dict, summary="站内通知列表")
def notifications(context: Context, db: DbSession, only_unread: bool = False) -> dict:
    from sqlalchemy import select  # noqa: PLC0415

    from app.models.customer import Notification  # noqa: PLC0415

    stmt = select(Notification).where(Notification.company_id == context.company_id)
    if only_unread:
        stmt = stmt.where(Notification.is_read.is_(False))
    items = list(db.scalars(stmt.order_by(Notification.created_at.desc()).limit(50)))
    return {
        "ok": True,
        "data": {
            "items": [
                {
                    "id": item.id,
                    "type": item.type,
                    "title": item.title,
                    "content": item.content,
                    "link": item.link,
                    "is_read": item.is_read,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                }
                for item in items
            ],
            "unread": sum(1 for item in items if not item.is_read),
        },
    }


@router.post("/notifications/read", response_model=Message, summary="通知标记已读")
def read_notifications(context: Context, db: DbSession, notification_id: int | None = None) -> Message:
    from app.services import notification_service  # noqa: PLC0415

    if notification_id:
        notification_service.mark_read(db, context.company_id, notification_id)
        return Message(message="已标记为已读")
    count = notification_service.mark_all_read(db, context.company_id, context.user_id)
    return Message(message=f"已将 {count} 条通知标记为已读")


@router.get("/search", response_model=dict, summary="全局搜索（客户 / 项目 / 报价编号）")
def global_search(context: Context, db: DbSession, q: str = Query(min_length=1, max_length=100)) -> dict:
    from sqlalchemy import or_  # noqa: PLC0415
    from sqlalchemy import select  # noqa: PLC0415

    from app.models.customer import Customer  # noqa: PLC0415
    from app.models.quote import Quote  # noqa: PLC0415

    keyword = f"%{q.strip()}%"
    customers = list(
        db.scalars(
            select(Customer)
            .where(
                Customer.company_id == context.company_id,
                or_(Customer.name.ilike(keyword), Customer.contact_name.ilike(keyword), Customer.phone.ilike(keyword)),
            )
            .limit(8)
        )
    )
    quotes = list(
        db.scalars(
            select(Quote)
            .where(
                Quote.company_id == context.company_id,
                or_(Quote.quote_no.ilike(keyword), Quote.project_name.ilike(keyword), Quote.customer_name.ilike(keyword)),
            )
            .order_by(Quote.created_at.desc())
            .limit(8)
        )
    )
    return {
        "ok": True,
        "data": {
            "customers": [
                {"id": item.id, "name": item.name, "contact_name": item.contact_name, "phone": item.phone}
                for item in customers
            ],
            "quotes": [
                {
                    "id": item.id,
                    "quote_no": item.quote_no,
                    "project_name": item.project_name,
                    "customer_name": item.customer_name,
                    "total_amount": float(item.total_amount or 0),
                    "status": item.status,
                }
                for item in quotes
            ],
        },
    }

