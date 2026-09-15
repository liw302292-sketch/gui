"""平台级初始化：默认套餐、管理员账号、行业同步。

开发环境与首次启动会自动执行，生产环境第一次登录会提示修改密码。
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.company import Company, Member
from app.models.subscription import Plan
from app.models.user import User
from app.services import provisioning

logger = logging.getLogger("quote_engine.app")

DEFAULT_PLANS: tuple[dict, ...] = (
    {
        "code": "free",
        "name": "免费版",
        "tagline": "先把报价这件事跑起来",
        "price": 0,
        "billing_cycle": "forever",
        "max_users": 1,
        "max_quotes": 20,
        "ai_quota": 100,
        "storage_quota_mb": 200,
        "sort_order": 1,
        "features": ["quotes", "ai", "analytics"],
        "description": "每月 20 份报价、100 次 AI 识别，适合刚起步的广告制作团队。",
    },
    {
        "code": "pro",
        "name": "专业版",
        "tagline": "给每天都在报价的老板",
        "price": 399,
        "billing_cycle": "year",
        "max_users": 3,
        "max_quotes": 0,
        "ai_quota": 2000,
        "storage_quota_mb": 5120,
        "sort_order": 2,
        "features": ["quotes", "ai", "branding", "analytics", "members"],
        "description": "不限报价数量、2000 次 AI 识别、自定义报价单与多人协作。",
    },
    {
        "code": "enterprise",
        "name": "企业版",
        "tagline": "999-1999 / 年，按门店与人数确定",
        "price": 1999,
        "billing_cycle": "year",
        "max_users": 20,
        "max_quotes": 0,
        "ai_quota": 20000,
        "storage_quota_mb": 51200,
        "sort_order": 3,
        "features": ["quotes", "ai", "branding", "analytics", "members", "api", "private_deploy"],
        "description": "不限报价数量、20000 次 AI 识别、开放 API 与私有部署支持。按规模 999-1999 元 / 年，具体以合同为准。",
    },
)


def ensure_plans(db: Session) -> None:
    for payload in DEFAULT_PLANS:
        plan = db.scalar(select(Plan).where(Plan.code == payload["code"]))
        if plan is None:
            db.add(Plan(**payload))
        else:
            # 只补齐新字段，不覆盖管理员改过的价格与额度
            for key in ("features", "max_users", "storage_quota_mb", "tagline"):
                if getattr(plan, key, None) in (None, [], 0):
                    setattr(plan, key, payload[key])
    db.flush()


def ensure_superadmin(db: Session) -> User | None:
    if not settings.admin_email or not settings.admin_password:
        return None
    user = db.scalar(select(User).where(User.email == settings.admin_email.lower()))
    if user is None:
        user = User(
            email=settings.admin_email.lower(),
            name="平台管理员",
            password_hash=hash_password(settings.admin_password),
            is_superadmin=True,
            status="active",
            must_change_password=settings.is_production,
        )
        db.add(user)
        db.flush()
        logger.info("已创建超级管理员账号：%s", settings.admin_email)
    else:
        user.is_superadmin = True
        db.flush()
    return user


def ensure_admin_company(db: Session, admin: User | None = None) -> Company | None:
    """管理员也需要一个企业上下文，否则后台无法登录（前端会提示无企业）。"""
    if admin is None:
        return None
    existing = db.scalar(
        select(Company)
        .join(Member, Member.company_id == Company.id)
        .where(Member.user_id == admin.id)
        .limit(1)
    )
    if existing:
        return existing
    company = provisioning.provision_company(
        db,
        name="平台运营中心",
        industry_id="advertising",
        owner=admin,
        with_default_data=True,
    )
    logger.info("已为管理员创建运营企业 id=%s", company.id)
    return company


def bootstrap(db: Session) -> dict[str, object]:
    """启动时执行的幂等初始化。"""
    provisioning.ensure_industries(db)
    ensure_plans(db)
    admin = ensure_superadmin(db)
    company = ensure_admin_company(db, admin)
    db.flush()
    return {
        "industries": True,
        "plans": True,
        "admin_email": admin.email if admin else None,
        "admin_company_id": company.id if company else None,
    }
