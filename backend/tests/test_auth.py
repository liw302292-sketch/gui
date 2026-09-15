"""验收 1-3：注册、自动创建企业、登录、进入工作台。"""

from __future__ import annotations


def test_register_creates_company_and_user(client):  # noqa: ANN001
    response = client.post(
        "/api/auth/register",
        json={
            "phone": "13900001111",
            "password": "Hello12345",
            "name": "李老板",
            "company_name": "李记广告",
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["company"]["name"] == "李记广告"
    assert data["access_token"]

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["data"]["company"]["role"] == "owner"


def test_register_rejects_weak_password(client):  # noqa: ANN001
    response = client.post(
        "/api/auth/register",
        json={"email": "weak@example.com", "password": "12345678", "company_name": "弱密码公司"},
    )
    assert response.status_code == 422
    assert "密码" in response.json()["message"]


def test_register_duplicate_email(client):  # noqa: ANN001
    payload = {"email": "dup@example.com", "password": "Hello12345", "company_name": "重复公司"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    second = client.post("/api/auth/register", json=payload)
    assert second.status_code == 409
    assert "已经注册" in second.json()["message"]


def test_login_and_logout(client):  # noqa: ANN001
    login = client.post("/api/auth/login", json={"identifier": "dup@example.com", "password": "Hello12345"})
    assert login.status_code == 200, login.text
    assert client.get("/api/auth/me").status_code == 200

    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_login_wrong_password(client):  # noqa: ANN001
    response = client.post("/api/auth/login", json={"identifier": "dup@example.com", "password": "WrongPass1"})
    assert response.status_code == 401
    assert "不正确" in response.json()["message"]


def test_change_password(client):  # noqa: ANN001
    client.post("/api/auth/login", json={"identifier": "dup@example.com", "password": "Hello12345"})
    response = client.post(
        "/api/auth/change-password",
        json={"old_password": "Hello12345", "new_password": "NewPass12345"},
    )
    assert response.status_code == 200, response.text
    relogin = client.post("/api/auth/login", json={"identifier": "dup@example.com", "password": "NewPass12345"})
    assert relogin.status_code == 200


def test_bearer_token_works(client):  # noqa: ANN001
    response = client.post(
        "/api/auth/login",
        json={"identifier": "company.a@example.com", "password": "Test123456!"},
    )
    token = response.json()["data"]["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200


def test_protected_route_requires_auth(client):  # noqa: ANN001
    anonymous = client.get("/api/quotes")
    assert anonymous.status_code == 401
    assert "登录" in anonymous.json()["message"]


def test_health_and_meta(client):  # noqa: ANN001
    health = client.get("/api/health").json()
    assert health["ok"] is True
    assert health["ai_mode"] in ("mock", "real")
    assert client.get("/api/meta").json()["data"]["units"]

