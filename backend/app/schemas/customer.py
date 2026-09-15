"""客户与跟进 Schema。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    contact_name: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    wechat: str | None = Field(default=None, max_length=80)
    source: str | None = Field(default=None, max_length=50)
    address: str | None = None
    remark: str | None = None
    status: str = "new"
    next_followup_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    contact_name: str | None = None
    phone: str | None = None
    wechat: str | None = None
    source: str | None = None
    address: str | None = None
    remark: str | None = None
    status: str | None = None
    next_followup_at: datetime | None = None
    tags: list[str] | None = None


class CustomerOut(BaseModel):
    id: int
    name: str
    contact_name: str | None = None
    phone: str | None = None
    wechat: str | None = None
    source: str | None = None
    address: str | None = None
    remark: str | None = None
    status: str
    tags: list[str] = Field(default_factory=list)
    quote_count: int = 0
    deal_count: int = 0
    total_amount: float = 0
    next_followup_at: datetime | None = None
    last_contact_at: datetime | None = None
    created_at: datetime | None = None


class FollowupCreate(BaseModel):
    customer_id: int
    quote_id: int | None = None
    content: str = Field(default="", max_length=2000)
    status: str = "communicating"
    next_followup_at: datetime | None = None
    channel: str = "wechat"


class FollowupUpdate(BaseModel):
    content: str | None = Field(default=None, max_length=2000)
    status: str | None = None
    next_followup_at: datetime | None = None
    done: bool | None = None


class FollowupOut(BaseModel):
    id: int
    customer_id: int
    customer_name: str | None = None
    quote_id: int | None = None
    user_id: int | None = None
    status: str
    content: str
    next_followup_at: datetime | None = None
    done: bool = False
    channel: str = "wechat"
    created_at: datetime | None = None

