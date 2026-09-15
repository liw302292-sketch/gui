"""认证相关 Schema。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, model_validator


class RegisterRequest(BaseModel):
    """注册：手机号 + 密码 或 邮箱 + 密码。"""

    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(default="", max_length=50)
    company_name: str = Field(default="", max_length=200)
    industry_id: str = Field(default="advertising", max_length=50)

    @model_validator(mode="after")
    def _require_identifier(self) -> "RegisterRequest":
        if not self.email and not self.phone:
            raise ValueError("请填写手机号或邮箱")
        return self


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=200, description="邮箱或手机号")
    password: str = Field(min_length=1, max_length=128)
    remember: bool = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    must_change_password: bool = False


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class UserProfile(BaseModel):
    id: int
    email: str | None = None
    phone: str | None = None
    name: str
    is_superadmin: bool = False
    must_change_password: bool = False
    created_at: datetime | None = None


class CompanyBrief(BaseModel):
    id: int
    name: str
    industry_id: str
    role: str
    plan_code: str | None = None
    plan_name: str | None = None
    ai_quota: int = 0
    logo_file_id: int | None = None


class MeResponse(BaseModel):
    user: UserProfile
    company: CompanyBrief | None = None
    unread_notifications: int = 0

