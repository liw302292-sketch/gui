"""集中式配置管理。

所有配置项通过环境变量注入；任何模块都不允许硬编码 API Key、模型名或价格。
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


class Settings(BaseSettings):
    """应用配置。字段名与环境变量一一对应（大小写不敏感）。"""

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---------- 基础 ----------
    app_name: str = "Quote Engine"
    app_env: Literal["development", "production", "test"] = "development"
    app_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"
    app_secret_key: str = "dev-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    refresh_token_expire_days: int = 30
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # ---------- 数据库 ----------
    database_url: str = ""
    database_echo: bool = False

    # ---------- Redis ----------
    redis_url: str = ""

    # ---------- AI ----------
    ai_mode: Literal["mock", "real"] = "mock"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_text_model: str = "deepseek-v4-flash"
    deepseek_reasoning_model: str = "deepseek-v4-pro"
    deepseek_vision_model: str = "deepseek-v4-flash-vision-exp"
    ai_request_timeout_seconds: int = 120
    ai_max_retries: int = 2
    ai_price_flash_input: float = 0.0
    ai_price_flash_output: float = 0.0
    ai_price_pro_input: float = 0.0
    ai_price_pro_output: float = 0.0
    ai_price_vision_input: float = 0.0
    ai_price_vision_output: float = 0.0

    # ---------- 存储 ----------
    storage_backend: Literal["local", "s3"] = "local"
    storage_local_dir: str = "./storage/uploads"
    storage_endpoint: str = ""
    storage_region: str = "us-east-1"
    storage_access_key: str = ""
    storage_secret_key: str = ""
    storage_bucket: str = "quote-engine"
    storage_public_base_url: str = ""
    max_upload_mb: int = 20

    # ---------- 安全 ----------
    rate_limit_per_minute: int = 240
    ai_rate_limit_per_minute: int = 20
    register_rate_limit_per_hour: int = 30
    login_rate_limit_per_5min: int = 30
    login_max_failures: int = 8
    login_lockout_minutes: int = 15

    # ---------- 演示数据 ----------
    seed_demo_data: bool = True
    admin_email: str = "admin@example.com"
    admin_password: str = "Admin123456!"
    demo_email: str = "demo@example.com"
    demo_password: str = "Demo123456!"

    # ---------- 支付 ----------
    payment_provider: Literal["mock", "wechat", "alipay"] = "mock"
    payment_mock_auto_paid: bool = True

    # ---------- 日志 ----------
    log_level: str = "INFO"
    log_dir: str = "./logs"
    log_to_file: bool = False

    # ---------- 内置默认值（非环境变量） ----------
    default_industry: str = Field(default="advertising")

    @field_validator("ai_mode", mode="before")
    @classmethod
    def _auto_ai_mode(cls, value: object) -> object:
        """没有 API Key 时强制使用 mock，保证项目零配置可运行。"""
        key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        if not key and (value in (None, "", "real")):
            return "mock"
        return value

    # ---------- 派生属性 ----------
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_test(self) -> bool:
        return self.app_env == "test"

    @property
    def resolved_database_url(self) -> str:
        """未配置 DATABASE_URL 时使用本地 SQLite，做到零依赖启动。"""
        if self.database_url.strip():
            return self.database_url.strip()
        data_dir = BACKEND_DIR / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{(data_dir / 'quote_engine.db').as_posix()}"

    @property
    def is_sqlite(self) -> bool:
        return self.resolved_database_url.startswith("sqlite")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def storage_dir(self) -> Path:
        path = Path(self.storage_local_dir)
        if not path.is_absolute():
            path = (BACKEND_DIR / path).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def log_path(self) -> Path:
        path = Path(self.log_dir)
        if not path.is_absolute():
            path = (BACKEND_DIR / path).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def ai_enabled(self) -> bool:
        return self.ai_mode == "real" and bool(self.deepseek_api_key.strip())

    @property
    def cjk_font_candidates(self) -> list[Path]:
        return [
            BACKEND_DIR / "app" / "assets" / "fonts" / "NotoSansSC-Regular.otf",
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
            Path("C:/Windows/Fonts/msyh.ttc"),
            Path("C:/Windows/Fonts/simhei.ttf"),
            Path("/System/Library/Fonts/PingFang.ttc"),
        ]

    @property
    def cjk_font(self) -> Path | None:
        return _first_existing(self.cjk_font_candidates)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
