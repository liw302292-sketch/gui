"""API 路由聚合。所有接口统一挂在 /api 下。"""

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    ai,
    auth,
    company,
    customers,
    files,
    followups,
    price_rules,
    products,
    quote_public,
    quote_templates,
    quotes,
    subscription,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(company.router, prefix="/company", tags=["企业"])
api_router.include_router(products.router, prefix="/products", tags=["产品与价格库"])
api_router.include_router(price_rules.router, prefix="/price-rules", tags=["价格规则"])
api_router.include_router(customers.router, prefix="/customers", tags=["客户"])
api_router.include_router(quotes.router, prefix="/quotes", tags=["报价"])
api_router.include_router(quote_templates.router, prefix="/quote-templates", tags=["报价模板"])
api_router.include_router(quote_public.router, prefix="/quote-public", tags=["公开报价"])
api_router.include_router(followups.router, prefix="/followups", tags=["跟进"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI"])
api_router.include_router(files.router, prefix="/files", tags=["文件"])
api_router.include_router(subscription.router, prefix="/subscription", tags=["套餐与订单"])
api_router.include_router(admin.router, prefix="/admin", tags=["管理员"])

