"""套餐、订单、订阅。第一阶段为支付抽象层，未配置支付密钥时使用 mock payment。"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ConflictError, NotFoundError
from app.models.base import utcnow
from app.models.company import Company
from app.models.subscription import Order, Plan, Subscription
from app.services import numbering, notification_service

FEATURE_LABELS = {
    "quotes": "报价单",
    "ai": "AI 识别与助手",
    "branding": "企业品牌与自定义报价单",
    "analytics": "数据统计",
    "members": "多人协作",
    "private_deploy": "私有部署",
    "api": "开放 API",
}


def list_plans(db: Session, *, include_hidden: bool = False) -> list[Plan]:
    stmt = select(Plan).where(Plan.is_active.is_(True))
    if not include_hidden:
        stmt = stmt.where(Plan.is_public.is_(True))
    return list(db.scalars(stmt.order_by(Plan.sort_order.asc(), Plan.price.asc())))


def plan_to_dict(plan: Plan) -> dict[str, Any]:
    return {
        "id": plan.id,
        "code": plan.code,
        "name": plan.name,
        "tagline": plan.tagline,
        "price": float(plan.price or 0),
        "billing_cycle": plan.billing_cycle,
        "max_users": plan.max_users,
        "max_quotes": plan.max_quotes,
        "ai_quota": plan.ai_quota,
        "storage_quota_mb": plan.storage_quota_mb,
        "features": plan.features or [],
        "description": plan.description,
        "is_public": plan.is_public,
    }


def current_subscription(db: Session, company_id: int) -> Subscription | None:
    subscription = db.scalar(
        select(Subscription)
        .where(Subscription.company_id == company_id, Subscription.status == "active")
        .order_by(Subscription.end_at.desc().nulls_last())
    )
    if subscription and subscription.end_at and subscription.end_at < utcnow():
        subscription.status = "expired"
        db.flush()
        return None
    return subscription


def create_order(
    db: Session,
    *,
    company_id: int,
    user_id: int | None,
    plan_code: str,
    payment_method: str | None = None,
    auto_pay: bool | None = None,
) -> Order:
    plan = db.scalar(select(Plan).where(Plan.code == plan_code, Plan.is_active.is_(True)))
    if plan is None:
        raise NotFoundError("套餐不存在或已下架")

    method = payment_method or settings.payment_provider
    order = Order(
        order_no=numbering.generate_order_no(db),
        company_id=company_id,
        plan_id=plan.id,
        user_id=user_id,
        plan_code=plan.code,
        amount=plan.price,
        payment_method=method,
        status="pending",
        remark=f"购买 {plan.name}",
    )
    db.add(order)
    db.flush()

    should_auto_pay = settings.payment_mock_auto_paid if auto_pay is None else auto_pay
    if should_auto_pay and method == "mock":
        pay_order(db, order=order, external_trade_no=f"MOCK-{order.order_no}")
    return order


def pay_order(db: Session, *, order: Order, external_trade_no: str | None = None) -> Order:
    """支付抽象层：mock 直接置为已支付；真实支付接入后回调此方法。"""
    if order.status == "paid":
        return order
    if order.status in ("cancelled", "refunded"):
        raise ConflictError(f"当前订单状态（{order.status}）无法支付")

    order.status = "paid"
    order.paid_at = utcnow()
    order.external_trade_no = external_trade_no or order.external_trade_no
    db.flush()
    activate_subscription(db, order=order)
    return order


def activate_subscription(db: Session, *, order: Order) -> Subscription:
    plan = db.get(Plan, order.plan_id) if order.plan_id else None
    if plan is None:
        raise NotFoundError("套餐不存在")

    for existing in db.scalars(
        select(Subscription).where(Subscription.company_id == order.company_id, Subscription.status == "active")
    ):
        existing.status = "cancelled"
        existing.cancelled_at = utcnow()

    today = utcnow()
    if plan.billing_cycle == "year":
        end_at = today + timedelta(days=365)
    elif plan.billing_cycle == "month":
        end_at = today + timedelta(days=30)
    else:
        end_at = None

    subscription = Subscription(
        company_id=order.company_id,
        plan_id=plan.id,
        order_id=order.id,
        status="active",
        start_at=today,
        end_at=end_at,
        auto_renew=False,
    )
    db.add(subscription)

    company = db.get(Company, order.company_id)
    if company:
        company.ai_monthly_quota = plan.ai_quota

    notification_service.push(
        db,
        company_id=order.company_id,
        user_id=order.user_id,
        title=f"套餐已升级为 {plan.name}",
        content=f"订单 {order.order_no} 已支付成功，AI 每月额度 {plan.ai_quota} 次，报价单上限 {plan.max_quotes} 个/月。",
        type="subscription",
        link="/app/billing",
    )
    db.flush()
    return subscription


def enforce_plan_limits(db: Session, company_id: int, plan: Plan | None) -> None:
    """套餐额度校验：报价数量超限时提示升级。"""
    if plan is None or plan.max_quotes <= 0:
        return
    from app.core.errors import QuotaExceededError  # noqa: PLC0415
    from app.models.base import utcnow as _now  # noqa: PLC0415
    from app.models.quote import Quote  # noqa: PLC0415

    month_start = _now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    count = int(
        db.scalar(
            select(func.count())
            .select_from(Quote)
            .where(Quote.company_id == company_id, Quote.created_at >= month_start)
        )
        or 0
    )
    if count >= plan.max_quotes:
        raise QuotaExceededError(
            f"本月报价数量已达套餐上限（{plan.max_quotes} 份），升级套餐可继续创建报价。"
        )


def platform_billing_stats(db: Session) -> dict[str, Any]:
    today = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = today.replace(day=1)
    paid_statuses = ("paid",)

    def amount_since(since) -> float:  # noqa: ANN001
        return float(
            db.scalar(
                select(func.coalesce(func.sum(Order.amount), 0)).where(
                    Order.status.in_(paid_statuses), Order.paid_at >= since
                )
            )
            or 0
        )

    return {
        "today_revenue": amount_since(today),
        "month_revenue": amount_since(month_start),
        "total_revenue": float(
            db.scalar(
                select(func.coalesce(func.sum(Order.amount), 0)).where(Order.status.in_(paid_statuses))
            )
            or 0
        ),
        "pending_orders": int(
            db.scalar(select(func.count()).select_from(Order).where(Order.status == "pending")) or 0
        ),
    }

