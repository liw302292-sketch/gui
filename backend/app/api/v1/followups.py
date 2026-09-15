"""跟进系统：不做完整 CRM，只保留下一次跟进时间、备注、状态。"""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.core.deps import Context, DbSession
from app.core.errors import NotFoundError
from app.models.base import utcnow
from app.models.customer import Customer, Followup
from app.schemas.common import Message
from app.schemas.customer import FollowupCreate, FollowupOut, FollowupUpdate
from app.services import quote_service

router = APIRouter()


def _out(db: DbSession, followup: Followup) -> FollowupOut:
    customer = db.get(Customer, followup.customer_id)
    return FollowupOut(
        id=followup.id,
        customer_id=followup.customer_id,
        customer_name=customer.name if customer else None,
        quote_id=followup.quote_id,
        user_id=followup.user_id,
        status=followup.status,
        content=followup.content,
        next_followup_at=followup.next_followup_at,
        done=followup.done,
        channel=followup.channel,
        created_at=followup.created_at,
    )


@router.get("", response_model=dict, summary="跟进列表")
def list_followups(
    context: Context,
    db: DbSession,
    scope: str = Query(default="all", pattern="^(all|today|overdue|done)$"),
    customer_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
) -> dict:
    stmt = select(Followup).where(Followup.company_id == context.company_id)
    today_start = datetime.combine(utcnow().date(), datetime.min.time())
    if scope == "today":
        stmt = stmt.where(
            Followup.done.is_(False),
            Followup.next_followup_at.is_not(None),
            Followup.next_followup_at < today_start + timedelta(days=1),
        )
    elif scope == "overdue":
        stmt = stmt.where(Followup.done.is_(False), Followup.next_followup_at < today_start)
    elif scope == "done":
        stmt = stmt.where(Followup.done.is_(True))
    if customer_id:
        stmt = stmt.where(Followup.customer_id == customer_id)

    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    followups = list(
        db.scalars(
            stmt.order_by(Followup.done.asc(), Followup.next_followup_at.asc().nulls_last(), Followup.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return {
        "ok": True,
        "data": {
            "items": [_out(db, item).model_dump() for item in followups],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/today", response_model=dict, summary="今日待跟进")
def today(context: Context, db: DbSession) -> dict:
    today_start = datetime.combine(utcnow().date(), datetime.min.time())
    customers = list(
        db.scalars(
            select(Customer)
            .where(
                Customer.company_id == context.company_id,
                Customer.next_followup_at.is_not(None),
                Customer.next_followup_at < today_start + timedelta(days=1),
                Customer.status.notin_(("won", "lost")),
            )
            .order_by(Customer.next_followup_at.asc())
        )
    )
    return {
        "ok": True,
        "data": {
            "count": len(customers),
            "hint": f"今日有 {len(customers)} 个客户需要跟进。" if customers else "今天没有需要跟进的客户。",
            "items": [
                {
                    "id": customer.id,
                    "name": customer.name,
                    "contact_name": customer.contact_name,
                    "phone": customer.phone,
                    "status": customer.status,
                    "next_followup_at": customer.next_followup_at.isoformat() if customer.next_followup_at else None,
                    "total_amount": float(customer.total_amount or 0),
                }
                for customer in customers
            ],
        },
    }


@router.post("", response_model=dict, summary="新增跟进记录")
def create_followup(payload: FollowupCreate, context: Context, db: DbSession) -> dict:
    customer = db.get(Customer, payload.customer_id)
    if not customer or customer.company_id != context.company_id:
        raise NotFoundError("客户不存在")
    followup = quote_service.add_followup(
        db,
        company_id=context.company_id,
        customer_id=payload.customer_id,
        user_id=context.user_id,
        quote_id=payload.quote_id,
        content=payload.content,
        status=payload.status,
        next_followup_at=payload.next_followup_at,
        channel=payload.channel,
    )
    return {"ok": True, "message": "跟进记录已保存", "data": _out(db, followup).model_dump()}


@router.put("/{followup_id}", response_model=dict, summary="更新跟进记录")
def update_followup(followup_id: int, payload: FollowupUpdate, context: Context, db: DbSession) -> dict:
    followup = db.get(Followup, followup_id)
    if not followup or followup.company_id != context.company_id:
        raise NotFoundError("跟进记录不存在")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if value is not None:
            setattr(followup, key, value)
    if followup.done:
        customer = db.get(Customer, followup.customer_id)
        if customer:
            customer.next_followup_at = None
    db.flush()
    return {"ok": True, "message": "跟进记录已更新", "data": _out(db, followup).model_dump()}


@router.delete("/{followup_id}", response_model=Message, summary="删除跟进记录")
def delete_followup(followup_id: int, context: Context, db: DbSession) -> Message:
    followup = db.get(Followup, followup_id)
    if not followup or followup.company_id != context.company_id:
        raise NotFoundError("跟进记录不存在")
    db.delete(followup)
    return Message(message="跟进记录已删除")

