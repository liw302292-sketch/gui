"""企业初始化：新注册或 seed 时按行业模板灌入分类、产品、规则、报价模板、套餐。

这是「行业模板 → 企业数据」的唯一入口，换行业只换模板，不改业务代码。
"""

from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.industry.registry import get_template
from app.models.base import utcnow
from app.models.company import Company, Member
from app.models.product import PriceRule, Product, ProductCategory
from app.models.quote import QuoteTemplate
from app.models.subscription import Plan, Subscription
from app.models.user import User
from app.services import notification_service

logger = logging.getLogger("quote_engine.app")


def ensure_industries(db: Session) -> None:
    """把代码中的行业模板同步到数据库（供前端筛选与未来扩展）。"""
    from app.models.company import Industry  # noqa: PLC0415
    from app.industry.registry import industry_registry  # noqa: PLC0415

    for template in industry_registry.all():
        existing = db.get(Industry, template.code)
        if existing is None:
            db.add(
                Industry(
                    id=template.code,
                    name=template.name,
                    description=template.description,
                    is_active=template.available,
                    sort_order=template.sort_order,
                )
            )
        else:
            existing.name = template.name
            existing.description = template.description
            existing.is_active = template.available
            existing.sort_order = template.sort_order
    db.flush()


def provision_company(
    db: Session,
    *,
    name: str,
    industry_id: str = "advertising",
    owner: User | None = None,
    with_default_data: bool = True,
    slug: str | None = None,
) -> Company:
    """创建企业并灌入行业模板默认数据。"""
    template = get_template(industry_id)
    company = Company(
        name=name,
        short_name=name[:20],
        industry_id=template.code,
        slug=slug,
        default_payment_terms=template.payment_terms,
        default_service_terms=template.service_terms,
        default_footer=template.footer,
        rounding_mode="10",
        quote_no_prefix="Q",
        ai_monthly_quota=300,
        status="active",
        onboarded_at=utcnow(),
    )
    db.add(company)
    db.flush()

    if owner is not None:
        db.add(
            Member(
                company_id=company.id,
                user_id=owner.id,
                role="owner",
                status="active",
                nickname=owner.name or None,
            )
        )

    _create_default_quote_template(db, company, template.quote_template_name)
    if with_default_data:
        create_template_data(db, company=company, industry_id=template.code)
    _attach_free_plan(db, company)
    db.flush()
    logger.info("企业已初始化 id=%s name=%s industry=%s", company.id, company.name, template.code)
    return company


def _create_default_quote_template(db: Session, company: Company, name: str) -> QuoteTemplate:
    template = QuoteTemplate(
        company_id=company.id,
        industry_id=company.industry_id,
        name=name,
        is_default=True,
        accent_color="#635BFF",
        show_tiers=True,
        show_unit_price=True,
        payment_terms=company.default_payment_terms,
        service_terms=company.default_service_terms,
        footer=company.default_footer,
        layout={"layout": "classic", "show_logo": True},
    )
    db.add(template)
    db.flush()
    return template


def create_template_data(db: Session, *, company: Company, industry_id: str, price_factor: float = 1.0) -> dict[str, int]:
    """按行业模板创建分类、产品与价格规则。"""
    template = get_template(industry_id)
    category_map: dict[str, ProductCategory] = {}
    for index, name in enumerate(template.categories):
        category = ProductCategory(
            company_id=company.id,
            industry_id=template.code,
            name=name,
            code=f"c{index + 1}",
            sort_order=index,
            is_active=True,
        )
        db.add(category)
        category_map[name] = category
    db.flush()

    for index, seed in enumerate(template.products):
        category = category_map.get(seed.category)
        db.add(
            Product(
                company_id=company.id,
                industry_id=template.code,
                category_id=category.id if category else None,
                name=seed.name,
                model=seed.model or None,
                spec=seed.spec or None,
                unit=seed.unit,
                pricing_mode=seed.pricing_mode,
                cost_price=round(seed.cost_price * price_factor, 4),
                default_price=round(seed.default_price * price_factor, 4),
                min_price=round(seed.cost_price * price_factor * 1.05, 2),
                loss_rate=seed.loss_rate,
                labor_cost=seed.labor_cost,
                labor_price_per_unit=seed.labor_price_per_unit,
                transport_cost=seed.transport_cost,
                other_cost=seed.other_cost,
                min_profit_margin=seed.min_profit_margin,
                markup_rate=seed.markup_rate,
                remark=seed.remark or None,
                sort_order=index,
                is_active=True,
            )
        )

    for seed_rule in template.rules:
        category = category_map.get(seed_rule.category)
        db.add(
            PriceRule(
                company_id=company.id,
                category_id=category.id if category else None,
                name=seed_rule.name,
                rule_type=seed_rule.rule_type,
                priority=seed_rule.priority,
                conditions=seed_rule.conditions,
                params=seed_rule.params,
                description=seed_rule.description,
                is_active=True,
            )
        )
    db.flush()
    return {"categories": len(category_map), "products": len(template.products), "rules": len(template.rules)}


def _attach_free_plan(db: Session, company: Company) -> Subscription | None:
    plan = db.scalar(select(Plan).where(Plan.code == "free"))
    if plan is None:
        return None
    subscription = Subscription(
        company_id=company.id,
        plan_id=plan.id,
        status="active",
        start_at=utcnow(),
        end_at=utcnow() + timedelta(days=3650),
        auto_renew=True,
    )
    db.add(subscription)
    company.ai_monthly_quota = plan.ai_quota or 100
    db.flush()
    return subscription


def welcome_notification(db: Session, company: Company, user: User) -> None:
    notification_service.push(
        db,
        company_id=company.id,
        user_id=user.id,
        title="欢迎使用报价引擎",
        content="建议先完善产品价格库，然后上传一张客户需求截图，体验 30 秒出报价。",
        type="welcome",
        link="/app/quotes/new",
    )
    db.flush()

