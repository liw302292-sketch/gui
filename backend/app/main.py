"""FastAPI 应用入口。"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.db import SessionLocal, engine
from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging
from app.core.rate_limit import enforce_rate_limit
from app.industry.registry import industry_registry
from app.services import bootstrap as bootstrap_service

logger = logging.getLogger("quote_engine.app")


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201
    setup_logging()
    logger.info("启动 %s（env=%s, ai_mode=%s）", settings.app_name, settings.app_env, settings.ai_mode)

    # 开发/测试环境自动建表，生产环境必须使用 alembic upgrade head
    if not settings.is_production:
        from app.models.base import Base  # noqa: PLC0415
        import app.models  # noqa: F401, PLC0415  确保所有模型已注册

        Base.metadata.create_all(bind=engine)

    from app.models.base import Base  # noqa: PLC0415
    import app.models  # noqa: F401, PLC0415

    with SessionLocal() as db:
        try:
            result = bootstrap_service.bootstrap(db)
            db.commit()
            logger.info("平台初始化完成：%s", result)
        except Exception:  # pragma: no cover - 启动阶段容错
            db.rollback()
            logger.exception("平台初始化失败，服务继续启动（请检查数据库配置）")

    yield
    logger.info("服务已停止")


app = FastAPI(
    title="Quote Engine API — 报价引擎",
    description=(
        "面向非标行业的 AI 报价基础设施。\n\n"
        "第一行业版本：广告标识 / 广告制作。\n\n"
        "核心原则：AI 只负责理解与提取，最终价格一律由后端规则引擎计算。"
    ),
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-PDF-Fallback"],
)


@app.middleware("http")
async def security_and_logging(request: Request, call_next):  # noqa: ANN001, ANN201
    started = time.perf_counter()

    # 基础 CSRF 防护：非安全方法校验来源
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("origin")
        if origin and origin not in settings.cors_origin_list:
            return JSONResponse(
                status_code=403,
                content={"ok": False, "code": "origin_rejected", "message": "请求来源不被信任"},
            )
        try:
            enforce_rate_limit(request, bucket="global")
        except Exception as exc:  # noqa: BLE001
            from app.core.errors import AppError  # noqa: PLC0415

            if isinstance(exc, AppError):
                return JSONResponse(
                    status_code=exc.status_code,
                    content={"ok": False, "code": exc.code, "message": exc.message},
                )
            raise

    response = await call_next(request)
    elapsed = (time.perf_counter() - started) * 1000
    response.headers["X-Process-Time"] = f"{elapsed:.1f}ms"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if elapsed > 3000:
        logger.warning("慢请求 %s %s %.0fms", request.method, request.url.path, elapsed)
    return response


register_exception_handlers(app)
app.include_router(api_router, prefix="/api")


@app.get("/api/health", tags=["系统"], summary="健康检查")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "status": "healthy",
        "app": settings.app_name,
        "env": settings.app_env,
        "ai_mode": settings.ai_mode,
        "version": app.version,
    }


@app.get("/api/meta", tags=["系统"], summary="平台元信息（行业模板、计价方式、状态字典）")
def meta() -> dict[str, Any]:
    return {
        "ok": True,
        "data": {
            "app_name": settings.app_name,
            "industries": industry_registry.summaries(),
            "ai_mode": settings.ai_mode,
            "pricing_modes": [
                {"value": "fixed", "label": "固定单价"},
                {"value": "area", "label": "面积计价"},
                {"value": "volume", "label": "体积计价"},
                {"value": "weight", "label": "重量计价"},
                {"value": "cost_plus", "label": "成本加成"},
                {"value": "margin", "label": "毛利率"},
            ],
            "quote_statuses": [
                {"value": "draft", "label": "草稿"},
                {"value": "sent", "label": "已发送"},
                {"value": "viewed", "label": "已查看"},
                {"value": "following", "label": "待跟进"},
                {"value": "won", "label": "已成交"},
                {"value": "void", "label": "已作废"},
            ],
            "units": ["平方米", "米", "个", "套", "张", "块", "项", "公斤", "件", "车"],
        },
    }


@app.get("/", tags=["系统"], include_in_schema=False)
def root() -> dict[str, Any]:
    """后端根路径。

    注意：这里只是后端 API 服务，界面在独立的前端地址上。
    直接访问 8000 端口会看到这段 JSON，属于预期行为。
    """
    return {
        "ok": True,
        "name": settings.app_name,
        "message": "这是后端 API 服务，界面请打开下面的 frontend 地址。",
        "frontend": settings.app_url,
        "app": f"{settings.app_url.rstrip('/')}/app",
        "admin": f"{settings.app_url.rstrip('/')}/admin",
        "docs": "/api/docs",
        "health": "/api/health",
    }
