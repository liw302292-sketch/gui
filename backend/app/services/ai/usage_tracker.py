"""AI 用量与成本统计。

成本只做统计参考：单价来自环境变量（DeepSeek 采用峰谷计价），绝不写死在业务代码。
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai import AITask, AIUsage
from app.models.base import utcnow
from app.models.company import Company

DEFAULT_PRICES: dict[str, tuple[float, float]] = {
    "flash": (0.5, 2.0),
    "pro": (2.0, 8.0),
    "vision": (1.0, 4.0),
}


def model_role(model: str) -> str:
    name = (model or "").lower()
    if "vision" in name:
        return "vision"
    if "pro" in name or "reason" in name:
        return "pro"
    return "flash"


def price_for(model: str) -> tuple[Decimal, Decimal]:
    role = model_role(model)
    configured = {
        "flash": (settings.ai_price_flash_input, settings.ai_price_flash_output),
        "pro": (settings.ai_price_pro_input, settings.ai_price_pro_output),
        "vision": (settings.ai_price_vision_input, settings.ai_price_vision_output),
    }[role]
    if configured == (0.0, 0.0):
        configured = DEFAULT_PRICES[role]
    return Decimal(str(configured[0])), Decimal(str(configured[1]))


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> Decimal:
    price_in, price_out = price_for(model)
    cost = (Decimal(input_tokens) / Decimal(1000000)) * price_in
    cost += (Decimal(output_tokens) / Decimal(1000000)) * price_out
    return cost.quantize(Decimal("0.000001"))


def estimate_tokens(text: str | None) -> int:
    """粗略 token 估算：中文约 1.5 字/token，这里保守按 2 字/token 计。"""
    if not text:
        return 0
    return max(len(text) // 2, 1)


class UsageTracker:
    def record(
        self,
        db: Session,
        *,
        company_id: int,
        user_id: int | None,
        task_type: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        status: str = "success",
        task_id: int | None = None,
    ) -> AIUsage:
        usage = AIUsage(
            company_id=company_id,
            user_id=user_id,
            task_id=task_id,
            task_type=task_type,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=estimate_cost(model, input_tokens, output_tokens),
            status=status,
        )
        db.add(usage)
        return usage

    def monthly_usage(self, db: Session, company_id: int) -> dict[str, Any]:
        now = utcnow()
        start = datetime(now.year, now.month, 1)
        calls = db.scalar(
            select(func.count())
            .select_from(AIUsage)
            .where(AIUsage.company_id == company_id, AIUsage.created_at >= start)
        ) or 0
        tokens_in = db.scalar(
            select(func.coalesce(func.sum(AIUsage.input_tokens), 0)).where(
                AIUsage.company_id == company_id, AIUsage.created_at >= start
            )
        ) or 0
        tokens_out = db.scalar(
            select(func.coalesce(func.sum(AIUsage.output_tokens), 0)).where(
                AIUsage.company_id == company_id, AIUsage.created_at >= start
            )
        ) or 0
        cost = db.scalar(
            select(func.coalesce(func.sum(AIUsage.estimated_cost), 0)).where(
                AIUsage.company_id == company_id, AIUsage.created_at >= start
            )
        ) or Decimal("0")
        company = db.get(Company, company_id)
        quota = company.ai_monthly_quota if company else 0
        return {
            "month": start.strftime("%Y-%m"),
            "calls": int(calls),
            "input_tokens": int(tokens_in),
            "output_tokens": int(tokens_out),
            "estimated_cost": float(cost),
            "quota": quota,
            "remaining": max(quota - int(calls), 0) if quota else -1,
            "usage_ratio": round(int(calls) / quota, 4) if quota else 0,
        }

    def check_quota(self, db: Session, company_id: int) -> tuple[bool, dict[str, Any]]:
        stats = self.monthly_usage(db, company_id)
        quota = int(stats["quota"])
        if quota <= 0:
            return True, stats
        return int(stats["calls"]) < quota, stats

    def platform_stats(self, db: Session, days: int = 30) -> dict[str, Any]:
        since = datetime.combine(date.today() - timedelta(days=days), datetime.min.time())
        today = datetime.combine(date.today(), datetime.min.time())
        total = db.scalar(select(func.count()).select_from(AIUsage)) or 0
        today_calls = db.scalar(select(func.count()).select_from(AIUsage).where(AIUsage.created_at >= today)) or 0
        cost_total = db.scalar(select(func.coalesce(func.sum(AIUsage.estimated_cost), 0))) or Decimal("0")
        cost_today = db.scalar(
            select(func.coalesce(func.sum(AIUsage.estimated_cost), 0)).where(AIUsage.created_at >= today)
        ) or Decimal("0")
        by_model = [
            {"model": model, "calls": int(calls), "cost": float(cost or 0)}
            for model, calls, cost in db.execute(
                select(
                    AIUsage.model,
                    func.count(AIUsage.id),
                    func.coalesce(func.sum(AIUsage.estimated_cost), 0),
                )
                .where(AIUsage.created_at >= since)
                .group_by(AIUsage.model)
                .order_by(func.count(AIUsage.id).desc())
            )
        ]
        by_company = [
            {"company_id": cid, "company_name": name, "calls": int(calls), "cost": float(cost or 0)}
            for cid, name, calls, cost in db.execute(
                select(
                    AIUsage.company_id,
                    Company.name,
                    func.count(AIUsage.id),
                    func.coalesce(func.sum(AIUsage.estimated_cost), 0),
                )
                .join(Company, Company.id == AIUsage.company_id)
                .where(AIUsage.created_at >= since)
                .group_by(AIUsage.company_id, Company.name)
                .order_by(func.count(AIUsage.id).desc())
                .limit(20)
            )
        ]
        by_task = [
            {"task_type": task_type, "calls": int(calls)}
            for task_type, calls in db.execute(
                select(AIUsage.task_type, func.count(AIUsage.id))
                .where(AIUsage.created_at >= since)
                .group_by(AIUsage.task_type)
                .order_by(func.count(AIUsage.id).desc())
            )
        ]
        return {
            "total_calls": int(total),
            "today_calls": int(today_calls),
            "total_cost": float(cost_total),
            "today_cost": float(cost_today),
            "by_model": by_model,
            "by_company": by_company,
            "by_task": by_task,
            "window_days": days,
        }


usage_tracker = UsageTracker()


def create_task(
    db: Session,
    *,
    company_id: int,
    user_id: int | None,
    task_type: str,
    model: str,
    mode: str,
    input_payload: dict[str, Any] | None = None,
    file_id: int | None = None,
) -> AITask:
    task = AITask(
        company_id=company_id,
        user_id=user_id,
        task_type=task_type,
        model=model,
        mode=mode,
        status="pending",
        input_payload=input_payload or {},
        file_id=file_id,
    )
    db.add(task)
    db.flush()
    return task
