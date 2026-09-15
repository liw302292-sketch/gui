"""系统管理员后台接口。所有接口要求超级管理员权限。"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import func, or_, select

from app.core.config import settings
from app.core.deps import AdminContext, DbSession, SuperAdmin
from app.core.errors import NotFoundError
from app.core.logging import memory_log_handler
from app.core.redis_client import redis_available
from app.industry.registry import industry_registry
from app.models.ai import AITask, AIUsage
from app.models.audit import AuditLog
from app.models.company import Company, Member, SystemSetting
from app.models.customer import Customer
from app.models.quote import Quote
from app.models.subscription import Order, Plan, Subscription
from app.models.user import User
from app.schemas.admin import (
    CompanyStatusRequest,
    PlanCreate,
    PlanUpdate,
    SystemSettingUpdate,
)
from app.schemas.common import Message
from app.services import notification_service
from app.services.ai.prompt_manager import prompt_manager
from app.services.ai.usage_tracker import usage_tracker
from app.services.plan_service import plan_to_dict, platform_billing_stats

router = APIRouter()


def _day_start(day: date) -> datetime:
    return datetime.combine(day, datetime.min.time())


@router.get("/dashboard", response_model=dict, summary="平台总览")
def dashboard(db: DbSession, context: AdminContext) -> dict:
    today = _day_start(date.today())
    month_start = today.replace(day=1)
    companies_total = int(db.scalar(select(func.count()).select_from(Company)) or 0)
    companies_active = int(
        db.scalar(select(func.count()).select_from(Company).where(Company.status == "active")) or 0
    )
    users_total = int(db.scalar(select(func.count()).select_from(User)) or 0)
    new_today = int(
        db.scalar(select(func.count()).select_from(User).where(User.created_at >= today)) or 0
    )
    quotes_today = int(db.scalar(select(func.count()).select_from(Quote).where(Quote.created_at >= today)) or 0)
    quotes_total = int(db.scalar(select(func.count()).select_from(Quote)) or 0)
    paid_companies = int(
        db.scalar(
            select(func.count(func.distinct(Subscription.company_id))).where(
                Subscription.status == "active",
                Subscription.plan_id.is_not(None),
                Subscription.end_at > datetime.now() + timedelta(days=3),
                Subscription.plan_id.in_(select(Plan.id).where(Plan.code != "free")),
            )
        )
        or 0
    )
    ai_stats = usage_tracker.platform_stats(db)
    billing = platform_billing_stats(db)

    trend = []
    for offset in range(13, -1, -1):
        day = date.today() - timedelta(days=offset)
        start = _day_start(day)
        end = start + timedelta(days=1)
        trend.append(
            {
                "date": day.strftime("%m-%d"),
                "companies": int(
                    db.scalar(select(func.count()).select_from(Company).where(Company.created_at >= start, Company.created_at < end)) or 0
                ),
                "quotes": int(
                    db.scalar(select(func.count()).select_from(Quote).where(Quote.created_at >= start, Quote.created_at < end)) or 0
                ),
                "ai_calls": int(
                    db.scalar(select(func.count()).select_from(AIUsage).where(AIUsage.created_at >= start, AIUsage.created_at < end)) or 0
                ),
            }
        )

    return {
        "ok": True,
        "data": {
            "stats": {
                "companies_total": companies_total,
                "companies_active": companies_active,
                "users_total": users_total,
                "new_users_today": new_today,
                "paid_companies": paid_companies,
                "quotes_today": quotes_today,
                "quotes_total": quotes_total,
                **billing,
            },
            "ai": ai_stats,
            "trend": trend,
            "system": {
                "env": settings.app_env,
                "ai_mode": settings.ai_mode,
                "redis": redis_available(),
                "storage_backend": settings.storage_backend,
                "database": "sqlite" if settings.is_sqlite else "postgresql",
            },
        },
    }


@router.get("/companies", response_model=dict, summary="企业列表")
def companies(
    db: DbSession,
    context: AdminContext,
    keyword: str | None = None,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
) -> dict:
    stmt = select(Company)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(or_(Company.name.ilike(like), Company.contact_phone.ilike(like)))
    if status:
        stmt = stmt.where(Company.status == status)
    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    items = list(db.scalars(stmt.order_by(Company.created_at.desc()).offset((page - 1) * page_size).limit(page_size)))

    result = []
    for company in items:
        owner_member = db.scalar(
            select(Member).where(Member.company_id == company.id, Member.role == "owner").limit(1)
        )
        owner = db.get(User, owner_member.user_id) if owner_member else None
        plan, subscription = None, None
        subscription = db.scalar(
            select(Subscription)
            .where(Subscription.company_id == company.id, Subscription.status == "active")
            .order_by(Subscription.end_at.desc().nulls_last())
        )
        plan = db.get(Plan, subscription.plan_id) if subscription and subscription.plan_id else None
        result.append(
            {
                "id": company.id,
                "name": company.name,
                "industry_id": company.industry_id,
                "status": company.status,
                "plan_code": plan.code if plan else "free",
                "plan_name": plan.name if plan else "免费版",
                "owner_name": owner.name if owner else None,
                "owner_email": owner.email if owner else None,
                "owner_phone": owner.phone if owner else None,
                "member_count": int(
                    db.scalar(select(func.count()).select_from(Member).where(Member.company_id == company.id)) or 0
                ),
                "quote_count": int(
                    db.scalar(select(func.count()).select_from(Quote).where(Quote.company_id == company.id)) or 0
                ),
                "ai_calls": int(
                    db.scalar(select(func.count()).select_from(AIUsage).where(AIUsage.company_id == company.id)) or 0
                ),
                "created_at": company.created_at.isoformat() if company.created_at else None,
            }
        )
    return {"ok": True, "data": {"items": result, "total": total, "page": page, "page_size": page_size}}


@router.get("/companies/{company_id}", response_model=dict, summary="企业详情")
def company_detail(company_id: int, db: DbSession, context: AdminContext) -> dict:
    company = db.get(Company, company_id)
    if not company:
        raise NotFoundError("企业不存在")
    members = list(db.scalars(select(Member).where(Member.company_id == company_id)))
    users = []
    for member in members:
        user = db.get(User, member.user_id)
        if user:
            users.append(
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "phone": user.phone,
                    "role": member.role,
                    "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                }
            )
    return {
        "ok": True,
        "data": {
            "company": {
                "id": company.id,
                "name": company.name,
                "industry_id": company.industry_id,
                "status": company.status,
                "contact_name": company.contact_name,
                "contact_phone": company.contact_phone,
                "address": company.address,
                "ai_monthly_quota": company.ai_monthly_quota,
                "created_at": company.created_at.isoformat() if company.created_at else None,
            },
            "members": users,
            "ai_usage": usage_tracker.monthly_usage(db, company_id),
            "quote_count": int(
                db.scalar(select(func.count()).select_from(Quote).where(Quote.company_id == company_id)) or 0
            ),
            "customer_count": int(
                db.scalar(select(func.count()).select_from(Customer).where(Customer.company_id == company_id)) or 0
            ),
        },
    }


@router.post("/companies/{company_id}/status", response_model=Message, summary="启用/禁用企业")
def set_company_status(
    company_id: int, payload: CompanyStatusRequest, db: DbSession, context: AdminContext
) -> Message:
    company = db.get(Company, company_id)
    if not company:
        raise NotFoundError("企业不存在")
    company.status = payload.status
    db.flush()
    if payload.status == "disabled":
        notification_service.push(
            db,
            company_id=company.id,
            user_id=None,
            title="企业账号已被停用",
            content=payload.reason or "如有疑问请联系平台客服。",
            type="account",
        )
    return Message(message="企业状态已更新为 " + ("正常" if payload.status == "active" else "已停用"))


@router.post("/companies/{company_id}/quota", response_model=Message, summary="调整企业 AI 额度")
def set_quota(company_id: int, db: DbSession, context: AdminContext, ai_monthly_quota: int) -> Message:
    company = db.get(Company, company_id)
    if not company:
        raise NotFoundError("企业不存在")
    company.ai_monthly_quota = max(ai_monthly_quota, 0)
    db.flush()
    return Message(message=f"AI 每月额度已调整为 {company.ai_monthly_quota} 次")


@router.get("/users", response_model=dict, summary="用户列表")
def users(
    db: DbSession,
    context: AdminContext,
    keyword: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
) -> dict:
    stmt = select(User)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(or_(User.name.ilike(like), User.email.ilike(like), User.phone.ilike(like)))
    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    items = list(db.scalars(stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)))
    return {
        "ok": True,
        "data": {
            "items": [
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "phone": user.phone,
                    "is_superadmin": user.is_superadmin,
                    "status": user.status,
                    "company_count": int(
                        db.scalar(select(func.count()).select_from(Member).where(Member.user_id == user.id)) or 0
                    ),
                    "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                }
                for user in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.post("/users/{user_id}/status", response_model=Message, summary="启用/禁用用户")
def set_user_status(user_id: int, db: DbSession, context: AdminContext, status: str) -> Message:
    user = db.get(User, user_id)
    if not user:
        raise NotFoundError("用户不存在")
    if user.id == context.user_id:
        raise NotFoundError("不能修改自己的状态")
    user.status = status
    db.flush()
    return Message(message="用户状态已更新")


@router.get("/plans", response_model=dict, summary="套餐列表（含隐藏）")
def admin_plans(db: DbSession, context: AdminContext) -> dict:
    plans = list(db.scalars(select(Plan).order_by(Plan.sort_order.asc())))
    return {
        "ok": True,
        "data": [
            {
                **plan_to_dict(plan),
                "is_active": plan.is_active,
                "sort_order": plan.sort_order,
                "company_count": int(
                    db.scalar(
                        select(func.count(func.distinct(Subscription.company_id))).where(
                            Subscription.plan_id == plan.id, Subscription.status == "active"
                        )
                    )
                    or 0
                ),
            }
            for plan in plans
        ],
    }


@router.post("/plans", response_model=dict, summary="创建套餐")
def create_plan(payload: PlanCreate, db: DbSession, context: AdminContext) -> dict:
    plan = Plan(**payload.model_dump())
    db.add(plan)
    db.flush()
    return {"ok": True, "message": "套餐已创建", "data": plan_to_dict(plan)}


@router.put("/plans/{plan_id}", response_model=dict, summary="更新套餐")
def update_plan(plan_id: int, payload: PlanUpdate, db: DbSession, context: AdminContext) -> dict:
    plan = db.get(Plan, plan_id)
    if not plan:
        raise NotFoundError("套餐不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(plan, key, value)
    db.flush()
    return {"ok": True, "message": "套餐已更新", "data": plan_to_dict(plan)}


@router.get("/orders", response_model=dict, summary="订单列表")
def admin_orders(db: DbSession, context: AdminContext, status: str | None = None) -> dict:
    stmt = select(Order)
    if status:
        stmt = stmt.where(Order.status == status)
    orders = list(db.scalars(stmt.order_by(Order.created_at.desc()).limit(200)))
    return {
        "ok": True,
        "data": [
            {
                "id": order.id,
                "order_no": order.order_no,
                "company_id": order.company_id,
                "company_name": (db.get(Company, order.company_id).name if db.get(Company, order.company_id) else None),
                "plan_code": order.plan_code,
                "amount": float(order.amount or 0),
                "payment_method": order.payment_method,
                "status": order.status,
                "paid_at": order.paid_at.isoformat() if order.paid_at else None,
                "created_at": order.created_at.isoformat() if order.created_at else None,
            }
            for order in orders
        ],
    }


@router.get("/subscriptions", response_model=dict, summary="订阅列表")
def admin_subscriptions(db: DbSession, context: AdminContext) -> dict:
    subscriptions = list(
        db.scalars(select(Subscription).order_by(Subscription.created_at.desc()).limit(200))
    )
    return {
        "ok": True,
        "data": [
            {
                "id": item.id,
                "company_id": item.company_id,
                "company_name": (db.get(Company, item.company_id).name if db.get(Company, item.company_id) else None),
                "plan_code": (db.get(Plan, item.plan_id).code if item.plan_id and db.get(Plan, item.plan_id) else None),
                "status": item.status,
                "start_at": item.start_at.isoformat() if item.start_at else None,
                "end_at": item.end_at.isoformat() if item.end_at else None,
                "auto_renew": item.auto_renew,
            }
            for item in subscriptions
        ],
    }


@router.get("/ai/usage", response_model=dict, summary="AI 使用统计")
def admin_ai_usage(db: DbSession, context: AdminContext, days: int = Query(default=30, ge=1, le=365)) -> dict:
    return {"ok": True, "data": usage_tracker.platform_stats(db, days=days)}


@router.get("/ai/tasks", response_model=dict, summary="AI 任务列表")
def admin_ai_tasks(db: DbSession, context: AdminContext, status: str | None = None, limit: int = 100) -> dict:
    stmt = select(AITask)
    if status:
        stmt = stmt.where(AITask.status == status)
    tasks = list(db.scalars(stmt.order_by(AITask.created_at.desc()).limit(min(limit, 300))))
    return {
        "ok": True,
        "data": [
            {
                "id": task.id,
                "company_id": task.company_id,
                "task_type": task.task_type,
                "status": task.status,
                "model": task.model,
                "mode": task.mode,
                "input_tokens": task.input_tokens,
                "output_tokens": task.output_tokens,
                "estimated_cost": float(task.estimated_cost or 0),
                "latency_ms": task.latency_ms,
                "error": task.error_message,
                "created_at": task.created_at.isoformat() if task.created_at else None,
            }
            for task in tasks
        ],
    }


@router.get("/quotes/stats", response_model=dict, summary="平台报价统计")
def admin_quote_stats(db: DbSession, context: AdminContext) -> dict:
    totals = db.execute(
        select(
            func.count(Quote.id),
            func.coalesce(func.sum(Quote.total_amount), 0),
            func.coalesce(func.sum(Quote.total_cost), 0),
        )
    ).one()
    by_status = [
        {"status": status, "count": int(count or 0), "amount": float(amount or 0)}
        for status, count, amount in db.execute(
            select(
                Quote.status,
                func.count(Quote.id),
                func.coalesce(func.sum(Quote.total_amount), 0),
            ).group_by(Quote.status)
        )
    ]
    top_companies = [
        {"company_id": cid, "company_name": name, "count": int(count), "amount": float(amount or 0)}
        for cid, name, count, amount in db.execute(
            select(
                Quote.company_id,
                Company.name,
                func.count(Quote.id),
                func.coalesce(func.sum(Quote.total_amount), 0),
            )
            .join(Company, Company.id == Quote.company_id)
            .group_by(Quote.company_id, Company.name)
            .order_by(func.count(Quote.id).desc())
            .limit(10)
        )
    ]
    return {
        "ok": True,
        "data": {
            "quote_count": int(totals[0] or 0),
            "quote_amount": float(totals[1] or 0),
            "total_cost": float(totals[2] or 0),
            "by_status": by_status,
            "top_companies": top_companies,
        },
    }


@router.get("/logs", response_model=dict, summary="系统日志")
def logs(
    db: DbSession,
    context: AdminContext,
    level: str | None = None,
    limit: int = Query(default=200, ge=1, le=500),
) -> dict:
    audit_logs = list(db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)))
    return {
        "ok": True,
        "data": {
            "application_logs": memory_log_handler.snapshot(level=level, limit=limit),
            "audit_logs": [
                {
                    "id": item.id,
                    "company_id": item.company_id,
                    "user_name": item.user_name,
                    "action": item.action,
                    "target_type": item.target_type,
                    "target_id": item.target_id,
                    "summary": item.summary,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                }
                for item in audit_logs
            ],
        },
    }


@router.get("/errors", response_model=dict, summary="异常任务与错误日志")
def errors(db: DbSession, context: AdminContext, limit: int = 100) -> dict:
    failed_tasks = list(
        db.scalars(
            select(AITask).where(AITask.status == "failed").order_by(AITask.created_at.desc()).limit(limit)
        )
    )
    return {
        "ok": True,
        "data": {
            "ai_failures": [
                {
                    "id": task.id,
                    "company_id": task.company_id,
                    "task_type": task.task_type,
                    "model": task.model,
                    "error": task.error_message,
                    "raw_response": (task.raw_response or "")[:2000],
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                }
                for task in failed_tasks
            ],
            "error_logs": memory_log_handler.snapshot(level="ERROR", limit=limit),
        },
    }


@router.get("/settings", response_model=dict, summary="系统设置")
def get_settings(db: DbSession, context: AdminContext) -> dict:
    stored = {item.key: item.value for item in db.scalars(select(SystemSetting))}
    return {
        "ok": True,
        "data": {
            "runtime": {
                "app_env": settings.app_env,
                "ai_mode": settings.ai_mode,
                "deepseek_base_url": settings.deepseek_base_url,
                "text_model": settings.deepseek_text_model,
                "reasoning_model": settings.deepseek_reasoning_model,
                "vision_model": settings.deepseek_vision_model,
                "storage_backend": settings.storage_backend,
                "rate_limit_per_minute": settings.rate_limit_per_minute,
                "ai_rate_limit_per_minute": settings.ai_rate_limit_per_minute,
                "max_upload_mb": settings.max_upload_mb,
                "payment_provider": settings.payment_provider,
            },
            "stored": stored,
            "industries": industry_registry.summaries(),
            "prompt_files": [
                {"name": path.name, "size": path.stat().st_size}
                for path in sorted(prompt_manager.directory.glob("*.txt"))
            ],
        },
    }


@router.put("/settings", response_model=Message, summary="保存系统设置")
def save_setting(payload: SystemSettingUpdate, db: DbSession, context: AdminContext) -> Message:
    setting = db.scalar(select(SystemSetting).where(SystemSetting.key == payload.key))
    if setting is None:
        setting = SystemSetting(key=payload.key, value=payload.value, description=payload.description)
        db.add(setting)
    else:
        setting.value = payload.value
        if payload.description:
            setting.description = payload.description
    db.flush()
    return Message(message=f"设置 {payload.key} 已保存")


@router.get("/me", response_model=dict, summary="当前管理员信息")
def admin_me(user: SuperAdmin) -> dict:
    return {
        "ok": True,
        "data": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_superadmin": user.is_superadmin,
        },
    }
