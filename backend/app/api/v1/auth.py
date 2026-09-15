"""认证接口：注册 / 登录 / 刷新 / 退出 / 当前用户 / 修改密码。"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request, Response, status
from sqlalchemy import or_, select

from app.core.config import settings
from app.core.cookies import clear_auth_cookies, set_auth_cookies
from app.core.deps import (
    ACCESS_COOKIE,
    REFRESH_COOKIE,
    Context,
    CurrentUser,
    DbSession,
)
from app.core.errors import AuthError, ConflictError, ValidationError_
from app.core.rate_limit import (
    clear_login_failures,
    enforce_rate_limit,
    is_login_locked,
    register_login_failure,
)
from app.core.security import (
    create_token,
    decode_token,
    hash_password,
    password_strength_error,
    verify_password,
)
from app.models.base import utcnow
from app.models.company import Company, Member
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    CompanyBrief,
    LoginRequest,
    MeResponse,
    RegisterRequest,
    TokenResponse,
    UserProfile,
)
from app.schemas.common import Message
from app.services import notification_service, provisioning

logger = logging.getLogger("quote_engine.app")

router = APIRouter()


def _normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    return phone.strip().replace(" ", "").replace("-", "")


def _issue_tokens(user: User, company: Company | None, role: str = "member", *, remember: bool = True) -> tuple[str, str, int]:
    access, _ = create_token(
        user.id,
        "access",
        company_id=company.id if company else None,
        role=role,
        extra={"email": user.email, "is_superadmin": user.is_superadmin},
    )
    refresh, _ = create_token(
        user.id,
        "refresh",
        company_id=company.id if company else None,
        role=role,
    )
    return access, refresh, settings.access_token_expire_minutes * 60


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED, summary="注册并自动创建企业")
def register(payload: RegisterRequest, request: Request, response: Response, db: DbSession) -> dict:
    enforce_rate_limit(
        request, bucket="register", limit=settings.register_rate_limit_per_hour, window=3600
    )

    strength_error = password_strength_error(payload.password)
    if strength_error:
        raise ValidationError_(strength_error)

    phone = _normalize_phone(payload.phone)
    if payload.email:
        exists = db.scalar(select(User).where(User.email == payload.email.lower()))
        if exists:
            raise ConflictError("该邮箱已经注册过了，请直接登录")
    if phone:
        exists = db.scalar(select(User).where(User.phone == phone))
        if exists:
            raise ConflictError("该手机号已经注册过了，请直接登录")

    user = User(
        email=payload.email.lower() if payload.email else None,
        phone=phone,
        name=payload.name or (payload.email.split("@")[0] if payload.email else f"用户{phone[-4:] if phone else ''}"),
        password_hash=hash_password(payload.password),
        status="active",
        must_change_password=False,
    )
    db.add(user)
    db.flush()

    company_name = payload.company_name.strip() or (f"{user.name}的广告制作" if user.name else "我的广告制作")
    company = provisioning.provision_company(
        db,
        name=company_name,
        industry_id=payload.industry_id,
        owner=user,
        with_default_data=True,
    )
    provisioning.welcome_notification(db, company, user)
    db.flush()

    access, refresh, expires_in = _issue_tokens(user, company, "owner", remember=True)
    set_auth_cookies(response, access_token=access, refresh_token=refresh, remember=True)
    logger.info("新用户注册成功 user=%s company=%s", user.id, company.id)
    return {
        "ok": True,
        "message": "注册成功，已为你创建企业",
        "data": {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": expires_in,
            "must_change_password": user.must_change_password,
            "company": {"id": company.id, "name": company.name, "industry_id": company.industry_id},
        },
    }


@router.post("/login", response_model=dict, summary="登录")
def login(payload: LoginRequest, request: Request, response: Response, db: DbSession) -> dict:
    enforce_rate_limit(request, bucket="login", limit=settings.login_rate_limit_per_5min, window=300)
    identifier = payload.identifier.strip()

    if is_login_locked(identifier):
        raise AuthError("登录失败次数过多，请稍后再试或联系管理员")

    phone = _normalize_phone(identifier)
    user = db.scalar(
        select(User).where(
            or_(User.email == identifier.lower(), User.phone == phone, User.phone == identifier)
        )
    )
    if user is None or not verify_password(payload.password, user.password_hash):
        failures = register_login_failure(identifier)
        logger.info("登录失败 identifier=%s 次数=%s", identifier, failures)
        raise AuthError("账号或密码不正确")
    if user.status != "active":
        raise AuthError("账号已被禁用，请联系管理员")

    clear_login_failures(identifier)
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = utcnow()

    member = db.scalar(
        select(Member)
        .where(Member.user_id == user.id, Member.status == "active")
        .order_by(Member.id.asc())
    )
    company = db.get(Company, member.company_id) if member else None
    role = member.role if member else "member"
    access, refresh, expires_in = _issue_tokens(user, company, role, remember=payload.remember)
    set_auth_cookies(response, access_token=access, refresh_token=refresh, remember=payload.remember)
    db.flush()

    return {
        "ok": True,
        "message": "登录成功",
        "data": TokenResponse(
            access_token=access,
            refresh_token=refresh,
            expires_in=expires_in,
            must_change_password=user.must_change_password,
        ).model_dump(),
    }


@router.post("/refresh", response_model=dict, summary="刷新令牌")
def refresh_token(
    request: Request,
    response: Response,
    db: DbSession,
    refresh_cookie: str | None = None,
) -> dict:
    token = refresh_cookie or request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise AuthError("登录状态已失效，请重新登录")
    payload = decode_token(token, expected_type="refresh")
    user = db.get(User, int(payload.get("sub", 0)))
    if not user or user.status != "active":
        raise AuthError("登录状态已失效，请重新登录")

    member = db.scalar(select(Member).where(Member.user_id == user.id, Member.status == "active"))
    company = db.get(Company, member.company_id) if member else None
    access, new_refresh, expires_in = _issue_tokens(
        user, company, member.role if member else "member", remember=True
    )
    set_auth_cookies(response, access_token=access, refresh_token=new_refresh, remember=True)
    return {
        "ok": True,
        "message": "刷新成功",
        "data": {"access_token": access, "refresh_token": new_refresh, "expires_in": expires_in},
    }


@router.post("/logout", response_model=Message, summary="退出登录")
def logout(response: Response) -> Message:
    clear_auth_cookies(response)
    return Message(message="已退出登录")


@router.get("/me", response_model=dict, summary="当前用户信息")
def me(context: Context, db: DbSession) -> dict:
    company_brief = None
    plan_code = plan_name = None
    ai_quota = 0
    if context.company:
        plan_code = context.plan.code if context.plan else None
        plan_name = context.plan.name if context.plan else None
        ai_quota = context.company.ai_monthly_quota
        company_brief = CompanyBrief(
            id=context.company.id,
            name=context.company.name,
            industry_id=context.company.industry_id,
            role=context.role,
            plan_code=plan_code,
            plan_name=plan_name,
            ai_quota=ai_quota,
            logo_file_id=context.company.logo_file_id,
        )
    unread = notification_service.unread_count(db, context.company_id, context.user_id)
    return {
        "ok": True,
        "data": MeResponse(
            user=UserProfile(
                id=context.user.id,
                email=context.user.email,
                phone=context.user.phone,
                name=context.user.name,
                is_superadmin=context.user.is_superadmin,
                must_change_password=context.user.must_change_password,
                created_at=context.user.created_at,
            ),
            company=company_brief,
            unread_notifications=unread,
        ).model_dump(),
    }


@router.post("/change-password", response_model=Message, summary="修改密码")
def change_password(
    payload: ChangePasswordRequest, user: CurrentUser, db: DbSession, response: Response
) -> Message:
    if not verify_password(payload.old_password, user.password_hash):
        raise ValidationError_("原密码不正确")
    strength_error = password_strength_error(payload.new_password)
    if strength_error:
        raise ValidationError_(strength_error)
    if payload.old_password == payload.new_password:
        raise ValidationError_("新密码不能与原密码相同")

    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    db.flush()
    clear_auth_cookies(response)
    return Message(message="密码已更新，请使用新密码重新登录")


@router.get("/check-availability", response_model=dict, summary="检查邮箱/手机号是否可用")
def check_availability(db: DbSession, email: str | None = None, phone: str | None = None) -> dict:
    result = {"email_available": True, "phone_available": True}
    if email:
        result["email_available"] = db.scalar(select(User.id).where(User.email == email.lower())) is None
    if phone:
        normalized = _normalize_phone(phone)
        result["phone_available"] = db.scalar(select(User.id).where(User.phone == normalized)) is None
    return {"ok": True, "data": result}
