"""AI 接口：需求识别、缺失信息、客户回复、报价解释、区间建议、用量、连接测试。"""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, Form, Request, UploadFile
from sqlalchemy import select

from app.core.config import settings
from app.core.deps import Context, DbSession, check_ai_quota
from app.core.errors import AIUnavailableError, ConflictError, NotFoundError
from app.core.rate_limit import enforce_ai_rate_limit
from app.models.ai import AITask
from app.schemas.ai import (
    ExplainRequest,
    ExtractTextRequest,
    MissingFieldsRequest,
    ReplyRequest,
    SuggestRequest,
)
from app.services import analytics_service, file_service
from app.services.ai.quotation_ai import quotation_ai
from app.services.ai.usage_tracker import usage_tracker
from app.services.ai.vision_parser import SUPPORTED_IMAGE_MIME, detect_mime

logger = logging.getLogger("quote_engine.ai")

router = APIRouter()


def _usage_context(db: DbSession, context: Context) -> dict:
    return usage_tracker.monthly_usage(db, context.company_id)


@router.get("/status", response_model=dict, summary="AI 状态与用量")
def ai_status(context: Context, db: DbSession) -> dict:
    usage = _usage_context(db, context)
    return {
        "ok": True,
        "data": {
            "mode": quotation_ai.mode,
            "models": {
                "text": settings.deepseek_text_model,
                "reasoning": settings.deepseek_reasoning_model,
                "vision": settings.deepseek_vision_model,
            },
            "base_url": settings.deepseek_base_url,
            "usage": usage,
        },
    }


@router.post("/test", response_model=dict, summary="测试 DeepSeek 连接")
def test_connection(context: Context) -> dict:
    return {"ok": True, "data": quotation_ai.test_connection()}


@router.post("/extract", response_model=dict, summary="需求识别（截图 / 图片 / PDF / Excel / 文字）")
async def extract(
    context: Context,
    db: DbSession,
    request: Request,
    text: str = Form(default=""),
    file: UploadFile | None = File(default=None),
) -> dict:
    enforce_ai_rate_limit(request)
    check_ai_quota(db, context)

    images: list[tuple[bytes, str]] = []
    file_id = None
    requirement_text = text or ""

    if file is not None and file.filename:
        data = await file.read()
        record = file_service.save_upload(
            db,
            company_id=context.company_id,
            user_id=context.user_id,
            filename=file.filename,
            content_type=file.content_type,
            data=data,
        )
        file_id = record.id

        if record.kind == "image":
            images.append((data, detect_mime(file.filename, file.content_type)))
        elif record.kind == "pdf":
            try:
                extracted = file_service.extract_pdf_text(data)
                if extracted:
                    requirement_text = f"{requirement_text}\n{extracted}".strip()
            except Exception:  # noqa: BLE001
                logger.warning("PDF 文本提取失败，改为直接送入 Vision 模型")
        elif record.kind == "sheet":
            try:
                rows = file_service.extract_spreadsheet(data)
                preview = rows[:50]
                requirement_text = f"{requirement_text}\n表格内容：{preview}".strip()
            except Exception as exc:  # noqa: BLE001
                raise ConflictError("无法读取该表格文件，请确认为 .xlsx 或 .csv") from exc
        elif record.kind == "text":
            requirement_text = f"{requirement_text}\n{data.decode('utf-8', errors='ignore')}".strip()

    if not images and not requirement_text.strip():
        raise ConflictError("请上传图片/截图/PDF，或粘贴客户需求文字")

    result = quotation_ai.extract_requirement(
        db,
        company_id=context.company_id,
        user_id=context.user_id,
        requirement_text=requirement_text,
        images=images or None,
        file_id=file_id,
    )
    missing = quotation_ai.missing_fields(
        db, company_id=context.company_id, user_id=context.user_id, requirement=result
    )
    result["missing_questions"] = missing.get("questions", [])
    result["missing_summary"] = missing.get("summary", "")
    return {
        "ok": True,
        "data": {
            "mode": result.get("mode", "mock"),
            "model": result.get("model", ""),
            "file_id": file_id,
            "requirement": result,
            "usage": _usage_context(db, context),
        },
    }


