"""统计服务：Dashboard、转化漏斗、趋势、企业数据报表。"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.base import utcnow
from app.models.customer import Customer, Followup
from app.models.quote import Quote, QuoteItem, QuoteView
from app.services.quote_service import QUOTE_STATUS_LABELS


def _day_start(day: date) -> datetime:
    return datetime.combine(day, datetime.min.time())


def _sum_amount(db: Session, company_id: int, *, since: datetime | None = None, statuses: tuple[str, ...] = ()) -> float:
    stmt = select(func.coalesce(func.sum(Quote.total_amount), 0)).where(Quote.company_id == company_id)
    if since:
        stmt = stmt.where(Quote.created_at >= since)
    if statuses:
        stmt = stmt.where(Quote.status.in_(statuses))
    return float(db.scalar(stmt) or 0)


def _count(db: Session, model, company_id: int, **filters) -> int:  # noqa: ANN001
    stmt = select(func.count()).select_from(model).where(model.company_id == company_id)
    for key, value in filters.items():
        column = getattr(model, key)
        stmt = stmt.where(column == value)
    return int(db.scalar(stmt) or 0)


def dashboard(db: Session, *, company_id: int, user_name: str) -> dict[str, Any]:
    today = utcnow().date()
    today_start = _day_start(today)
    month_start = datetime(today.year, today.month, 1)

    today_quotes = int(
        db.scalar(
            select(func.count())
            .select_from(Quote)
            .where(Quote.company_id == company_id, Quote.created_at >= today_start)
        )
        or 0
    )
    pending_followups = int(
        db.scalar(
            select(func.count())
            .select_from(Customer)
            .where(
                Customer.company_id == company_id,
                Customer.next_followup_at.is_not(None),
                Customer.next_followup_at <= _day_start(today + timedelta(days=1)),
                Customer.status.notin_(("won", "lost")),
            )
        )
        or 0
    )
    month_quote_amount = _sum_amount(db, company_id, since=month_start)
    month_deal_amount = _sum_amount(db, company_id, since=month_start, statuses=("won",))
    total_quotes = _count(db, Quote, company_id)
    total_deals = _count(db, Quote, company_id, status="won")

    # ---- 近 14 天趋势 ----
    days = 14
    quote_trend: list[dict[str, Any]] = []
    deal_trend: list[dict[str, Any]] = []
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        start = _day_start(day)
        end = start + timedelta(days=1)
        amount = float(
            db.scalar(
                select(func.coalesce(func.sum(Quote.total_amount), 0)).where(
                    Quote.company_id == company_id, Quote.created_at >= start, Quote.created_at < end
                )
            )
            or 0
        )
        count = int(
            db.scalar(
                select(func.count())
                .select_from(Quote)
                .where(Quote.company_id == company_id, Quote.created_at >= start, Quote.created_at < end)
            )
            or 0
        )
        won = float(
            db.scalar(
                select(func.coalesce(func.sum(Quote.total_amount), 0)).where(
                    Quote.company_id == company_id,
                    Quote.status == "won",
                    Quote.won_at.is_not(None),
                    Quote.won_at >= start,
                    Quote.won_at < end,
                )
            )
            or 0
        )
        label = day.strftime("%m-%d")
        quote_trend.append({"date": label, "amount": amount, "count": count})
        deal_trend.append({"date": label, "amount": won})

    # ---- 转化漏斗：报价 → 查看 → 跟进 → 成交 ----
    quoted = total_quotes
    viewed = int(
        db.scalar(
            select(func.count(func.distinct(QuoteView.quote_id))).where(QuoteView.company_id == company_id)
        )
        or 0
    )
    followed = int(
        db.scalar(
            select(func.count(func.distinct(Followup.quote_id))).where(
                Followup.company_id == company_id, Followup.quote_id.is_not(None)
            )
        )
        or 0
    )
    funnel = [
        {"stage": "报价", "value": quoted},
        {"stage": "查看", "value": viewed},
        {"stage": "跟进", "value": followed},
        {"stage": "成交", "value": total_deals},
    ]

    # ---- 今日待跟进 ----
    followups = db.scalars(
        select(Customer)
        .where(
            Customer.company_id == company_id,
            Customer.next_followup_at.is_not(None),
            Customer.next_followup_at <= _day_start(today + timedelta(days=1)),
            Customer.status.notin_(("won", "lost")),
        )
        .order_by(Customer.next_followup_at.asc())
        .limit(8)
    )
    today_followups = [
        {
            "id": customer.id,
            "name": customer.name,
            "contact_name": customer.contact_name,
            "phone": customer.phone,
            "status": customer.status,
            "quote_count": customer.quote_count,
            "total_amount": float(customer.total_amount or 0),
            "next_followup_at": customer.next_followup_at.isoformat() if customer.next_followup_at else None,
        }
        for customer in followups
    ]

    recent = db.scalars(
        select(Quote).where(Quote.company_id == company_id).order_by(Quote.created_at.desc()).limit(6)
    )
    recent_quotes = [
        {
            "id": quote.id,
            "quote_no": quote.quote_no,
            "project_name": quote.project_name,
            "customer_name": quote.customer_name,
            "status": quote.status,
            "status_label": QUOTE_STATUS_LABELS.get(quote.status, quote.status),
            "total_amount": float(quote.total_amount or 0),
            "created_at": quote.created_at.isoformat() if quote.created_at else None,
            "view_count": quote.view_count,
        }
        for quote in recent
    ]

    high_value = db.scalars(
        select(Quote)
        .where(Quote.company_id == company_id, Quote.status.notin_(("void", "draft")))
        .order_by(Quote.total_amount.desc())
        .limit(5)
    )
    high_value_quotes = [
        {
            "id": quote.id,
            "quote_no": quote.quote_no,
            "project_name": quote.project_name,
            "customer_name": quote.customer_name,
            "status": quote.status,
            "status_label": QUOTE_STATUS_LABELS.get(quote.status, quote.status),
            "total_amount": float(quote.total_amount or 0),
        }
        for quote in high_value
    ]

    hour = utcnow().hour
    greeting = "早上好" if hour < 11 else ("下午好" if hour < 18 else "晚上好")

    return {
        "greeting": f"{greeting}，{user_name}",
        "stats": {
            "today_quotes": today_quotes,
            "pending_followups": pending_followups,
            "month_quote_amount": month_quote_amount,
            "month_deal_amount": month_deal_amount,
            "total_quotes": total_quotes,
            "total_deals": total_deals,
            "conversion_rate": round(total_deals / total_quotes, 4) if total_quotes else 0,
        },
        "quote_trend": quote_trend,
        "deal_trend": deal_trend,
        "funnel": funnel,
        "today_followups": today_followups,
        "recent_quotes": recent_quotes,
        "high_value_quotes": high_value_quotes,
        "followup_hint": (
            f"今日有 {pending_followups} 个客户需要跟进。" if pending_followups else "今天没有需要跟进的客户。"
        ),
    }


def company_analytics(db: Session, *, company_id: int, period: str = "month") -> dict[str, Any]:
    """企业统计：日 / 周 / 月。"""
    today = utcnow().date()
    if period == "day":
        since = _day_start(today)
    elif period == "week":
        since = _day_start(today - timedelta(days=today.weekday()))
    else:
        since = datetime(today.year, today.month, 1)
        period = "month"

    quotes = list(
        db.scalars(select(Quote).where(Quote.company_id == company_id, Quote.created_at >= since))
    )
    quote_count = len(quotes)
    quote_amount = float(sum((quote.total_amount or 0) for quote in quotes))
    won_quotes = [quote for quote in quotes if quote.status == "won"]
    won_amount = float(sum((quote.total_amount or 0) for quote in won_quotes))
    margins = [float(quote.gross_margin or 0) for quote in quotes if quote.total_amount]
    followup_count = int(
        db.scalar(
            select(func.count())
            .select_from(Followup)
            .where(Followup.company_id == company_id, Followup.created_at >= since)
        )
        or 0
    )
    new_customers = int(
        db.scalar(
            select(func.count())
            .select_from(Customer)
            .where(Customer.company_id == company_id, Customer.created_at >= since)
        )
        or 0
    )
    category_rows = db.execute(
        select(
            func.coalesce(QuoteItem.category_name, "其他"),
            func.count(),
            func.coalesce(func.sum(QuoteItem.final_price), 0),
        )
        .select_from(QuoteItem)
        .join(Quote, Quote.id == QuoteItem.quote_id)
        .where(Quote.company_id == company_id, Quote.created_at >= since)
        .group_by(QuoteItem.category_name)
    )
    by_category = [
        {"category": name or "其他", "count": int(count), "amount": float(amount or 0)}
        for name, count, amount in category_rows
    ]

    status_breakdown = [
        {"status": status, "label": label, "count": _count(db, Quote, company_id, status=status)}
        for status, label in QUOTE_STATUS_LABELS.items()
    ]

    return {
        "period": period,
        "since": since.isoformat(),
        "quote_count": quote_count,
        "quote_amount": quote_amount,
        "won_count": len(won_quotes),
        "won_amount": won_amount,
        "conversion_rate": round(len(won_quotes) / quote_count, 4) if quote_count else 0,
        "average_quote_amount": round(quote_amount / quote_count, 2) if quote_count else 0,
        "average_margin": round(sum(margins) / len(margins), 4) if margins else 0,
        "followup_count": followup_count,
        "new_customers": new_customers,
        "by_category": sorted(by_category, key=lambda item: item["amount"], reverse=True),
        "status_breakdown": status_breakdown,
    }


def price_history(db: Session, *, company_id: int, category: str | None = None, limit: int = 50) -> dict[str, Any]:
    """历史成交报价统计（供 AI 建议区间使用，AI 只能给区间）。"""
    stmt = select(Quote).where(Quote.company_id == company_id, Quote.status == "won")
    if category:
        stmt = stmt.join(QuoteItem, QuoteItem.quote_id == Quote.id).where(QuoteItem.category_name == category)
    quotes = list(db.scalars(stmt.order_by(Quote.won_at.desc()).limit(limit)))
    amounts = [float(quote.total_amount or 0) for quote in quotes if quote.total_amount]
    if not amounts:
        return {"samples": [], "sample_size": 0, "average_amount": 0, "min_amount": 0, "max_amount": 0}
    return {
        "samples": [
            {
                "quote_no": quote.quote_no,
                "project_name": quote.project_name,
                "total_amount": float(quote.total_amount or 0),
            }
            for quote in quotes
        ],
        "sample_size": len(amounts),
        "average_amount": round(sum(amounts) / len(amounts), 2),
        "min_amount": min(amounts),
        "max_amount": max(amounts),
    }


def _decimal_sum(values: list[Decimal]) -> Decimal:
    return sum(values, Decimal("0"))
