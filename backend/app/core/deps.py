"""依赖注入：认证、多租户上下文、权限、套餐校验。

所有业务接口都必须通过 CurrentContext 获取 company_id，
绝不允许从请求体或路径参数直接信任企业 ID。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

from fastapi import Cookie, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.errors import AuthError, PermissionError_, QuotaExceededError
from app.core.security import decode_token
from app.models.base import utcnow
from app.models.company import Company, Member
from app.models.subscription import Plan, Subscription
from app.models.user import User

ACCESS_COOKIE = "qe_access"
REFRESH_COOKIE = "qe_refresh"


@dataclass
class CurrentContext:
    """当前请求上下文：用户 + 企业 + 角色 + 套餐。"""

    user: User
    company: Company
    member: Member | None
    role: str
    user_id: int
    company_id: int
    is_superadmin: bool
    plan: Plan | None = None
    subscription: Subscription | None = None

    @property
    def is_owner(self) -> bool:
        return self.role in ("owner", "admin") or self.is_superadmin


def _extract_token(
    authorization: Annotated[str | None, Header()] = None,
    qe_access: Annotated[str | None, Cookie()] = None,
) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    if qe_access:
        return qe_access
    return None


def get_optional_user(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str | None, Depends(_extract_token)],
) -> User | None:
    if not token:
        return None
    payload = decode_token(token, expected_type="access")
    user_id = int(payload.get("sub", 0))
    user = db.get(User, user_id)
    if not user or user.status != "active":
        return None
    return user


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str | None, Depends(_extract_token)],
) -> User:
    if not token:
        raise AuthError()
    payload = decode_token(token, expected_type="access")
    user = db.get(User, int(payload.get("sub", 0)))
    if not user:
        raise AuthError("账号不存在或已被删除")
    if user.status != "active":
        raise AuthError("账号已被禁用，请联系管理员")
    return user


def get_context(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    x_company_id: Annotated[str | None, Header()] = None,
) -> CurrentContext:
    """解析当前企业与角色。管理员可切换企业（X-Company-Id）。"""
    member: Member | None = None
    company: Company | None = None

    if user.is_superadmin and x_company_id:
        company = db.get(Company, int(x_company_id))
        if not company:
            raise PermissionError_("指定的企业不存在")
        member = db.scalar(
            select(Member).where(Member.company_id == company.id, Member.user_id == user.id)
        )
    else:
        member = db.scalar(
            select(Member)
            .where(Member.user_id == user.id, Member.status == "active")
            .order_by(Member.id.asc())
        )
        if member:
            company = db.get(Company, member.company_id)

    if company is None:
        raise PermissionError_("当前账号还没有绑定企业，请先完成注册")
    if company.status != "active":
        raise PermissionError_("企业账号已被停用，请联系客服")

    plan, subscription = get_company_plan(db, company.id)
    return CurrentContext(
        user=user,
        company=company,
        member=member,
        role=member.role if member else ("owner" if user.is_superadmin else "member"),
        user_id=user.id,
        company_id=company.id,
        is_superadmin=bool(user.is_superadmin),
        plan=plan,
        subscription=subscription,
    )


def get_company_plan(db: Session, company_id: int) -> tuple[Plan | None, Subscription | None]:
    subscription = db.scalar(
        select(Subscription)
        .where(Subscription.company_id == company_id, Subscription.status == "active")
        .order_by(Subscription.end_at.desc().nulls_last())
    )
    if subscription and subscription.end_at and subscription.end_at < utcnow():
        subscription.status = "expired"
        db.flush()
        subscription = None

    plan = db.get(Plan, subscription.plan_id) if subscription and subscription.plan_id else None
    if plan is None:
        plan = db.scalar(select(Plan).where(Plan.code == "free"))
    return plan, subscription


def require_admin(context: Annotated[CurrentContext, Depends(get_context)]) -> CurrentContext:
    if not context.is_superadmin:
        raise PermissionError_("需要系统管理员权限")
    return context


def require_owner(context: Annotated[CurrentContext, Depends(get_context)]) -> CurrentContext:
    if not context.is_owner:
        raise PermissionError_("需要企业管理员权限")
    return context


def require_superadmin_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    if not user.is_superadmin:
        raise PermissionError_("需要系统管理员权限")
    return user


def check_ai_quota(db: Session, context: CurrentContext) -> None:
    """套餐 AI 额度校验：超限提示升级，绝不无限免费烧 API。"""
    from app.services.ai.usage_tracker import usage_tracker  # noqa: PLC0415

    allowed, stats = usage_tracker.check_quota(db, context.company_id)
    if not allowed:
        raise QuotaExceededError(
            f"本月 AI 额度已用完（{stats['calls']}/{stats['quota']} 次），升级套餐后可继续使用。"
        )


DbSession = Annotated[Session, Depends(get_db)]
Context = Annotated[CurrentContext, Depends(get_context)]
AdminContext = Annotated[CurrentContext, Depends(require_admin)]
OwnerContext = Annotated[CurrentContext, Depends(require_owner)]
SuperAdmin = Annotated[User, Depends(require_superadmin_user)]
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]


def now() -> datetime:
    return utcnow()


__all__ = [
    "ACCESS_COOKIE",
    "REFRESH_COOKIE",
    "AdminContext",
    "Context",
    "CurrentContext",
    "CurrentUser",
    "DbSession",
    "OptionalUser",
    "OwnerContext",
    "SuperAdmin",
    "check_ai_quota",
    "get_company_plan",
    "get_context",
    "get_current_user",
    "settings",
]

