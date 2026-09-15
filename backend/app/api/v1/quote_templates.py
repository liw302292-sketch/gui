"""报价模板：企业自定义报价单样式与条款。"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import Context, DbSession, OwnerContext
from app.core.errors import NotFoundError
from app.models.quote import QuoteTemplate
from app.schemas.common import Message
from app.schemas.quote import QuoteTemplateCreate, QuoteTemplateOut, QuoteTemplateUpdate

router = APIRouter()


def _out(template: QuoteTemplate) -> QuoteTemplateOut:
    return QuoteTemplateOut(
        id=template.id,
        name=template.name,
        accent_color=template.accent_color,
        show_tiers=template.show_tiers,
        show_unit_price=template.show_unit_price,
        payment_terms=template.payment_terms,
        service_terms=template.service_terms,
        footer=template.footer,
        is_default=template.is_default,
        layout=template.layout or {},
        created_at=template.created_at,
    )


@router.get("", response_model=dict, summary="模板列表")
def list_templates(context: Context, db: DbSession) -> dict:
    templates = list(
        db.scalars(
            select(QuoteTemplate)
            .where(QuoteTemplate.company_id == context.company_id)
            .order_by(QuoteTemplate.is_default.desc(), QuoteTemplate.id.asc())
        )
    )
    return {"ok": True, "data": [_out(template).model_dump() for template in templates]}


@router.post("", response_model=dict, summary="创建模板")
def create_template(payload: QuoteTemplateCreate, context: OwnerContext, db: DbSession) -> dict:
    if payload.is_default:
        for existing in db.scalars(
            select(QuoteTemplate).where(QuoteTemplate.company_id == context.company_id)
        ):
            existing.is_default = False
    template = QuoteTemplate(
        company_id=context.company_id,
        industry_id=context.company.industry_id,
        **payload.model_dump(),
    )
    db.add(template)
    db.flush()
    return {"ok": True, "message": "模板已创建", "data": _out(template).model_dump()}


@router.put("/{template_id}", response_model=dict, summary="更新模板")
def update_template(
    template_id: int, payload: QuoteTemplateUpdate, context: OwnerContext, db: DbSession
) -> dict:
    template = db.get(QuoteTemplate, template_id)
    if not template or template.company_id != context.company_id:
        raise NotFoundError("模板不存在")
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("is_default"):
        for existing in db.scalars(
            select(QuoteTemplate).where(QuoteTemplate.company_id == context.company_id)
        ):
            existing.is_default = False
    for key, value in updates.items():
        if value is not None:
            setattr(template, key, value)
    db.flush()
    return {"ok": True, "message": "模板已更新", "data": _out(template).model_dump()}


@router.delete("/{template_id}", response_model=Message, summary="删除模板")
def delete_template(template_id: int, context: OwnerContext, db: DbSession) -> Message:
    template = db.get(QuoteTemplate, template_id)
    if not template or template.company_id != context.company_id:
        raise NotFoundError("模板不存在")
    if template.is_default:
        raise NotFoundError("默认模板不能删除，请先设置其他模板为默认")
    db.delete(template)
    return Message(message="模板已删除")

