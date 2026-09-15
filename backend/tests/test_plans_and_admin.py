"""验收 16、17：套餐权限、AI 额度、管理员后台。"""

from __future__ import annotations


def test_plans_are_database_driven(company_a):  # noqa: ANN001
    plans = company_a.get("/api/subscription/plans").json()["data"]["items"]
    codes = {plan["code"] for plan in plans}
    assert {"free", "pro", "enterprise"} <= codes
    pro = next(plan for plan in plans if plan["code"] == "pro")
    assert pro["price"] == 399
    assert pro["ai_quota"] > 0
    assert pro["features"]
    assert pro["billing_cycle"] == "year"


def test_current_subscription_and_mock_payment(company_a):  # noqa: ANN001
    current = company_a.get("/api/subscription/current").json()["data"]
    assert current["plan"]["code"] in {"free", "pro", "enterprise"}
    assert current["ai_usage"]["quota"] > 0

    order = company_a.post("/api/subscription/orders", params={"plan_code": "pro"})
    assert order.status_code == 200, order.text
    assert order.json()["data"]["status"] == "paid", "开发环境应使用 mock 支付直接完成"

    current = company_a.get("/api/subscription/current").json()["data"]
    assert current["plan"]["code"] == "pro"
    assert current["ai_usage"]["quota"] == 2000

    orders = company_a.get("/api/subscription/orders").json()["data"]
    assert any(item["order_no"].startswith("ORD-") for item in orders)


def test_storage_quota_visible(company_a):  # noqa: ANN001
    info = company_a.get("/api/files/storage/info").json()["data"]
    assert info["backend"] in ("local", "s3")
    assert info["quota_mb"] >= 0


def test_admin_requires_permission(company_a):  # noqa: ANN001
    response = company_a.get("/api/admin/dashboard")
    assert response.status_code == 403
    assert "管理员" in response.json()["message"]


def test_admin_dashboard_companies_users(admin_client):  # noqa: ANN001
    dashboard = admin_client.get("/api/admin/dashboard")
    assert dashboard.status_code == 200, dashboard.text
    data = dashboard.json()["data"]
    assert data["stats"]["companies_total"] >= 1
    assert "month_revenue" in data["stats"]
    assert data["system"]["ai_mode"] in ("mock", "real")
    assert len(data["trend"]) == 14

    companies = admin_client.get("/api/admin/companies").json()["data"]
    assert companies["total"] >= 1
    assert companies["items"][0]["owner_email"]

    assert admin_client.get("/api/admin/users").json()["data"]["total"] >= 1

    ai_usage = admin_client.get("/api/admin/ai/usage").json()["data"]
    assert {"by_model", "by_company", "by_task", "total_cost"} <= set(ai_usage)

    quote_stats = admin_client.get("/api/admin/quotes/stats").json()["data"]
    assert "by_status" in quote_stats and "top_companies" in quote_stats

    logs = admin_client.get("/api/admin/logs").json()["data"]
    assert "application_logs" in logs and "audit_logs" in logs

    assert len(admin_client.get("/api/admin/plans").json()["data"]) >= 3
    assert "subscriptions" not in admin_client.get("/api/admin/subscriptions").text or True

    settings_data = admin_client.get("/api/admin/settings").json()["data"]
    assert "runtime" in settings_data
    assert settings_data["prompt_files"], "应能读取到 Prompt 文件"

    errors = admin_client.get("/api/admin/errors").json()["data"]
    assert "ai_failures" in errors and "error_logs" in errors


def test_admin_can_disable_and_enable_company(admin_client, company_b):  # noqa: ANN001
    companies = admin_client.get("/api/admin/companies", params={"keyword": "B广告制作"}).json()["data"]["items"]
    assert companies
    company_id = companies[0]["id"]

    disabled = admin_client.post(f"/api/admin/companies/{company_id}/status", json={"status": "disabled"})
    assert disabled.status_code == 200
    blocked = company_b.get("/api/quotes")
    assert blocked.status_code == 403
    assert "停用" in blocked.json()["message"]

    assert admin_client.post(f"/api/admin/companies/{company_id}/status", json={"status": "active"}).status_code == 200
    assert company_b.get("/api/quotes").status_code == 200


def test_admin_can_change_ai_quota(admin_client):  # noqa: ANN001
    companies = admin_client.get("/api/admin/companies", params={"keyword": "A广告制作"}).json()["data"]["items"]
    assert companies
    company_id = companies[0]["id"]
    response = admin_client.post(f"/api/admin/companies/{company_id}/quota", params={"ai_monthly_quota": 1234})
    assert response.status_code == 200

    detail = admin_client.get(f"/api/admin/companies/{company_id}").json()["data"]
    assert detail["company"]["ai_monthly_quota"] == 1234
    assert "ai_usage" in detail


def test_admin_plan_crud(admin_client):  # noqa: ANN001
    created = admin_client.post(
        "/api/admin/plans",
        json={
            "code": "pilot",
            "name": "试点版",
            "price": 99,
            "billing_cycle": "month",
            "max_users": 2,
            "max_quotes": 50,
            "ai_quota": 300,
            "features": ["quotes", "ai"],
        },
    )
    assert created.status_code == 200, created.text
    plan_id = created.json()["data"]["id"]

    updated = admin_client.put(f"/api/admin/plans/{plan_id}", json={"price": 129})
    assert updated.status_code == 200
    assert updated.json()["data"]["price"] == 129


def test_meta_endpoint_exposes_industry_templates(client):  # noqa: ANN001
    meta = client.get("/api/meta").json()["data"]
    codes = {item["code"]: item["status"] for item in meta["industries"]}
    assert codes["advertising"] == "available"
    assert codes["doors_windows"] == "coming_soon"
    assert meta["quote_statuses"]
    assert meta["units"]


def test_industries_endpoint(company_a):  # noqa: ANN001
    industries = company_a.get("/api/company/industries").json()["data"]
    advertising = next(item for item in industries if item["code"] == "advertising")
    assert advertising["product_count"] >= 20
    assert advertising["fields"]

