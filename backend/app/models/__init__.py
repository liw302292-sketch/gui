"""SQLAlchemy 模型。所有业务表都带 company_id，实现企业级数据隔离。"""

from app.models.ai import AITask, AIUsage
from app.models.audit import AuditLog
from app.models.base import Base
from app.models.company import Company, Industry, Member, SystemSetting
from app.models.customer import Customer, Followup, Notification
from app.models.file import StoredFile
from app.models.product import PriceRule, Product, ProductCategory
from app.models.quote import Quote, QuoteItem, QuoteTemplate, QuoteVersion, QuoteView
from app.models.subscription import Order, Plan, Subscription
from app.models.user import User

__all__ = [
    "AITask",
    "AIUsage",
    "AuditLog",
    "Base",
    "Company",
    "Customer",
    "Followup",
    "Industry",
    "Member",
    "Notification",
    "Order",
    "Plan",
    "PriceRule",
    "Product",
    "ProductCategory",
    "Quote",
    "QuoteItem",
    "QuoteTemplate",
    "QuoteVersion",
    "QuoteView",
    "StoredFile",
    "Subscription",
    "SystemSetting",
    "User",
]

