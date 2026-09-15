"""客户管理：列表、详情、报价记录、跟进记录、活动记录。"""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import func, or_, select

from app.core.deps import Context, DbSession
from app.core.errors import ConflictError, NotFoundError
from app.models.base import utcnow
from app.models.customer import Customer, Followup
from app.models.quote import Quote
from app.schemas.common import Message
from app.schemas.customer import CustomerCreate, CustomerOut, CustomerUpdate
from app.services.quote_service import QUOTE_STATUS_LABELS

router = APIRouter()

CUSTOMER_STATUSES = [
    {"value": "new", "label": "新客户", "color": "gray"},
    {"value": "quoted", "label": "已报价", "color": "blue"},
    {"value": "communicating", "label": "沟通中", "color": "amber"},
    {"value": "high_intent", "label": "高意向", "color": "violet"},
    {"value": "won", "label": "已成交", "color": "green"},
    {"value": "lost", "label": "已流失", "color": "red"},
]


def _out(customer: Customer) -> CustomerOut:
    return CustomerOut(
        id=customer.id,
        name=customer.name,
        contact_name=customer.contact_name,
        phone=customer.phone,
        wechat=customer.wechat,
        source=customer.source,
        address=customer.address,
        remark=customer.remark,
        status=customer.status,
        tags=customer.tags or [],
        quote_count=customer.quote_count,
        deal_count=customer.deal_count,
        total_amount=float(customer.total_amount or 0),
        next_followup_at=customer.next_followup_at,
        last_contact_at=customer.last_contact_at,
        created_at=customer.created_at,
    )


@router.get("/statuses", response_model=dict, summary="客户状态字典")
def statuses() -> dict:
    return {"ok": True, "data": CUSTOMER_STATUSES}


@router.get("", response_model=dict, summary="客户列表")
def list_customers(
    context: Context,
    db: DbSession,
    keyword: str | None = None,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    order_by: str = Query(default="recent", pattern="^(recent|amount|followup)$"),
) -> dict:
    stmt = select(Customer).where(Customer.company_id == context.company_id)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            or_(Customer.name.ilike(like), Customer.contact_name.ilike(like), Customer.phone.ilike(like))
        )
    if status:
        stmt = stmt.where(Customer.status == status)

    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    if order_by == "amount":
        stmt = stmt.order_by(Customer.total_amount.desc())
    elif order_by == "followup":
        stmt = stmt.order_by(Customer.next_followup_at.asc().nulls_last())
    else:
        stmt = stmt.order_by(Customer.created_at.desc())
    customers = list(db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)))

    summary = db.execute(
        select(
            func.count(Customer.id),
            func.coalesce(func.sum(Customer.total_amount), 0),
        ).where(Customer.company_id == context.company_id)
    ).one()

    return {
        "ok": True,
        "data": {
            "items": [_out(customer).model_dump() for customer in customers],
            "total": total,
            "page": page,
            "page_size": page_size,
            "summary": {"total_customers": int(summary[0] or 0), "total_amount": float(summary[1] or 0)},
        },
    }


@router.get("/{customer_id}", response_model=dict, summary="客户详情（含报价与跟进）")
def get_customer(customer_id: int, context: Context, db: DbSession) -> dict:
    customer = db.get(Customer, customer_id)
    if not customer or customer.company_id != context.company_id:
        raise NotFoundError("客户不存在")

    quotes = list(
        db.scalars(
            select(Quote)
            .where(Quote.company_id == context.company_id, Quote.customer_id == customer_id)
            .order_by(Quote.created_at.desc())
            .limit(50)
        )
    )
    followups = list(
        db.scalars(
            select(Followup)
            .where(Followup.company_id == context.company_id, Followup.customer_id == customer_id)
            .order_by(Followup.created_at.desc())
            .limit(50)
        )
    )
    activities = [
        {
            "type": "quote",
            "title": f"创建报价 {quote.quote_no}",
            "detail": f"{quote.project_name} · ¥{float(quote.total_amount or 0):,.2f}",
            "status": quote.status,
            "at": quote.created_at.isoformat() if quote.created_at else None,
        }
        for quote in quotes
    ] + [
        {
            "type": "followup",
            "title": "跟进记录",
            "detail": item.content,
            "status": item.status,
            "at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in followups
    ]
    activities.sort(key=lambda item: item["at"] or "", reverse=True)

    return {
        "ok": True,
        "data": {
            "customer": _out(customer).model_dump(),
            "quotes": [
                {
                    "id": quote.id,
                    "quote_no": quote.quote_no,
                    "project_name": quote.project_name,
                    "status": quote.status,
                    "status_label": QUOTE_STATUS_LABELS.get(quote.status, quote.status),
                    "total_amount": float(quote.total_amount or 0),
                    "view_count": quote.view_count,
                    "created_at": quote.created_at.isoformat() if quote.created_at else None,
                }
                for quote in quotes
            ],
            "followups": [
                {
                    "id": item.id,
                    "content": item.content,
                    "status": item.status,
                    "channel": item.channel,
                    "done": item.done,
                    "next_followup_at": item.next_followup_at.isoformat() if item.next_followup_at else None,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "user_id": item.user_id,
                }
                for item in followups
            ],
            "activities": activities[:30],
        },
    }


@router.post("", response_model=dict, summary="创建客户")
def create_customer(payload: CustomerCreate, context: Context, db: DbSession) -> dict:
    exists = db.scalar(
        select(Customer).where(Customer.company_id == context.company_id, Customer.name == payload.name)
    )
    if exists:
        raise ConflictError("已存在同名客户")
    customer = Customer(
        company_id=context.company_id,
        owner_user_id=context.user_id,
        **payload.model_dump(),
    )
    db.add(customer)
    db.flush()
    return {"ok": True, "message": "客户已创建", "data": _out(customer).model_dump()}


@router.put("/{customer_id}", response_model=dict, summary="更新客户")
def update_customer(customer_id: int, payload: CustomerUpdate, context: Context, db: DbSession) -> dict:
    customer = db.get(Customer, customer_id)
    if not customer or customer.company_id != context.company_id:
        raise NotFoundError("客户不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(customer, key, value)
    db.flush()
    return {"ok": True, "message": "客户已更新", "data": _out(customer).model_dump()}


@router.delete("/{customer_id}", response_model=Message, summary="删除客户")
def delete_customer(customer_id: int, context: Context, db: DbSession) -> Message:
    customer = db.get(Customer, customer_id)
    if not customer or customer.company_id != context.company_id:
        raise NotFoundError("客户不存在")
    count = db.scalar(
        select(func.count()).select_from(Quote).where(Quote.customer_id == customer_id)
    ) or 0
    if count:
        raise ConflictError(f"该客户还有 {count} 份报价单，删除会影响历史数据，请先作废报价")
    db.delete(customer)
    return Message(message="客户已删除")


@router.post("/{customer_id}/touch", response_model=Message, summary="记录一次联系")
def touch(customer_id: int, context: Context, db: DbSession, next_followup_at: str | None = None) -> Message:
    customer = db.get(Customer, customer_id)
    if not customer or customer.company_id != context.company_id:
        raise NotFoundError("客户不存在")
    customer.last_contact_at = utcnow()
    if next_followup_at:
        from datetime import datetime  # noqa: PLC0415

        try:
            customer.next_followup_at = datetime.fromisoformat(next_followup_at.replace("Z", ""))
        except ValueError as exc:
            raise ConflictError("下次跟进时间格式不正确") from exc
    db.flush()
    return Message(message="已记录本次联系")

