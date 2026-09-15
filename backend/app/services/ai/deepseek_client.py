"""DeepSeek API 客户端（OpenAI-compatible）。

- Base URL / 模型名全部来自配置，换模型不需要改业务代码。
- 只暴露 chat_json / chat_text，业务层不关心 HTTP 细节。
- 内置超时、重试、JSON 解析失败自动重试、用量提取。
"""

from __future__ import annotations

import base64
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.core.config import settings
from app.core.errors import AIUnavailableError

logger = logging.getLogger("quote_engine.ai")


@dataclass
class AIResponse:
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    raw: dict[str, Any] = field(default_factory=dict)
    retries: int = 0
    parsed: dict[str, Any] | None = None
    parse_error: str | None = None
    mode: str = "real"


class DeepSeekClient:
    """轻量封装：只依赖 httpx，避免额外 SDK 风险。"""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.api_key = (api_key if api_key is not None else settings.deepseek_api_key).strip()
        self.base_url = (base_url or settings.deepseek_base_url).rstrip("/")
        self.timeout = timeout or settings.ai_request_timeout_seconds

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.available:
            raise AIUnavailableError("未配置 DEEPSEEK_API_KEY，AI 处于 Mock 模式")
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise AIUnavailableError("AI 响应超时，请稍后重试。") from exc
        except httpx.HTTPError as exc:
            logger.warning("DeepSeek 网络错误: %s", exc)
            raise AIUnavailableError("AI 暂时繁忙，请稍后重试。") from exc

        if response.status_code == 429:
            raise AIUnavailableError("AI 调用过于频繁，请稍后重试。")
        if response.status_code >= 500:
            logger.warning("DeepSeek 服务端错误 %s: %s", response.status_code, response.text[:500])
            raise AIUnavailableError("AI 暂时繁忙，请稍后重试。")
        if response.status_code >= 400:
            logger.warning("DeepSeek 请求失败 %s: %s", response.status_code, response.text[:500])
            raise AIUnavailableError("AI 请求未被接受，请检查 API Key 与模型配置。")

        try:
            return response.json()
        except ValueError as exc:
            raise AIUnavailableError("AI 返回内容无法解析，请稍后重试。") from exc

    @staticmethod
    def _extract_usage(data: dict[str, Any]) -> tuple[int, int]:
        usage = data.get("usage") or {}
        prompt_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
        return prompt_tokens, completion_tokens

    @staticmethod
    def _extract_content(data: dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if choices:
            message = choices[0].get("message") or {}
            content = message.get("content")
            if isinstance(content, list):
                return "".join(part.get("text", "") for part in content if isinstance(part, dict))
            if content:
                return str(content)
        output = data.get("output_text") or data.get("output")
        if isinstance(output, str):
            return output
        return ""

    def chat_json(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        images: list[tuple[bytes, str]] | None = None,
        temperature: float = 0.1,
        max_retries: int | None = None,
    ) -> AIResponse:
        """JSON Output 调用；解析失败自动重试（次数可配置）。"""
        retries_allowed = settings.ai_max_retries if max_retries is None else max_retries
        attempt = 0
        last_error = ""
        total_latency = 0
        input_tokens = output_tokens = 0
        raw_response: dict[str, Any] = {}
        content = ""

        while attempt <= retries_allowed:
            started = time.perf_counter()
            raw_response = self._chat_completion(
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                images=images,
                temperature=temperature,
                force_json=True,
                retry_hint=last_error if attempt else None,
            )
            total_latency += int((time.perf_counter() - started) * 1000)
            prompt_tokens, completion_tokens = self._extract_usage(raw_response)
            input_tokens += prompt_tokens
            output_tokens += completion_tokens
            content = self._extract_content(raw_response)

            parsed, error = self.parse_json(content)
            if parsed is not None:
                return AIResponse(
                    content=content,
                    model=raw_response.get("model", model),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=total_latency,
                    raw=raw_response,
                    retries=attempt,
                    parsed=parsed,
                )

            last_error = error or "JSON 解析失败"
            logger.warning("AI JSON 解析失败（第 %s 次）：%s", attempt + 1, last_error)
            attempt += 1

        logger.error("AI JSON 解析连续失败，保留原始响应以便人工修正")
        return AIResponse(
            content=content,
            model=raw_response.get("model", model),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=total_latency,
            raw=raw_response,
            retries=retries_allowed,
            parsed=None,
            parse_error=last_error,
        )

    def chat_text(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.4,
    ) -> AIResponse:
        started = time.perf_counter()
        raw = self._chat_completion(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            images=None,
            temperature=temperature,
            force_json=False,
        )
        prompt_tokens, completion_tokens = self._extract_usage(raw)
        return AIResponse(
            content=self._extract_content(raw),
            model=raw.get("model", model),
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            latency_ms=int((time.perf_counter() - started) * 1000),
            raw=raw,
        )

    def _chat_completion(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        images: list[tuple[bytes, str]] | None,
        temperature: float,
        force_json: bool,
        retry_hint: str | None = None,
    ) -> dict[str, Any]:
        user_content: str | list[dict[str, Any]]
        if images:
            parts: list[dict[str, Any]] = [{"type": "text", "text": user_prompt}]
            for blob, mime in images:
                encoded = base64.b64encode(blob).decode("ascii")
                parts.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}})
            user_content = parts
        else:
            user_content = user_prompt

        messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": user_content})
        if retry_hint:
            messages.append({"role": "assistant", "content": "（上一次输出不是合法 JSON）"})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"上一次输出无法解析为 JSON，错误：{retry_hint}。"
                        "请重新输出，只输出一个合法的 JSON 对象，不要包含 markdown 代码块或任何解释。"
                    ),
                }
            )

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        if force_json:
            payload["response_format"] = {"type": "json_object"}

        return self._post("/chat/completions", payload)

    @staticmethod
    def parse_json(content: str) -> tuple[dict[str, Any] | None, str | None]:
        """健壮 JSON 解析：兼容 markdown 包裹、前后多余文本。"""
        if not content or not content.strip():
            return None, "AI 返回内容为空"
        text = content.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
            text = text.strip()
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data, None
            return None, "AI 返回的 JSON 不是对象"
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    data = json.loads(text[start : end + 1])
                    if isinstance(data, dict):
                        return data, None
                except json.JSONDecodeError as exc:
                    return None, f"JSON 解析失败：{exc.msg}"
            return None, "未找到合法 JSON 对象"


deepseek_client = DeepSeekClient()

