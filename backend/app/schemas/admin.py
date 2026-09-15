"""管理员后台 Schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PlanCreate(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=100)
    tagline: str | None = None
    price: float = Field(default=0, ge=0)
    billing_cycle: str = Field(default="year", pattern="^(month|year|forever)$")
    max_users: int = Field(default=1, ge=1)
    max_quotes: int = Field(default=20, ge=0)
    ai_quota: int = Field(default=50, ge=0)
    storage_quota_mb: int = Field(default=200, ge=0)
    features: list[str] = Field(default_factory=list)
    is_active: bool = True
    is_public: bool = True
    sort_order: int = 100
    description: str | None = None


class PlanUpdate(BaseModel):
    name: str | None = None
    tagline: str | None = None
    price: float | None = Field(default=None, ge=0)
    billing_cycle: str | None = None
    max_users: int | None = Field(default=None, ge=1)
    max_quotes: int | None = Field(default=None, ge=0)
    ai_quota: int | None = Field(default=None, ge=0)
    storage_quota_mb: int | None = Field(default=None, ge=0)
    features: list[str] | None = None
    is_active: bool | None = None
    is_public: bool | None = None
    sort_order: int | None = None
    description: str | None = None


class CompanyAdminOut(BaseModel):
    id: int
    name: str
    industry_id: str
    status: str
    plan_code: str | None = None
    plan_name: str | None = None
    owner_name: str | None = None
    owner_email: str | None = None
    owner_phone: str | None = None
    member_count: int = 0
    quote_count: int = 0
    ai_calls: int = 0
    created_at: datetime | None = None


class CompanyStatusRequest(BaseModel):
    status: str = Field(pattern="^(active|disabled)$")
    reason: str | None = None


class UserAdminOut(BaseModel):
    id: int
    name: str
    email: str | None = None
    phone: str | None = None
    is_superadmin: bool = False
    status: str
    company_count: int = 0
    last_login_at: datetime | None = None
    created_at: datetime | None = None


class SystemSettingUpdate(BaseModel):
    key: str
    value: dict[str, Any]
    description: str | None = None

