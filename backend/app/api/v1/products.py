"""产品与价格库接口：分类、产品、Excel 导入。"""

from __future__ import annotations

from fastapi import APIRouter, File, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import Context, DbSession, OwnerContext
from app.core.errors import ConflictError, NotFoundError
from app.models.product import PriceRule, Product, ProductCategory
from app.schemas.common import Message
from app.schemas.product import (
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
    ProductCreate,
    ProductOut,
    ProductUpdate,
)
from app.services import audit_service, file_service
from app.services.pricing.profit_calculator import effective_margin

router = APIRouter()

IMPORT_COLUMNS = {
    "分类": "category",
    "产品名称": "name",
    "名称": "name",
    "型号": "model",
    "规格": "spec",
    "单位": "unit",
    "计价方式": "pricing_mode",
    "成本": "cost_price",
    "成本价": "cost_price",
    "默认报价": "default_price",
    "报价": "default_price",
    "损耗率": "loss_rate",
    "人工费": "labor_cost",
    "人工单价": "labor_price_per_unit",
    "运输费": "transport_cost",
    "最低利润率": "min_profit_margin",
    "备注": "remark",
}

PRICING_MODE_ALIASES = {
    "固定": "fixed",
    "固定单价": "fixed",
    "按个": "fixed",
    "面积": "area",
    "按面积": "area",
    "体积": "volume",
    "重量": "weight",
    "成本加成": "cost_plus",
    "毛利率": "margin",
}


def _product_out(db: Session, product: Product, category_name: str | None = None) -> ProductOut:
    if category_name is None and product.category_id:
        category = db.get(ProductCategory, product.category_id)
        category_name = category.name if category else None
    cost = float(product.cost_price or 0)
    price = float(product.default_price or 0)
    return ProductOut(
        id=product.id,
        name=product.name,
        category_id=product.category_id,
        category_name=category_name,
        model=product.model,
        spec=product.spec,
        unit=product.unit,
        pricing_mode=product.pricing_mode,
        cost_price=cost,
        default_price=price,
        min_price=float(product.min_price or 0),
        loss_rate=float(product.loss_rate or 0),
        labor_cost=float(product.labor_cost or 0),
        labor_price_per_unit=float(product.labor_price_per_unit or 0),
        transport_cost=float(product.transport_cost or 0),
        other_cost=float(product.other_cost or 0),
        min_profit_margin=float(product.min_profit_margin or 0),
        markup_rate=float(product.markup_rate or 0),
        tax_rate=float(product.tax_rate or 0),
        gross_margin_preview=float(effective_margin(price, cost)),
        is_active=product.is_active,
        remark=product.remark,
        created_at=product.created_at,
    )


# ----------------------------------------------------------------------
# 分类
# ----------------------------------------------------------------------
@router.get("/categories", response_model=dict, summary="分类列表")
def list_categories(context: Context, db: DbSession, include_inactive: bool = False) -> dict:
    stmt = select(ProductCategory).where(ProductCategory.company_id == context.company_id)
    if not include_inactive:
        stmt = stmt.where(ProductCategory.is_active.is_(True))
    categories = list(db.scalars(stmt.order_by(ProductCategory.sort_order.asc(), ProductCategory.id.asc())))
    counts = dict(
        db.execute(
            select(Product.category_id, func.count(Product.id))
            .where(Product.company_id == context.company_id)
            .group_by(Product.category_id)
        ).all()
    )
    return {
        "ok": True,
        "data": [
            CategoryOut(
                id=category.id,
                name=category.name,
                code=category.code,
                description=category.description,
                sort_order=category.sort_order,
                is_active=category.is_active,
                product_count=int(counts.get(category.id, 0)),
            ).model_dump()
            for category in categories
        ],
    }


@router.post("/categories", response_model=dict, summary="创建分类")
def create_category(payload: CategoryCreate, context: OwnerContext, db: DbSession) -> dict:
    exists = db.scalar(
        select(ProductCategory).where(
            ProductCategory.company_id == context.company_id, ProductCategory.name == payload.name
        )
    )
    if exists:
        raise ConflictError("该分类已存在")
    category = ProductCategory(
        company_id=context.company_id,
        industry_id=context.company.industry_id,
        **payload.model_dump(),
    )
    db.add(category)
    db.flush()
    return {"ok": True, "message": "分类已创建", "data": {"id": category.id}}


