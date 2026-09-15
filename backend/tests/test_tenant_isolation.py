"""验收 15：企业数据严格隔离。"""

from __future__ import annotations

from tests.test_quote_flow import _with_height


def test_products_are_isolated(company_a, company_b):  # noqa: ANN001
    product = company_a.post(
        "/api/products",
        json={"name": "A公司专属产品", "unit": "个", "pricing_mode": "fixed", "cost_price": 10, "default_price": 30},
    ).json()["data"]

    assert company_b.get(f"/api/products/{product['id']}").status_code == 404
    listed = company_b.get("/api/products", params={"page_size": 200, "keyword": "A公司专属产品"}).json()["data"]
    assert listed["total"] == 0


def test_customers_are_isolated(company_a, company_b):  # noqa: ANN001
    customer = company_a.post("/api/customers", json={"name": "A公司客户"}).json()["data"]
    assert company_b.get(f"/api/customers/{customer['id']}").status_code == 404
    assert company_b.put(f"/api/customers/{customer['id']}", json={"remark": "越权修改"}).status_code == 404
    assert company_a.get(f"/api/customers/{customer['id']}").json()["data"]["customer"]["remark"] in (None, "")


def test_quotes_are_isolated(company_a, company_b, requirement):  # noqa: ANN001
    quote = company_a.post(
        "/api/quotes",
        json={"project_name": "隔离测试项目", "customer_name": "隔离客户", "items": _with_height(requirement)},
    ).json()["data"]

    assert company_b.get(f"/api/quotes/{quote['id']}").status_code == 404
    assert company_b.post(f"/api/quotes/{quote['id']}/status", json={"status": "won"}).status_code == 404
    assert company_b.delete(f"/api/quotes/{quote['id']}").status_code == 404

    listed = company_b.get("/api/quotes").json()["data"]["items"]
    assert all(item["id"] != quote["id"] for item in listed)


def test_files_are_isolated(company_a, company_b):  # noqa: ANN001
    import io

    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), (0, 0, 0)).save(buffer, format="PNG")
    uploaded = company_a.post(
        "/api/files/upload", files={"file": ("a.png", buffer.getvalue(), "image/png")}
    ).json()["data"]
    assert company_b.get(f"/api/files/{uploaded['id']}").status_code == 404


def test_dashboard_is_scoped_to_company(company_a, company_b):  # noqa: ANN001
    dashboard_a = company_a.get("/api/company/dashboard").json()["data"]
    dashboard_b = company_b.get("/api/company/dashboard").json()["data"]
    assert dashboard_a["company"]["id"] != dashboard_b["company"]["id"]