@router.post("/extract-text", response_model=dict, summary="纯文字需求识别")
def extract_text(payload: ExtractTextRequest, context: Context, db: DbSession, request: Request) -> dict:
    enforce_ai_rate_limit(request)
    check_ai_quota(db, context)
    result = quotation_ai.extract_requirement(
        db,
        company_id=context.company_id,
        user_id=context.user_id,
        requirement_text=payload.text,
        images=None,
        file_id=payload.file_id,
    )
    missing = quotation_ai.missing_fields(
        db, company_id=context.company_id, user_id=context.user_id, requirement=result
    )
    result["missing_questions"] = missing.get("questions", [])
    result["missing_summary"] = missing.get("summary", "")
    return {"ok": True, "data": {"requirement": result, "usage": _usage_context(db, context)}}


@router.post("/missing-fields", response_model=dict, summary="生成补问清单")
def missing_fields(payload: MissingFieldsRequest, context: Context, db: DbSession, request: Request) -> dict:
    enforce_ai_rate_limit(request)
    check_ai_quota(db, context)
    result = quotation_ai.missing_fields(
        db, company_id=context.company_id, user_id=context.user_id, requirement=payload.requirement
    )
    return {"ok": True, "data": {"result": result, "usage": _usage_context(db, context)}}


@router.post("/reply", response_model=dict, summary="生成客户回复文案（专业版/简洁版/成交版）")
def reply(payload: ReplyRequest, context: Context, db: DbSession, request: Request) -> dict:
    enforce_ai_rate_limit(request)
    check_ai_quota(db, context)
    result = quotation_ai.draft_reply(
        db,
        company_id=context.company_id,
        user_id=context.user_id,
        requirement=payload.requirement,
        quote=payload.quote,
        style=payload.style,
    )
    return {"ok": True, "data": {"result": result, "usage": _usage_context(db, context)}}


@router.post("/explain", response_model=dict, summary="报价解释（客户问为什么贵）")
def explain(payload: ExplainRequest, context: Context, db: DbSession, request: Request) -> dict:
    enforce_ai_rate_limit(request)
    check_ai_quota(db, context)
    result = quotation_ai.explain_price(
        db,
        company_id=context.company_id,
        user_id=context.user_id,
        question=payload.question,
        quote=payload.quote,
    )
    return {"ok": True, "data": {"result": result, "usage": _usage_context(db, context)}}


@router.post("/suggest-price", response_model=dict, summary="历史报价区间建议（只给区间）")
def suggest_price(payload: SuggestRequest, context: Context, db: DbSession, request: Request) -> dict:
    enforce_ai_rate_limit(request)
    check_ai_quota(db, context)
    history = analytics_service.price_history(db, company_id=context.company_id, category=payload.category)
    result = quotation_ai.suggest_price(
        db,
        company_id=context.company_id,
        user_id=context.user_id,
        requirement=payload.requirement,
        history=history,
    )
    result["history"] = {
        "sample_size": history.get("sample_size"),
        "average_amount": history.get("average_amount"),
        "min_amount": history.get("min_amount"),
        "max_amount": history.get("max_amount"),
    }
    return {"ok": True, "data": {"result": result, "usage": _usage_context(db, context)}}


@router.get("/usage", response_model=dict, summary="AI 用量统计")
def usage(context: Context, db: DbSession) -> dict:
    tasks = list(
        db.scalars(
            select(AITask)
            .where(AITask.company_id == context.company_id)
            .order_by(AITask.created_at.desc())
            .limit(30)
        )
    )
    return {
        "ok": True,
        "data": {
            "summary": usage_tracker.monthly_usage(db, context.company_id),
            "recent_tasks": [
                {
                    "id": task.id,
                    "task_type": task.task_type,
                    "status": task.status,
                    "model": task.model,
                    "mode": task.mode,
                    "input_tokens": task.input_tokens,
                    "output_tokens": task.output_tokens,
                    "estimated_cost": float(task.estimated_cost or 0),
                    "latency_ms": task.latency_ms,
                    "confidence": float(task.confidence) if task.confidence is not None else None,
                    "error": task.error_message,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                }
                for task in tasks
            ],
        },
    }


@router.get("/tasks/{task_id}", response_model=dict, summary="查看 AI 任务原始响应")
def task_detail(task_id: int, context: Context, db: DbSession) -> dict:
    task = db.get(AITask, task_id)
    if not task or task.company_id != context.company_id:
        raise NotFoundError("AI 任务不存在")
    return {
        "ok": True,
        "data": {
            "id": task.id,
            "task_type": task.task_type,
            "status": task.status,
            "model": task.model,
            "raw_response": task.raw_response,
            "output": task.output_payload,
            "error": task.error_message,
            "retry_count": task.retry_count,
        },
    }
