"""报价相关 Schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RequirementItemIn(BaseModel):
    product_id: int | None = None
    category: str | None = None
    product_name: str = "未命名产品"
    spec: str | None = None
    unit: str = "平方米"
    quantity: float = 1
    width: float | None = None
    height: float | None = None
    depth: float | None = None
    weight: float | None = None
    material: str | None = None
    process: list[str] = Field(default_factory=list)
    installation: bool | None = None
    unit_price: float | None = None
    cost_price: float | None = None
    loss_rate: float | None = None
    labor_cost: float | None = None
    transport_cost: float | None = None
    other_cost: float | None = None
    remark: str | None = None


class RequirementIn(BaseModel):
    project_name: str | None = None
    customer_name: str | None = None
    customer_id: int | None = None
    items: list[RequirementItemIn] = Field(default_factory=list)
    transport_required: bool | None = None
    installation_required: bool | None = None
    installation_location: str | None = None
    deadline: str | None = None
    missing_fields: list[str] = Field(default_factory=list)
    confidence: float | None = None
    requirement_text: str | None = None
    template_id: int | None = None
    industry_id: str = "advertising"


class QuoteCreateRequest(RequirementIn):
    rounding_mode: str | None = None
    tax_rate: float | None = None
    discount_amount: float | None = None
    global_margin: float | None = None


class QuoteRecalculateRequest(BaseModel):
    items: list[RequirementItemIn]
    rounding_mode: str | None = None
    tax_rate: float | None = None
    discount_amount: float | None = None
    global_margin: float | None = None


class QuoteUpdateRequest(BaseModel):
    project_name: str | None = None
    customer_name: str | None = None
    customer_id: int | None = None
    notes: str | None = None
    payment_terms: str | None = None
    service_terms: str | None = None
    valid_until: datetime | None = None
    allow_download: bool | None = None
    status: str | None = None
    items: list[RequirementItemIn] | None = None
    rounding_mode: str | None = None
    tax_rate: float | None = None
    discount_amount: float | None = None
    global_margin: float | None = None
    change_note: str | None = None


class QuoteSendRequest(BaseModel):
    valid_days: int | None = Field(default=None, ge=1, le=365)
    password: str | None = Field(default=None, max_length=50)


class QuoteStatusRequest(BaseModel):
    status: str
    note: str | None = None


class QuoteListItem(BaseModel):
    id: int
    quote_no: str
    project_name: str
    customer_name: str | None = None
    customer_id: int | None = None
    status: str
    status_label: str
    total_amount: float
    total_cost: float = 0
    gross_margin: float = 0
    version_no: int = 1
    view_count: int = 0
    item_count: int = 0
    created_at: datetime | None = None
    valid_until: datetime | None = None
    last_viewed_at: datetime | None = None
    public_token: str | None = None
    source: str | None = None


class QuoteItemOut(BaseModel):
    id: int
    product_id: int | None = None
    category_name: str | None = None
    product_name: str
    spec: str | None = None
    unit: str
    quantity: float
    width: float | None = None
    height: float | None = None
    depth: float | None = None
    unit_price: float
    cost_price: float
    material_cost: float
    loss_cost: float
    labor_cost: float
    transport_cost: float
    other_cost: float
    total_cost: float
    subtotal: float
    profit_margin: float
    final_price: float
    formula: str | None = None
    breakdown: dict[str, Any] = Field(default_factory=dict)
    match_confidence: float | None = None
    remark: str | None = None


class QuoteDetail(BaseModel):
    id: int
    quote_no: str
    version_no: int
    project_name: str
    customer_name: str | None = None
    customer_id: int | None = None
    status: str
    status_label: str
    currency: str
    subtotal: float
    discount_amount: float
    tax_rate: float
    tax_amount: float
    total_amount: float
    total_cost: float
    gross_profit: float
    gross_margin: float
    tiers: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None
    payment_terms: str | None = None
    service_terms: str | None = None
    requirement_text: str | None = None
    requirement_json: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    confidence: float | None = None
    valid_until: datetime | None = None
    public_token: str | None = None
    public_url: str | None = None
    allow_download: bool = True
    view_count: int = 0
    first_viewed_at: datetime | None = None
    last_viewed_at: datetime | None = None
    created_at: datetime | None = None
    sent_at: datetime | None = None
    won_at: datetime | None = None
    items: list[QuoteItemOut] = Field(default_factory=list)


class QuoteTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    accent_color: str = "#635BFF"
    show_tiers: bool = True
    show_unit_price: bool = True
    payment_terms: str | None = None
    service_terms: str | None = None
    footer: str | None = None
    is_default: bool = False
    layout: dict[str, Any] = Field(default_factory=dict)


class QuoteTemplateUpdate(BaseModel):
    name: str | None = None
    accent_color: str | None = None
    show_tiers: bool | None = None
    show_unit_price: bool | None = None
    payment_terms: str | None = None
    service_terms: str | None = None
    footer: str | None = None
    is_default: bool | None = None
    layout: dict[str, Any] | None = None


class QuoteTemplateOut(BaseModel):
    id: int
    name: str
    accent_color: str
    show_tiers: bool
    show_unit_price: bool
    payment_terms: str | None = None
    service_terms: str | None = None
    footer: str | None = None
    is_default: bool
    layout: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class PublicQuoteView(BaseModel):
    ok: bool = True
    requires_password: bool = False
    quote: dict[str, Any] | None = None
    company: dict[str, Any] | None = None

