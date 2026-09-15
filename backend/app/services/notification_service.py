"""站内通知。第一版只做站内消息，预留短信/邮件/微信接口。"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.customer import Notification


def push(
    db: Session,
    *,
    company_id: int,
    user_id: int | None,
    title: str,
    content: str = "",
    type: str = "system",  # noqa: A002
    link: str | None = None,
    meta: dict | None = None,
) -> Notification:
    notification = Notification(
        company_id=company_id,
        user_id=user_id,
        title=title,
        content=content,
        type=type,
        link=link,
        meta=meta or {},
    )
    db.add(notification)
    return notification


def unread_count(db: Session, company_id: int, user_id: int | None) -> int:
    stmt = select(func.count()).select_from(Notification).where(
        Notification.company_id == company_id, Notification.is_read.is_(False)
    )
    if user_id:
        stmt = stmt.where((Notification.user_id == user_id) | (Notification.user_id.is_(None)))
    return int(db.scalar(stmt) or 0)


def mark_read(db: Session, company_id: int, notification_id: int) -> None:
    notification = db.get(Notification, notification_id)
    if notification and notification.company_id == company_id:
        notification.is_read = True


def mark_all_read(db: Session, company_id: int, user_id: int | None) -> int:
    stmt = select(Notification).where(Notification.company_id == company_id, Notification.is_read.is_(False))
    if user_id:
        stmt = stmt.where((Notification.user_id == user_id) | (Notification.user_id.is_(None)))
    items = list(db.scalars(stmt))
    for item in items:
        item.is_read = True
    return len(items)


class Notifier:
    """通知抽象层：未来接入短信/邮件/微信，只需实现同一接口。"""

    def send_sms(self, phone: str, content: str) -> bool:  # pragma: no cover - 预留
        return False

    def send_email(self, email: str, subject: str, content: str) -> bool:  # pragma: no cover - 预留
        return False

    def send_wechat(self, openid: str, content: str) -> bool:  # pragma: no cover - 预留
        return False


notifier = Notifier()

