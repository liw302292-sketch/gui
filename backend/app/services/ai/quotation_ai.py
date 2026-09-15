"""AI 编排层：所有 AI 能力统一从这里暴露给业务代码。

职责边界：
  AI 负责  —— 理解自然语言、识别截图、提取尺寸/数量/产品/材质/工艺、
              发现缺失字段、生成补问、生成客户回复、给出建议区间。
  AI 不负责 —— 最终价格、成本、利润率、任何企业级计费逻辑。
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AIUnavailableError
from app.models.base import utcnow
from app.services.ai import mock_provider
from app.services.ai.deepseek_client import AIResponse, DeepSeekClient
from app.services.ai.prompt_manager import prompt_manager
from app.services.ai.usage_tracker import create_task, estimate_tokens, usage_tracker

logger = logging.getLogger("quote_engine.ai")


class QuotationAI:
    """AI 服务：负责理解与提取，绝不负责定价。"""

    def __init__(self, client: DeepSeekClient | None = None) -> None:
        self.client = client or DeepSeekClient()

    @property
    def mode(self) -> str:
        return "real" if (settings.ai_mode == "real" and self.client.available) else "mock"

    def model_for(self, task_type: str, *, has_image: bool = False, complex_task: bool = False) -> str:
        if has_image:
            return settings.deepseek_vision_model
        if complex_task or task_type in ("price_explain", "price_suggestion"):
            return settings.deepseek_reasoning_model
        return settings.deepseek_text_model

    def _category_hint(self, db: Session, company_id: int) -> str:
        from app.models.product import ProductCategory  # noqa: PLC0415

        categories = db.query(ProductCategory).filter(ProductCategory.company_id == company_id).all()
        return "、".join(category.name for category in categories if category.name)

    def _finish_task(
        self,
        db: Session,
        task,
        response: AIResponse | None,
        *,
        output: dict[str, Any],
        status: str = "success",
        error: str | None = None,
    ) -> None:
        task.status = status
        task.output_payload = output
        task.finished_at = utcnow()
        task.error_message = error
        if response is not None:
            task.raw_response = (response.content or "")[:20000]
            task.input_tokens = response.input_tokens
            task.output_tokens = response.output_tokens
            task.latency_ms = response.latency_ms
            task.retry_count = response.retries
            task.model = response.model
            task.confidence = output.get("confidence")
            usage = usage_tracker.record(
                db,
                company_id=task.company_id,
                user_id=task.user_id,
                task_type=task.task_type,
                model=response.model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                status=status,
                task_id=task.id,
            )
            task.estimated_cost = usage.estimated_cost

    def _run(
        self,
        db: Session,
        *,
        company_id: int,
        user_id: int | None,
        task_type: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        images: list[tuple[bytes, str]] | None = None,
        payload_hint: dict[str, Any] | None = None,
        mock_factory: Callable[[], dict[str, Any]] | None = None,
        file_id: int | None = None,
    ) -> dict[str, Any]:
        task = create_task(
            db,
            company_id=company_id,
            user_id=user_id,
            task_type=task_type,
            model=model,
            mode=self.mode,
            input_payload=payload_hint or {},
            file_id=file_id,
        )

        if self.mode == "mock":
            started = time.perf_counter()
            output = dict(mock_factory() if mock_factory else {})
            output["mode"] = "mock"
            output["model"] = f"{model} (mock)"
            task.status = "success"
            task.output_payload = output
            task.finished_at = utcnow()
            task.latency_ms = int((time.perf_counter() - started) * 1000)
            task.raw_response = "(mock mode: 未调用真实 DeepSeek API)"
            task.confidence = output.get("confidence")
            # Mock 模式同样记录用量与额度：保证没有 API Key 也能演示统计与套餐限制，
            # 同时让企业提前看到真实模式下大致的 token 消耗。
            task.input_tokens = estimate_tokens(system_prompt) + estimate_tokens(user_prompt) + 900 * len(images or [])
            task.output_tokens = estimate_tokens(json.dumps(output, ensure_ascii=False))
            usage = usage_tracker.record(
                db,
                company_id=company_id,
                user_id=user_id,
                task_type=task_type,
                model=model,
                input_tokens=task.input_tokens,
                output_tokens=task.output_tokens,
                status="success",
                task_id=task.id,
            )
            task.estimated_cost = usage.estimated_cost
            db.flush()
            return output

        try:
            response = self.client.chat_json(
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                images=images,
            )
        except AIUnavailableError as exc:
            self._finish_task(db, task, None, output={}, status="failed", error=str(exc))
            db.flush()
            raise

        if response.parsed is None:
            message = response.parse_error or "AI 返回内容无法解析"
            self._finish_task(db, task, response, output={}, status="failed", error=message)
            db.flush()
            raise AIUnavailableError("AI 识别结果解析失败，已保留原始响应，请人工确认或重试。")

        output = dict(response.parsed)
        output.setdefault("confidence", 0.0)
        output["mode"] = "real"
        output["model"] = response.model
        self._finish_task(db, task, response, output=output)
        db.flush()
        return output

    # ------------------------------------------------------------------
    # 1. 需求识别
    # ------------------------------------------------------------------
    def extract_requirement(
        self,
        db: Session,
        *,
        company_id: int,
        user_id: int | None,
        requirement_text: str = "",
        images: list[tuple[bytes, str]] | None = None,
        file_id: int | None = None,
        task_id_holder: dict[str, int] | None = None,
    ) -> dict[str, Any]:
        category_hint = self._category_hint(db, company_id)
        model = self.model_for("requirement_extract", has_image=bool(images))
        has_image = bool(images)

        user_prompt = prompt_manager.get(
            "quote_extract",
            requirement_text=requirement_text
            or ("（客户未提供文字说明，请从图片中提取全部可见需求信息）" if has_image else "（客户未提供任何需求描述）"),
            category_hint=category_hint,
        )

        result = self._run(
            db,
            company_id=company_id,
            user_id=user_id,
            task_type="requirement_extract",
            model=model,
            system_prompt="你是广告制作行业的报价需求识别引擎，只输出 JSON，绝不输出价格。",
            user_prompt=user_prompt,
            images=images,
            payload_hint={"text_length": len(requirement_text), "image_count": len(images or [])},
            mock_factory=lambda: mock_provider.mock_requirement(requirement_text, has_image=has_image),
            file_id=file_id,
        )
        return self._normalize_requirement(result)

    @staticmethod
    def _normalize_requirement(raw: dict[str, Any]) -> dict[str, Any]:
        """容错归一化：AI 输出缺字段也不能让流程崩溃。"""
        normalized: dict[str, Any] = {
            "project_name": raw.get("project_name"),
            "customer_name": raw.get("customer_name"),
            "items": [],
            "transport_required": raw.get("transport_required"),
            "installation_required": raw.get("installation_required"),
            "installation_location": raw.get("installation_location"),
            "deadline": raw.get("deadline"),
            "missing_fields": list(raw.get("missing_fields") or []),
            "unknown_fields": list(raw.get("unknown_fields") or []),
            "inference": raw.get("inference") or {},
            "confidence": float(raw.get("confidence") or 0.0),
            "mode": raw.get("mode", "mock"),
            "model": raw.get("model", ""),
        }
        for item in raw.get("items") or []:
            if not isinstance(item, dict):
                continue
            quantity = _to_float_or_none(item.get("quantity"))
            normalized["items"].append(
                {
                    "category": item.get("category"),
                    "product_name": item.get("product_name") or item.get("category") or "未命名产品",
                    "width": _to_float_or_none(item.get("width")),
                    "height": _to_float_or_none(item.get("height")),
                    "depth": _to_float_or_none(item.get("depth")),
                    "quantity": quantity if quantity and quantity > 0 else 1.0,
                    "unit": item.get("unit") or "平方米",
                    "material": item.get("material"),
                    "process": list(item.get("process") or []),
                    "installation": item.get("installation"),
                    "remark": item.get("remark"),
                    "source": item.get("source"),
                }
            )
        return normalized

    # ------------------------------------------------------------------
    # 2. 缺失信息补问
    # ------------------------------------------------------------------
    def missing_fields(
        self,
        db: Session,
        *,
        company_id: int,
        user_id: int | None,
        requirement: dict[str, Any],
    ) -> dict[str, Any]:
        return self._run(
            db,
            company_id=company_id,
            user_id=user_id,
            task_type="missing_fields",
            model=self.model_for("missing_fields"),
            system_prompt="你是广告制作行业的报价顾问，只输出 JSON。",
            user_prompt=prompt_manager.get("quote_missing_fields", requirement_json=requirement),
            payload_hint={"missing_fields": requirement.get("missing_fields")},
            mock_factory=lambda: mock_provider.mock_missing_fields(requirement),
        )

    # ------------------------------------------------------------------
    # 3. 客户回复文案
    # ------------------------------------------------------------------
    def draft_reply(
        self,
        db: Session,
        *,
        company_id: int,
        user_id: int | None,
        requirement: dict[str, Any],
        quote: dict[str, Any],
        style: str = "professional",
    ) -> dict[str, Any]:
        style = style if style in ("professional", "concise", "closing") else "professional"
        return self._run(
            db,
            company_id=company_id,
            user_id=user_id,
            task_type="reply_draft",
            model=self.model_for("reply_draft"),
            system_prompt="你是广告制作公司的资深销售，只输出 JSON，金额必须与给定报价一致。",
            user_prompt=prompt_manager.get(
                "quote_reply", requirement_json=requirement, quote_json=quote, style=style
            ),
            payload_hint={"style": style},
            mock_factory=lambda: mock_provider.mock_reply(requirement, quote, style),
        )

    # ------------------------------------------------------------------
    # 4. 报价解释
    # ------------------------------------------------------------------
    def explain_price(
        self,
        db: Session,
        *,
        company_id: int,
        user_id: int | None,
        question: str,
        quote: dict[str, Any],
    ) -> dict[str, Any]:
        return self._run(
            db,
            company_id=company_id,
            user_id=user_id,
            task_type="price_explain",
            model=self.model_for("price_explain", complex_task=True),
            system_prompt="你是广告制作公司的商务，只输出 JSON，不暴露成本与利润。",
            user_prompt=prompt_manager.get("quote_explain", question=question, quote_json=quote),
            payload_hint={"question": question[:200]},
            mock_factory=lambda: mock_provider.mock_explain(question, quote),
        )

    # ------------------------------------------------------------------
    # 5. 报价区间建议（只能给区间，绝不覆盖真实价格）
    # ------------------------------------------------------------------
    def suggest_price(
        self,
        db: Session,
        *,
        company_id: int,
        user_id: int | None,
        requirement: dict[str, Any],
        history: dict[str, Any],
    ) -> dict[str, Any]:
        return self._run(
            db,
            company_id=company_id,
            user_id=user_id,
            task_type="price_suggestion",
            model=self.model_for("price_suggestion", complex_task=True),
            system_prompt="你只能给出建议区间，不能给出最终价格。只输出 JSON。",
            user_prompt=prompt_manager.get(
                "quote_suggestion", requirement_json=requirement, history_json=history
            ),
            payload_hint={"sample_size": history.get("sample_size", 0)},
            mock_factory=lambda: mock_provider.mock_suggestion(requirement, history),
        )

    # ------------------------------------------------------------------
    def test_connection(self) -> dict[str, Any]:
        if self.mode == "mock":
            return {
                "mode": "mock",
                "ok": True,
                "message": "当前为 Mock 模式：未配置 DEEPSEEK_API_KEY，AI 使用确定性演示数据。",
            }
        started = time.perf_counter()
        try:
            response = self.client.chat_text(
                model=settings.deepseek_text_model,
                system_prompt="你是一个严谨的助手。",
                user_prompt="回复两个字：正常",
            )
        except AIUnavailableError as exc:
            return {"mode": "real", "ok": False, "message": str(exc)}
        return {
            "mode": "real",
            "ok": True,
            "message": "DeepSeek 连接正常",
            "model": response.model,
            "latency_ms": int((time.perf_counter() - started) * 1000),
        }


def _to_float_or_none(value: Any) -> float | None:
    if value in (None, "", "null", "None"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


quotation_ai = QuotationAI()
