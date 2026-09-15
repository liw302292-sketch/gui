"""套餐、订单、订阅接口。"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import Context, DbSession, OwnerContext
from app.core.errors import NotFoundError
from app.models.subscription import Order
from app.services import plan_service

router = APIRouter()


@router.get("/plans", response_model=dict, summary="套餐列表")
def plans(db: DbSession, include_hidden: bool = False) -> dict:
    items = [plan_service.plan_to_dict(plan) for plan in plan_service.list_plans(db, include_hidden=include_hidden)]
    return {"ok": True, "data": {"items": items, "feature_labels": plan_service.FEATURE_LABELS}}


@router.get("/current", response_model=dict, summary="当前套餐与用量")
def current(context: Context, db: DbSession) -> dict:
    from app.services.ai.usage_tracker import usage_tracker  # noqa: PLC0415
    from app.services.plan_service import platform_billing_stats  # noqa: PLC0415

    subscription = plan_service.current_subscription(db, context.company_id)
    return {
        "ok": True,
        "data": {
            "plan": plan_service.plan_to_dict(context.plan) if context.plan else None,
            "subscription": {
                "status": subscription.status if subscription else "active",
                "start_at": subscription.start_at.isoformat() if subscription else None,
                "end_at": subscription.end_at.isoformat() if subscription and subscription.end_at else None,
                "auto_renew": subscription.auto_renew if subscription else False,
            },
            "ai_usage": usage_tracker.monthly_usage(db, context.company_id),
            "billing": platform_billing_stats(db) if context.is_superadmin else None,
        },
    }


@router.get("/orders", response_model=dict, summary="订单列表")
def orders(context: Context, db: DbSession) -> dict:
    items = list(
        db.scalars(
            select(Order).where(Order.company_id == context.company_id).order_by(Order.created_at.desc()).limit(50)
        )
    )
    return {
        "ok": True,
        "data": [
            {
                "id": order.id,
                "order_no": order.order_no,
                "plan_code": order.plan_code,
                "amount": float(order.amount or 0),
                "payment_method": order.payment_method,
                "status": order.status,
                "paid_at": order.paid_at.isoformat() if order.paid_at else None,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "remark": order.remark,
            }
            for order in items
        ],
    }


@router.post("/orders", response_model=dict, summary="创建订单（开发环境自动完成支付）")
def create_order(context: OwnerContext, db: DbSession, plan_code: str, payment_method: str | None = None) -> dict:
    order = plan_service.create_order(
        db,
        company_id=context.company_id,
        user_id=context.user_id,
        plan_code=plan_code,
        payment_method=payment_method,
    )
    return {
        "ok": True,
        "message": "订单已创建" if order.status == "pending" else "订单已支付，套餐已生效",
        "data": {
            "id": order.id,
            "order_no": order.order_no,
            "amount": float(order.amount or 0),
            "status": order.status,
            "payment_method": order.payment_method,
        },
    }


@router.post("/orders/{order_id}/pay", response_model=dict, summary="支付订单（mock 支付抽象层）")
def pay_order(order_id: int, context: OwnerContext, db: DbSession, external_trade_no: str | None = None) -> dict:
    order = db.get(Order, order_id)
    if not order or order.company_id != context.company_id:
        raise NotFoundError("订单不存在")
    plan_service.pay_order(db, order=order, external_trade_no=external_trade_no)
    return {
        "ok": True,
        "message": "支付成功，套餐已生效",
        "data": {"order_no": order.order_no, "status": order.status},
    }


@router.post("/cancel", response_model=dict, summary="取消自动续费")
def cancel(context: OwnerContext, db: DbSession) -> dict:
    subscription = plan_service.current_subscription(db, context.company_id)
    if subscription is None:
        raise NotFoundError("没有正在生效的订阅")
    subscription.auto_renew = False
    db.flush()
    return {"ok": True, "message": "已取消自动续费，到期后将不再扣费"}

