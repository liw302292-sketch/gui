"""单号生成：报价编号 QT-20260915-0001（前缀可配置），订单号 ORD-...。"""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.base import utcnow
from app.models.company import Company
from app.models.quote import Quote
from app.models.subscription import Order


def generate_quote_no(db: Session, company_id: int) -> str:
    company = db.get(Company, company_id)
    prefix = (company.quote_no_prefix if company and company.quote_no_prefix else "Q").strip() or "Q"
    today = utcnow().date()
    day_str = today.strftime("%Y%m%d")
    pattern = f"{prefix}-{day_str}-%"

    count = db.scalar(
        select(func.count()).select_from(Quote).where(Quote.company_id == company_id, Quote.quote_no.like(pattern))
    ) or 0
    for attempt in range(count + 1, count + 50):
        candidate = f"{prefix}-{day_str}-{attempt:04d}"
        exists = db.scalar(select(Quote.id).where(Quote.quote_no == candidate).limit(1))
        if not exists:
            return candidate
    return f"{prefix}-{day_str}-{int(utcnow().timestamp()) % 10000:04d}"


def generate_order_no(db: Session, day: date | None = None) -> str:
    day = day or utcnow().date()
    day_str = day.strftime("%Y%m%d")
    pattern = f"ORD-{day_str}-%"
    count = db.scalar(select(func.count()).select_from(Order).where(Order.order_no.like(pattern))) or 0
    for attempt in range(count + 1, count + 50):
        candidate = f"ORD-{day_str}-{attempt:04d}"
        if not db.scalar(select(Order.id).where(Order.order_no == candidate).limit(1)):
            return candidate
    return f"ORD-{day_str}-{int(utcnow().timestamp()) % 10000:04d}"

