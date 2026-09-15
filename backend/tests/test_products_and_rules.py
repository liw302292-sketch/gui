"""验收 8：产品价格库与价格规则的可配置性。"""

from __future__ import annotations


def test_seeded_categories_and_products(company_a):  # noqa: ANN001
    categories = company_a.get("/api/products/categories").json()["data"]
    names = [item["name"] for item in categories]
    assert "门头" in names and "发光字" in names and "运输" in names

    products = company_a.get("/api/products", params={"page_size": 100}).json()["data"]
    product_names = [item["name"] for item in products["items"]]
    assert "铝塑板门头" in product_names
    assert "不锈钢发光字" in product_names
    assert products["total"] >= 20


def test_create_update_delete_product(company_a):  # noqa: ANN001
    categories = company_a.get("/api/products/categories").json()["data"]
    category_id = categories[0]["id"]

    created = company_a.post(
        "/api/products",
        json={
            "name": "测试灯箱",
            "category_id": category_id,
            "unit": "个",
            "pricing_mode": "fixed",
            "cost_price": 200,
            "default_price": 420,
            "min_profit_margin": 0.3,
        },
    )
    assert created.status_code == 200, created.text
    product_id = created.json()["data"]["id"]
    assert created.json()["data"]["gross_margin_preview"] > 0.4

    updated = company_a.put(f"/api/products/{product_id}", json={"default_price": 460})
    assert updated.status_code == 200
    assert updated.json()["data"]["default_price"] == 460

    assert company_a.delete(f"/api/products/{product_id}").status_code == 200
    assert company_a.get(f"/api/products/{product_id}").status_code == 404


def test_price_rule_crud_and_types(company_a):  # noqa: ANN001
    categories = company_a.get("/api/products/categories").json()["data"]
    door = next(item for item in categories if item["name"] == "门头")

    rules = company_a.get("/api/price-rules").json()["data"]
    assert any(rule["rule_type"] == "condition" for rule in rules)

    created = company_a.post(
        "/api/price-rules",
        json={
            "name": "测试固定人工费",
            "category_id": door["id"],
            "rule_type": "labor",
            "params": {"labor_cost": 500},
            "priority": 5,
        },
    )
    assert created.status_code == 200, created.text
    rule_id = created.json()["data"]["id"]

    types = {item["value"] for item in company_a.get("/api/price-rules/types").json()["data"]}
    assert types >= {"fixed", "area", "volume", "weight", "cost_plus", "margin", "loss", "labor", "transport", "condition"}

    assert company_a.delete(f"/api/price-rules/{rule_id}").status_code == 200


def test_price_rule_changes_quote_result(company_a, requirement):  # noqa: ANN001
    from tests.test_quote_flow import _with_height

    items = _with_height(requirement)
    before = company_a.post(
        "/api/quotes", json={"project_name": "规则前", "items": items}
    ).json()["data"]

    categories = company_a.get("/api/products/categories").json()["data"]
    door = next(item for item in categories if item["name"] == "门头")
    rule = company_a.post(
        "/api/price-rules",
        json={
            "name": "门头测试条件价",
            "category_id": door["id"],
            "rule_type": "condition",
            "conditions": {"all": [{"field": "area", "op": ">", "value": 5}]},
            "params": {"unit_price": 999},
            "priority": 1,
        },
    ).json()["data"]

    after = company_a.post(
        "/api/quotes", json={"project_name": "规则后", "items": items}
    ).json()["data"]
    assert after["total_amount"] > before["total_amount"], "新增高价规则后报价应上升"

    company_a.delete(f"/api/price-rules/{rule['id']}")


def test_category_conflict_when_products_exist(company_a):  # noqa: ANN001
    categories = company_a.get("/api/products/categories").json()["data"]
    door = next(item for item in categories if item["name"] == "门头" and item["product_count"] > 0)
    response = company_a.delete(f"/api/products/categories/{door['id']}")
    assert response.status_code == 409


def test_import_template_columns(company_a):  # noqa: ANN001
    template = company_a.get("/api/products/template/download").json()["data"]
    assert "产品名称" in template["columns"]
    assert "默认报价" in template["columns"]
    assert template["example"]["单位"]

