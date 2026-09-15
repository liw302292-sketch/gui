"""验收 6、17、18：AI mock / JSON 解析 / 缺失信息 / 回复 / 解释 / 区间建议 / 用量记录。"""

from __future__ import annotations

from app.services.ai.deepseek_client import DeepSeekClient
from app.services.ai.quotation_ai import QuotationAI


def test_mock_mode_without_api_key(company_a):  # noqa: ANN001
    status = company_a.get("/api/ai/status").json()["data"]
    assert status["mode"] == "mock"
    assert status["models"]["vision"].startswith("deepseek")

    test = company_a.post("/api/ai/test").json()["data"]
    assert test["ok"] is True
    assert test["mode"] == "mock"


def test_json_parse_handles_markdown_and_noise():
    client = DeepSeekClient(api_key="")
    assert client.parse_json('{"a": 1}')[0] == {"a": 1}
    assert client.parse_json('```json\n{"a": 2}\n```')[0] == {"a": 2}
    assert client.parse_json('好的，结果如下：{"a": 3} 以上。')[0] == {"a": 3}
    parsed, error = client.parse_json("完全不是 JSON")
    assert parsed is None and error


def test_ai_normalize_tolerates_bad_output():
    normalized = QuotationAI._normalize_requirement(
        {
            "items": [
                {"product_name": "门头", "quantity": "abc", "width": "10", "unit": None},
                "不是对象",
            ],
            "missing_fields": None,
        }
    )
    assert len(normalized["items"]) == 1
    assert normalized["items"][0]["quantity"] == 1.0
    assert normalized["items"][0]["width"] == 10.0
    assert normalized["items"][0]["unit"] == "平方米"
    assert normalized["missing_fields"] == []


def test_missing_fields_questions(company_a, requirement):  # noqa: ANN001
    missing = company_a.post("/api/ai/missing-fields", json={"requirement": requirement}).json()["data"]["result"]
    assert missing["questions"]
    assert missing["summary"]
    assert all("question" in item and item["question"] for item in missing["questions"])


def test_reply_styles_keep_amount(company_a, requirement):  # noqa: ANN001
    reply = company_a.post(
        "/api/ai/reply",
        json={"requirement": requirement, "quote": {"total_amount": 25600}, "style": "professional"},
    ).json()["data"]["result"]
    assert reply["content"]
    assert "25,600" in reply["content"] or "25600" in reply["content"]

    for style in ("concise", "closing"):
        response = company_a.post(
            "/api/ai/reply",
            json={"requirement": requirement, "quote": {"total_amount": 1000}, "style": style},
        )
        assert response.status_code == 200
        assert response.json()["data"]["result"]["style"] == style


def test_explain_price(company_a):  # noqa: ANN001
    explain = company_a.post(
        "/api/ai/explain",
        json={"quote": {"total_amount": 25600, "items": []}, "question": "为什么这么贵？"},
    ).json()["data"]["result"]
    assert explain["reasons"]
    assert explain["customer_reply"]
    assert explain["adjust_options"]


def test_price_suggestion_only_returns_range(company_a, requirement):  # noqa: ANN001
    suggestion = company_a.post(
        "/api/ai/suggest-price",
        json={"requirement": requirement, "category": "门头"},
    ).json()["data"]["result"]
    assert "range_low" in suggestion and "range_high" in suggestion
    assert "sample_size" in suggestion
    assert "caution" in suggestion
    assert "final_price" not in suggestion


def test_ai_usage_is_tracked(company_a):  # noqa: ANN001
    usage = company_a.get("/api/ai/usage").json()["data"]
    assert usage["summary"]["calls"] > 0
    assert usage["recent_tasks"]
    task = usage["recent_tasks"][0]
    assert task["task_type"] and task["model"]
    assert "input_tokens" in task
    assert "estimated_cost" in task
    assert task["status"] in ("success", "failed", "pending")


def test_ai_task_raw_response_is_kept(company_a):  # noqa: ANN001
    tasks = company_a.get("/api/ai/usage").json()["data"]["recent_tasks"]
    detail = company_a.get(f"/api/ai/tasks/{tasks[0]['id']}").json()["data"]
    assert detail["status"] in ("success", "failed")
    assert detail["raw_response"] is not None


def test_ai_requires_authentication(client):  # noqa: ANN001
    assert client.post("/api/ai/extract-text", json={"text": "门头"}).status_code == 401

