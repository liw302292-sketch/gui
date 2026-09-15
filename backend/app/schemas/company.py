"""企业设置 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    short_name: str | None = Field(default=None, max_length=100)
    contact_name: str | None = Field(default=None, max_length=100)
    contact_phone: str | None = Field(default=None, max_length=50)
    contact_wechat: str | None = Field(default=None, max_length=80)
    address: str | None = None
    credit_code: str | None = Field(default=None, max_length=50)
    default_tax_rate: float | None = Field(default=None, ge=0, le=1)
    default_profit_margin: float | None = Field(default=None, ge=0, le=0.95)
    default_quote_valid_days: int | None = Field(default=None, ge=1, le=365)
    default_payment_terms: str | None = None
    default_service_terms: str | None = None
    default_footer: str | None = None
    rounding_mode: str | None = Field(default=None, pattern="^(none|1|10|100|psychological)$")
    quote_no_prefix: str | None = Field(default=None, max_length=10)
    logo_file_id: int | None = None


class CompanyDetail(BaseModel):
    id: int
    name: str
    short_name: str | None = None
    industry_id: str
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_wechat: str | None = None
    address: str | None = None
    credit_code: str | None = None
    default_tax_rate: float
    default_profit_margin: float
    default_quote_valid_days: int
    default_payment_terms: str | None = None
    default_service_terms: str | None = None
    default_footer: str | None = None
    rounding_mode: str
    quote_no_prefix: str
    ai_monthly_quota: int
    logo_file_id: int | None = None
    status: str