@router.put("/categories/{category_id}", response_model=dict, summary="更新分类")
def update_category(category_id: int, payload: CategoryUpdate, context: OwnerContext, db: DbSession) -> dict:
    category = db.get(ProductCategory, category_id)
    if not category or category.company_id != context.company_id:
        raise NotFoundError("分类不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(category, key, value)
    db.flush()
    return {"ok": True, "message": "分类已更新"}


@router.delete("/categories/{category_id}", response_model=Message, summary="删除分类")
def delete_category(category_id: int, context: OwnerContext, db: DbSession) -> Message:
    category = db.get(ProductCategory, category_id)
    if not category or category.company_id != context.company_id:
        raise NotFoundError("分类不存在")
    count = db.scalar(
        select(func.count()).select_from(Product).where(Product.category_id == category_id)
    ) or 0
    if count:
        raise ConflictError(f"该分类下还有 {count} 个产品，请先移动或删除产品")
    db.delete(category)
    return Message(message="分类已删除")


# ----------------------------------------------------------------------
# 产品
# ----------------------------------------------------------------------
@router.get("", response_model=dict, summary="产品列表")
def list_products(
    context: Context,
    db: DbSession,
    keyword: str | None = None,
    category_id: int | None = None,
    pricing_mode: str | None = None,
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
) -> dict:
    stmt = select(Product).where(Product.company_id == context.company_id)
    if keyword:
        stmt = stmt.where(Product.name.ilike(f"%{keyword}%") | Product.model.ilike(f"%{keyword}%"))
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    if pricing_mode:
        stmt = stmt.where(Product.pricing_mode == pricing_mode)
    if is_active is not None:
        stmt = stmt.where(Product.is_active.is_(is_active))

    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    products = list(
        db.scalars(
            stmt.order_by(Product.sort_order.asc(), Product.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    category_ids = {product.category_id for product in products if product.category_id}
    names = {
        category.id: category.name
        for category in db.scalars(select(ProductCategory).where(ProductCategory.id.in_(category_ids)))
    } if category_ids else {}

    return {
        "ok": True,
        "data": {
            "items": [
                _product_out(db, product, names.get(product.category_id)).model_dump()
                for product in products
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/{product_id}", response_model=dict, summary="产品详情")
def get_product(product_id: int, context: Context, db: DbSession) -> dict:
    product = db.get(Product, product_id)
    if not product or product.company_id != context.company_id:
        raise NotFoundError("产品不存在")
    return {"ok": True, "data": _product_out(db, product).model_dump()}


@router.post("", response_model=dict, summary="创建产品")
def create_product(payload: ProductCreate, context: Context, db: DbSession) -> dict:
    if payload.category_id:
        category = db.get(ProductCategory, payload.category_id)
        if not category or category.company_id != context.company_id:
            raise NotFoundError("分类不存在")
    product = Product(
        company_id=context.company_id,
        industry_id=context.company.industry_id,
        **payload.model_dump(),
    )
    db.add(product)
    db.flush()
    audit_service.record(
        db,
        company_id=context.company_id,
        user_id=context.user_id,
        user_name=context.user.name,
        action="product.create",
        target_type="product",
        target_id=product.id,
        summary=f"新增产品 {product.name}",
    )
    return {"ok": True, "message": "产品已创建", "data": _product_out(db, product).model_dump()}


@router.put("/{product_id}", response_model=dict, summary="更新产品")
def update_product(product_id: int, payload: ProductUpdate, context: Context, db: DbSession) -> dict:
    product = db.get(Product, product_id)
    if not product or product.company_id != context.company_id:
        raise NotFoundError("产品不存在")
    before = _product_out(db, product).model_dump(mode="json")
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("category_id"):
        category = db.get(ProductCategory, updates["category_id"])
        if not category or category.company_id != context.company_id:
            raise NotFoundError("分类不存在")
    for key, value in updates.items():
        if value is not None:
            setattr(product, key, value)
    db.flush()
    audit_service.record(
        db,
        company_id=context.company_id,
        user_id=context.user_id,
        user_name=context.user.name,
        action="product.update",
        target_type="product",
        target_id=product.id,
        summary=f"修改产品 {product.name}",
        before=before,
        after=_product_out(db, product).model_dump(mode="json"),
    )
    return {"ok": True, "message": "产品已更新", "data": _product_out(db, product).model_dump()}


@router.delete("/{product_id}", response_model=Message, summary="删除产品")
def delete_product(product_id: int, context: OwnerContext, db: DbSession) -> Message:
    product = db.get(Product, product_id)
    if not product or product.company_id != context.company_id:
        raise NotFoundError("产品不存在")
    used = db.scalar(select(func.count()).select_from(PriceRule).where(PriceRule.product_id == product_id)) or 0
    if used:
        raise ConflictError("该产品还有关联的价格规则，请先处理规则或改为停用")
    db.delete(product)
    return Message(message="产品已删除")


@router.post("/import", response_model=dict, summary="Excel/CSV 导入产品")
def import_products(
    context: OwnerContext,
    db: DbSession,
    file: UploadFile = File(...),
    create_missing_categories: bool = True,
) -> dict:
    data = file.file.read()
    record = file_service.save_upload(
        db,
        company_id=context.company_id,
        user_id=context.user_id,
        filename=file.filename or "import.xlsx",
        content_type=file.content_type,
        data=data,
        kind="sheet",
    )
    try:
        rows = file_service.extract_spreadsheet(data)
    except Exception as exc:  # noqa: BLE001
        raise ConflictError("无法读取该表格文件，请确认为 .xlsx 或 .csv 格式") from exc

    category_cache: dict[str, ProductCategory] = {
        category.name: category
        for category in db.scalars(select(ProductCategory).where(ProductCategory.company_id == context.company_id))
    }

    created, updated, skipped, errors = 0, 0, 0, []
    for index, row in enumerate(rows, start=2):
        mapped: dict[str, object] = {}
        for raw_key, value in row.items():
            key = IMPORT_COLUMNS.get(str(raw_key).strip())
            if key and value not in (None, ""):
                mapped[key] = value
        name = str(mapped.get("name") or "").strip()
        if not name:
            skipped += 1
            continue

        category_name = str(mapped.get("category") or "").strip()
        category = category_cache.get(category_name)
        if category_name and category is None and create_missing_categories:
            category = ProductCategory(
                company_id=context.company_id,
                industry_id=context.company.industry_id,
                name=category_name,
                sort_order=len(category_cache),
            )
            db.add(category)
            db.flush()
            category_cache[category_name] = category

        def number(key: str, default: float = 0.0) -> float:
            value = mapped.get(key)
            if value in (None, ""):
                return default
            try:
                return float(str(value).replace("%", "").replace(",", "").strip())
            except ValueError:
                return default

        mode_raw = str(mapped.get("pricing_mode") or "area").strip()
        mode = PRICING_MODE_ALIASES.get(mode_raw, mode_raw if mode_raw in {
            "fixed", "area", "volume", "weight", "cost_plus", "margin", "tiered"
        } else "area")

        loss_rate = number("loss_rate")
        if loss_rate > 1:
            loss_rate = loss_rate / 100
        margin = number("min_profit_margin", 0.25)
        if margin > 1:
            margin = margin / 100

        product = db.scalar(
            select(Product).where(Product.company_id == context.company_id, Product.name == name)
        )
        payload = {
            "category_id": category.id if category else None,
            "unit": str(mapped.get("unit") or "平方米"),
            "pricing_mode": mode,
            "cost_price": number("cost_price"),
            "default_price": number("default_price"),
            "loss_rate": loss_rate,
            "labor_cost": number("labor_cost"),
            "labor_price_per_unit": number("labor_price_per_unit"),
            "transport_cost": number("transport_cost"),
            "min_profit_margin": margin,
            "model": str(mapped.get("model") or "") or None,
            "spec": str(mapped.get("spec") or "") or None,
            "remark": str(mapped.get("remark") or "") or None,
        }
        if product is None:
            db.add(
                Product(
                    company_id=context.company_id,
                    industry_id=context.company.industry_id,
                    name=name,
                    **payload,
                )
            )
            created += 1
        else:
            for key, value in payload.items():
                setattr(product, key, value)
            updated += 1
        if index > 2000:
            errors.append("单次最多导入 2000 行，仅处理了前 2000 行")
            break

    db.flush()
    audit_service.record(
        db,
        company_id=context.company_id,
        user_id=context.user_id,
        user_name=context.user.name,
        action="product.import",
        target_type="product",
        summary=f"导入产品：新增 {created}，更新 {updated}，跳过 {skipped}",
    )
    return {
        "ok": True,
        "message": f"导入完成：新增 {created} 个，更新 {updated} 个，跳过 {skipped} 行",
        "data": {"created": created, "updated": updated, "skipped": skipped, "file_id": record.id, "errors": errors},
    }


@router.get("/template/download", response_model=dict, summary="获取导入模板列说明")
def import_template() -> dict:
    return {
        "ok": True,
        "data": {
            "columns": list(IMPORT_COLUMNS.keys()),
            "example": {
                "分类": "门头",
                "产品名称": "铝塑板门头",
                "单位": "平方米",
                "计价方式": "面积",
                "成本": 145,
                "默认报价": 280,
                "损耗率": 0.06,
                "人工单价": 55,
                "最低利润率": 0.28,
                "备注": "4mm 铝塑板",
            },
        },
    }
