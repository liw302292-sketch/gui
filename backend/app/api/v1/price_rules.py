"""价格规则接口：规则完全由企业自己配置，规则引擎据此计算。"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import Context, DbSession, OwnerContext
from app.core.errors import NotFoundError
from app.models.product import PriceRule, Product, ProductCategory
from app.schemas.common import Message
from app.schemas.product import PriceRuleCreate, PriceRuleOut, PriceRuleUpdate

router = APIRouter()

RULE_TYPES = [
    {"value": "fixed", "label": "固定单价", "formula": "数量 × 单价"},
    {"value": "area", "label": "面积计价", "formula": "宽 × 高 × 数量 × 单价"},
    {"value": "volume", "label": "体积计价", "formula": "长 × 宽 × 高 × 数量 × 单价"},
    {"value": "weight", "label": "重量计价", "formula": "重量 × 单价"},
    {"value": "cost_plus", "label": "成本加成", "formula": "成本 × (1 + 加价率)"},
    {"value": "margin", "label": "毛利率", "formula": "售价 = 成本 / (1 - 毛利率)"},
    {"value": "loss", "label": "损耗", "formula": "材料成本 × 损耗率"},
    {"value": "labor", "label": "人工费", "formula": "固定人工费 或 面积 × 人工单价"},
    {"value": "transport", "label": "运输费", "formula": "固定运输费 或 按公里计算"},
    {"value": "condition", "label": "条件价格", "formula": "满足条件时使用指定价格，例如面积 > 20㎡ 用批发价"},
    {"value": "tiered", "label": "阶梯价格", "formula": "按数量/面积区间取不同单价"},
]


def _out(db: Session, rule: PriceRule) -> PriceRuleOut:
    product = db.get(Product, rule.product_id) if rule.product_id else None
    category = db.get(ProductCategory, rule.category_id) if rule.category_id else None
    return PriceRuleOut(
        id=rule.id,
        name=rule.name,
        product_id=rule.product_id,
        product_name=product.name if product else None,
        category_id=rule.category_id,
        category_name=category.name if category else None,
        rule_type=rule.rule_type,
        priority=rule.priority,
        conditions=rule.conditions or {},
        params=rule.params or {},
        description=rule.description,
        is_active=rule.is_active,
        created_at=rule.created_at,
    )


@router.get("/types", response_model=dict, summary="支持的规则类型")
def rule_types() -> dict:
    return {"ok": True, "data": RULE_TYPES}


@router.get("", response_model=dict, summary="规则列表")
def list_rules(context: Context, db: DbSession, include_inactive: bool = True) -> dict:
    stmt = select(PriceRule).where(PriceRule.company_id == context.company_id)
    if not include_inactive:
        stmt = stmt.where(PriceRule.is_active.is_(True))
    rules = list(db.scalars(stmt.order_by(PriceRule.priority.asc(), PriceRule.id.asc())))
    return {"ok": True, "data": [_out(db, rule).model_dump() for rule in rules]}


@router.post("", response_model=dict, summary="创建规则")
def create_rule(payload: PriceRuleCreate, context: OwnerContext, db: DbSession) -> dict:
    if payload.product_id:
        product = db.get(Product, payload.product_id)
        if not product or product.company_id != context.company_id:
            raise NotFoundError("产品不存在")
    if payload.category_id:
        category = db.get(ProductCategory, payload.category_id)
        if not category or category.company_id != context.company_id:
            raise NotFoundError("分类不存在")
    rule = PriceRule(company_id=context.company_id, **payload.model_dump())
    db.add(rule)
    db.flush()
    return {"ok": True, "message": "规则已创建", "data": _out(db, rule).model_dump()}


@router.put("/{rule_id}", response_model=dict, summary="更新规则")
def update_rule(rule_id: int, payload: PriceRuleUpdate, context: OwnerContext, db: DbSession) -> dict:
    rule = db.get(PriceRule, rule_id)
    if not rule or rule.company_id != context.company_id:
        raise NotFoundError("规则不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(rule, key, value)
    db.flush()
    return {"ok": True, "message": "规则已更新", "data": _out(db, rule).model_dump()}


@router.delete("/{rule_id}", response_model=Message, summary="删除规则")
def delete_rule(rule_id: int, context: OwnerContext, db: DbSession) -> Message:
    rule = db.get(PriceRule, rule_id)
    if not rule or rule.company_id != context.company_id:
        raise NotFoundError("规则不存在")
    db.delete(rule)
    return Message(message="规则已删除")
