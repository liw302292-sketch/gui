"""测试夹具：独立测试数据库 + 认证客户端。"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parents[1] / "data"
TEST_DB = TEST_DIR / "test_quote_engine.db"
TEST_STORAGE = TEST_DIR / "test_storage"

# 必须在导入 app 之前设置环境变量
os.environ.update(
    {
        "APP_ENV": "test",
        "DATABASE_URL": f"sqlite:///{TEST_DB.as_posix()}",
        "REDIS_URL": "",
        "AI_MODE": "mock",
        "DEEPSEEK_API_KEY": "",
        "SEED_DEMO_DATA": "false",
        "STORAGE_LOCAL_DIR": str(TEST_STORAGE),
        "RATE_LIMIT_PER_MINUTE": "1000000",
        "AI_RATE_LIMIT_PER_MINUTE": "1000000",
        "REGISTER_RATE_LIMIT_PER_HOUR": "1000000",
        "LOGIN_RATE_LIMIT_PER_5MIN": "1000000",
        "LOGIN_MAX_FAILURES": "50",
        "APP_SECRET_KEY": "test-secret-key-for-pytest-only",
    }
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def prepared_database():
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    if TEST_DB.exists():
        TEST_DB.unlink()
    if TEST_STORAGE.exists():
        shutil.rmtree(TEST_STORAGE, ignore_errors=True)

    from app.core.db import reset_database_schema, session_scope
    from app.services import bootstrap

    reset_database_schema()
    with session_scope() as db:
        bootstrap.bootstrap(db)
    yield


@pytest.fixture()
def client(prepared_database):  # noqa: ANN001, ANN201
    """匿名客户端：每个测试独立 Cookie，便于验证未登录行为。"""
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def admin_client(prepared_database):  # noqa: ANN001, ANN201
    from app.main import app

    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/auth/login",
            json={"identifier": "admin@example.com", "password": "Admin123456!"},
        )
        assert response.status_code == 200, response.text
        yield ApiClient(test_client)


class ApiClient:
    """带鉴权的测试客户端封装。"""

    def __init__(self, client: TestClient) -> None:
        self.client = client

    def get(self, url: str, **kwargs):  # noqa: ANN201
        return self.client.get(url, **kwargs)

    def post(self, url: str, **kwargs):  # noqa: ANN201
        return self.client.post(url, **kwargs)

    def put(self, url: str, **kwargs):  # noqa: ANN201
        return self.client.put(url, **kwargs)

    def delete(self, url: str, **kwargs):  # noqa: ANN201
        return self.client.delete(url, **kwargs)


def _register_or_login(client: TestClient, email: str, company_name: str, name: str) -> ApiClient:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "Test123456!", "name": name, "company_name": company_name},
    )
    assert response.status_code in (201, 409), response.text
    if response.status_code == 409:
        login = client.post("/api/auth/login", json={"identifier": email, "password": "Test123456!"})
        assert login.status_code == 200, login.text
    return ApiClient(client)


@pytest.fixture(scope="session")
def company_a(prepared_database) -> ApiClient:  # noqa: ANN001
    from app.main import app

    with TestClient(app) as test_client:
        yield _register_or_login(test_client, "company.a@example.com", "A广告制作", "A老板")


@pytest.fixture(scope="session")
def company_b(prepared_database) -> ApiClient:  # noqa: ANN001
    from app.main import app

    with TestClient(app) as test_client:
        yield _register_or_login(test_client, "company.b@example.com", "B广告制作", "B老板")


DEMO_TEXT = "帮我做一个10米门头，铝塑板底，12个发光字，月底安装"


@pytest.fixture()
def requirement(company_a: ApiClient) -> dict:
    response = company_a.post("/api/ai/extract-text", json={"text": DEMO_TEXT})
    assert response.status_code == 200, response.text
    return response.json()["data"]["requirement"]
