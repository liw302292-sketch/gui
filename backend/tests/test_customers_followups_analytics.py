"""验收 14：客户与跟进；数据统计。"""

from __future__ import annotations

from datetime import datetime, timedelta


def test_customer_crud_and_detail(company_a):  # noqa: ANN001
    created = company_a.post(
        "/api/customers",
        json={
            "name": "跟进测试客户",
            "contact_name": "李经理",
            "phone": "13800009999",
            "source": "微信",
            "next_followup_at": (datetime.now() + timedelta(days=1)).isoformat(),
        },
    )
    assert created.status_code == 200, created.text
    customer_id = created.json()["data"]["id"]

    updated = company_a.put(f"/api/customers/{customer_id}", json={"status": "high_intent", "remark": "很有意向"})
    assert updated.status_code == 200
    assert updated.json()["data"]["status"] == "high_intent"

    detail = company_a.get(f"/api/customers/{customer_id}").json()["data"]
    assert detail["customer"]["name"] == "跟进测试客户"
    assert {"quotes", "followups", "activities"} <= set(detail)

    statuses = company_a.get("/api/customers/statuses").json()["data"]
    assert any(item["value"] == "won" for item in statuses)

    duplicate = company_a.post("/api/customers", json={"name": "跟进测试客户"})
    assert duplicate.status_code == 409


def test_followup_flow(company_a):  # noqa: ANN001
    customer_id = company_a.post("/api/customers", json={"name": "待跟进客户"}).json()["data"]["id"]

    followup = company_a.post(
        "/api/followups",
        json={
            "customer_id": customer_id,
            "content": "已电话联系，客户要求重新出报价",
            "status": "communicating",
            "next_followup_at": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
    )
    assert followup.status_code == 200, followup.text
    followup_id = followup.json()["data"]["id"]

    today = company_a.get("/api/followups/today").json()["data"]
    assert today["count"] >= 1
    assert "需要跟进" in today["hint"]

    listed = company_a.get("/api/followups", params={"scope": "today"}).json()["data"]["items"]
    assert any(item["id"] == followup_id for item in listed)

    done = company_a.put(f"/api/followups/{followup_id}", json={"done": True, "content": "客户已确认下单"})
    assert done.status_code == 200
    assert done.json()["data"]["done"] is True


def test_dashboard_and_analytics(company_a):  # noqa: ANN001
    dashboard = company_a.get("/api/company/dashboard").json()["data"]
    assert dashboard["greeting"]
    assert {
        "today_quotes",
        "pending_followups",
        "month_quote_amount",
        "month_deal_amount",
        "conversion_rate",
    } <= set(dashboard["stats"])
    assert len(dashboard["quote_trend"]) == 14
    assert len(dashboard["deal_trend"]) == 14
    assert [stage["stage"] for stage in dashboard["funnel"]] == ["报价", "查看", "跟进", "成交"]
    assert "high_value_quotes" in dashboard
    assert dashboard["ai_usage"]["quota"] >= 0

    for period in ("day", "week", "month"):
        data = company_a.get("/api/company/analytics", params={"period": period}).json()["data"]
        assert data["period"] == period
        assert "average_margin" in data
        assert "by_category" in data


def test_company_settings_update(company_a):  # noqa: ANN001
    updated = company_a.put(
        "/api/company",
        json={
            "name": "A广告制作（已改）",
            "rounding_mode": "100",
            "default_profit_margin": 0.32,
            "default_quote_valid_days": 20,
            "default_footer": "专业广告制作",
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["data"]["rounding_mode"] == "100"

    detail = company_a.get("/api/company").json()["data"]
    assert detail["name"] == "A广告制作（已改）"
    assert detail["default_quote_valid_days"] == 20


def test_global_search(company_a):  # noqa: ANN001
    company_a.post("/api/customers", json={"name": "搜索目标客户"})
    result = company_a.get("/api/company/search", params={"q": "搜索目标"}).json()["data"]
    assert any(item["name"] == "搜索目标客户" for item in result["customers"])


def test_quote_template_management(company_a):  # noqa: ANN001
    templates = company_a.get("/api/quote-templates").json()["data"]
    assert templates
    assert templates[0]["is_default"] is True

    created = company_a.post(
        "/api/quote-templates",
        json={"name": "高级报价模板", "accent_color": "#12A150", "is_default": True},
    )
    assert created.status_code == 200, created.text
    new_id = created.json()["data"]["id"]

    templates = company_a.get("/api/quote-templates").json()["data"]
    assert sum(1 for item in templates if item["is_default"]) == 1
    assert next(item for item in templates if item["id"] == new_id)["is_default"] is True

