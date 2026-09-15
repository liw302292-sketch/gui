"""验收 5-13：上传需求 → 识别 → 计算 → 报价单 → 公开链接 → 客户查看 → 已查看。"""

from __future__ import annotations

import io

from PIL import Image


def _png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 48), (99, 91, 255)).save(buffer, format="PNG")
    return buffer.getvalue()


def _with_height(requirement: dict, height: float = 1.5) -> list[dict]:
    items = []
    for item in requirement["items"]:
        item = dict(item)
        if item.get("category") == "门头" and not item.get("height"):
            item["height"] = height
        items.append(item)
    return items


def test_ai_extract_from_wechat_screenshot(company_a):  # noqa: ANN001
    response = company_a.post("/api/ai/extract", files={"file": ("wechat.png", _png_bytes(), "image/png")})
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["mode"] == "mock"
    requirement = data["requirement"]
    assert requirement["items"], "应识别出报价项目"
    assert any(item["category"] == "门头" for item in requirement["items"])
    assert "门头高度" in requirement["missing_fields"]
    assert requirement["missing_questions"]
    assert data["file_id"]


def test_ai_extract_from_text(company_a, requirement):  # noqa: ANN001
    assert requirement["project_name"]
    door = next(item for item in requirement["items"] if item["category"] == "门头")
    assert float(door["width"]) == 10.0
    letters = next(item for item in requirement["items"] if item["category"] == "发光字")
    assert float(letters["quantity"]) == 12


def test_manual_edit_then_create_quote(company_a, requirement):  # noqa: ANN001
    payload = {
        "project_name": "自动化测试门头",
        "customer_name": "测试客户",
        "items": _with_height(requirement),
        "requirement_text": "帮我做一个10米门头，铝塑板底，12个发光字，月底安装",
        "transport_required": True,
    }
    response = company_a.post("/api/quotes", json=payload)
    assert response.status_code == 200, response.text
    quote = response.json()["data"]

    assert quote["quote_no"].startswith("Q-")
    assert quote["total_amount"] > 0
    assert quote["total_cost"] > 0
    assert 0 < quote["gross_margin"] < 1
    assert len(quote["items"]) >= 2
    for item in quote["items"]:
        assert item["formula"]
        assert item["breakdown"]
        assert item["final_price"] > 0
    assert quote["tiers"]["standard"]["total_amount"] == quote["total_amount"]
    assert quote["tiers"]["economy"]["total_amount"] < quote["tiers"]["premium"]["total_amount"]


def test_quote_detail_versions_and_audit(company_a, requirement):  # noqa: ANN001
    created = company_a.post(
        "/api/quotes",
        json={"project_name": "版本测试", "customer_name": "版本客户", "items": _with_height(requirement)},
    ).json()["data"]
    quote_id = created["id"]
    assert company_a.get(f"/api/quotes/{quote_id}").status_code == 200

    updated = company_a.put(
        f"/api/quotes/{quote_id}",
        json={
            "discount_amount": 200,
            "change_note": "客户要求优惠 200",
            "items": [
                {
                    "product_name": item["product_name"],
                    "category": item["category_name"],
                    "unit": item["unit"],
                    "quantity": item["quantity"],
                    "width": item["width"],
                    "height": item["height"],
                    "unit_price": item["unit_price"],
                    "cost_price": item["cost_price"],
                }
                for item in created["items"]
            ],
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["data"]["version_no"] == 2
    assert updated.json()["data"]["discount_amount"] == 200

    versions = company_a.get(f"/api/quotes/{quote_id}/versions").json()["data"]["versions"]
    assert len(versions) >= 2

    audit = company_a.get(f"/api/quotes/{quote_id}/audit").json()["data"]
    assert any(entry["action"] == "quote.update" for entry in audit)
    assert any(entry["after"].get("total_amount") is not None for entry in audit if entry["after"])


def test_public_quote_link_and_view_tracking(company_a, requirement):  # noqa: ANN001
    quote = company_a.post(
        "/api/quotes",
        json={"project_name": "公开链接测试", "customer_name": "链接客户", "items": _with_height(requirement)},
    ).json()["data"]
    quote_id = quote["id"]

    sent = company_a.post(f"/api/quotes/{quote_id}/send", json={"valid_days": 15})
    assert sent.status_code == 200, sent.text
    token = sent.json()["data"]["public_token"]
    assert token and token.lower() not in sent.json()["data"]["public_url"].lower().replace(token.lower(), "")

    public = company_a.client.get(f"/api/quote-public/{token}")
    assert public.status_code == 200, public.text
    payload = public.json()["data"]
    assert payload["quote"]["total_amount"] > 0
    assert "internal" not in payload["quote"], "客户端绝不能看到成本与利润"
    assert payload["company"]["name"]

    detail = company_a.get(f"/api/quotes/{quote_id}").json()["data"]
    assert detail["status"] == "viewed"
    assert detail["view_count"] == 1
    assert detail["first_viewed_at"]

    notifications = company_a.get("/api/company/notifications").json()["data"]["items"]
    assert any(item["type"] == "quote_viewed" for item in notifications)


def test_password_protected_public_quote(company_a, requirement):  # noqa: ANN001
    quote = company_a.post(
        "/api/quotes",
        json={"project_name": "密码报价", "customer_name": "密码客户", "items": _with_height(requirement)},
    ).json()["data"]
    token = company_a.post(f"/api/quotes/{quote['id']}/send", json={"password": "8888"}).json()["data"]["public_token"]

    locked = company_a.client.get(f"/api/quote-public/{token}").json()["data"]
    assert locked["requires_password"] is True
    assert locked["quote"] is None

    wrong = company_a.client.get(f"/api/quote-public/{token}", params={"password": "0000"})
    assert wrong.status_code == 401

    ok = company_a.client.get(f"/api/quote-public/{token}", params={"password": "8888"})
    assert ok.status_code == 200
    assert ok.json()["data"]["quote"]["total_amount"] > 0


def test_public_quote_pdf_download(company_a, requirement):  # noqa: ANN001
    quote = company_a.post(
        "/api/quotes",
        json={"project_name": "PDF测试", "customer_name": "PDF客户", "items": _with_height(requirement)},
    ).json()["data"]
    token = company_a.post(f"/api/quotes/{quote['id']}/send", json={}).json()["data"]["public_token"]

    response = company_a.client.get(f"/api/quote-public/{token}/pdf")
    assert response.status_code == 200
    content_type = response.headers["content-type"]
    assert content_type.startswith(("application/pdf", "text/html"))
    if content_type.startswith("application/pdf"):
        assert response.content[:4] == b"%PDF"
        assert len(response.content) > 2000


def test_quote_status_and_won_updates_customer(company_a, requirement):  # noqa: ANN001
    quote = company_a.post(
        "/api/quotes",
        json={"project_name": "成交测试", "customer_name": "成交客户", "items": _with_height(requirement)},
    ).json()["data"]

    won = company_a.post(f"/api/quotes/{quote['id']}/status", json={"status": "won", "note": "客户已签合同"})
    assert won.status_code == 200
    assert won.json()["data"]["status"] == "won"

    customers = company_a.get("/api/customers", params={"keyword": "成交客户"}).json()["data"]["items"]
    assert customers and customers[0]["deal_count"] == 1
    assert customers[0]["total_amount"] > 0


def test_quote_empty_items_rejected(company_a):  # noqa: ANN001
    response = company_a.post("/api/quotes", json={"project_name": "空报价", "items": []})
    assert response.status_code == 409
