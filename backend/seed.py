"""演示数据初始化脚本。

用法：
    python seed.py           # 幂等：已存在则不重复创建
    python seed.py --reset   # 清空数据库并重新灌入完整演示数据

执行后可直接登录：
    管理员  admin@example.com / Admin123456!
    演示企业 demo@example.com  / Demo123456!
"""

from __future__ import annotations

import argparse
import logging
import random
import sys
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.core.config import settings
from app.core.db import reset_database_schema, session_scope
from app.core.logging import setup_logging
from app.core.security import hash_password
from app.models.ai import AITask, AIUsage
from app.models.base import utcnow
from app.models.company import Company, Member
from app.models.customer import Customer, Followup, Notification
from app.models.product import Product
from app.models.quote import Quote, QuoteItem, QuoteView, QuoteVersion
from app.models.user import User
from app.services import bootstrap, quote_service
from app.services.ai.usage_tracker import estimate_cost

logger = logging.getLogger("quote_engine.seed")

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "Demo123456!"
DEMO_COMPANY = "星辰广告制作"

random.seed(20260915)


CUSTOMERS = [
    ("XX餐饮（万达店）", "李经理", "13800001111", "微信转介绍", "high_intent"),
    ("XX地产营销中心", "王主管", "13900002222", "电话咨询", "communicating"),
    ("XX酒店（高铁站店）", "张店长", "13700003333", "老客户复购", "quoted"),
    ("XX购物中心", "陈经理", "13600004444", "自然到访", "high_intent"),
    ("老周烧烤", "周老板", "13500005555", "微信咨询", "won"),
    ("XX连锁药房", "刘女士", "13400006666", "朋友介绍", "new"),
    ("XX汽车美容", "赵老板", "13300007777", "抖音咨询", "communicating"),
    ("XX教育机构", "孙老师", "13200008888", "微信咨询", "lost"),
    ("XX健身房", "胡教练", "13100009999", "转介绍", "quoted"),
    ("XX便利店（3家店）", "吴老板", "13000001010", "老客户复购", "high_intent"),
]

PROJECTS = [
    ("XX餐饮门头制作", "帮我做一个10米门头，铝塑板底，12个发光字，月底安装", 0),
    ("XX地产营销中心门头", "门头 8米×1.8米 铝塑板，加不锈钢发光字 16个，需要上门安装", 1),
    ("XX酒店楼顶大字", "楼顶要做亚克力发光字 20个，1.2米高，含高空安装", 2),
    ("XX商场导视系统", "一共 12 块导视牌，亚克力材质，需要安装到商场各楼层", 3),
    ("老周烧烤门头加灯箱", "门头 6米×1.5米 喷绘布，加两个 LED 灯箱，尽快做", 4),
    ("XX连锁药房店招", "5 家门店统一店招，每家 4米×1.2米 铝塑板，配发光字 8 个", 5),
    ("XX汽车美容车间标识", "车间标识牌 8 块，不锈钢材质，含运输", 6),
    ("XX教育机构大厅写真", "大厅背景墙高清写真 3.6米×2.4米，需要覆膜", 7),
    ("XX健身房灯箱", "健身房门口超薄灯箱 2 个，1.2米×0.8米", 8),
    ("XX便利店门头统一改造", "3 家店门头统一做铝合金门头，每家 5米×1.5米", 9),
    ("XX餐饮二层围挡", "二楼围挡喷绘 20米×2米，含安装", 0),
    ("XX地产围挡广告", "工地围挡 60米×3米 喷绘布，需要运输到现场", 1),
    ("XX酒店宴会厅指示牌", "宴会厅指示牌 6 块，亚克力，1.2米×0.4米", 2),
    ("XX商场中庭展架", "中庭活动 X 展架 20 个，含画面", 3),
    ("XX餐饮门贴", "玻璃门贴高清写真 2.4米×1.6米", 4),
    ("XX便利店发光字维护", "招牌发光字 4 个不亮，需要维修更换", 5),
    ("XX汽车美容门头升级", "门头升级做不锈钢门头 9米×1.6米，加发光字 14 个", 6),
    ("XX教育机构导视牌", "楼道导视牌 10 块，PVC 材质，含安装", 7),
    ("XX健身房门头", "健身房门头 7米×1.8米 铝塑板，发光字 10 个", 8),
    ("XX酒店大堂灯箱", "大堂 LED 灯箱 1 个，2米×1.2米，超薄款", 9),
]

STATUS_SEQUENCE = (
    ["sent", "viewed", "won", "viewed", "following", "sent", "viewed", "won", "draft", "sent"]
    + ["viewed", "won", "following", "sent", "viewed", "won", "following", "viewed", "sent", "draft"]
)

INSTALL_RATE = {"安装": 800, "高空安装": 1600}


def _ensure_demo_user(db) -> User:  # noqa: ANN001
    user = db.scalar(select(User).where(User.email == DEMO_EMAIL))
    if user is None:
        user = User(
            email=DEMO_EMAIL,
            phone="13800000000",
            name="张老板",
            password_hash=hash_password(DEMO_PASSWORD),
            status="active",
            is_superadmin=False,
        )
        db.add(user)
        db.flush()
    return user


def _ensure_demo_company(db, user: User) -> Company:  # noqa: ANN001
    member = db.scalar(select(Member).where(Member.user_id == user.id).limit(1))
    if member:
        company = db.get(Company, member.company_id)
        if company:
            return company

    from app.services import provisioning  # noqa: PLC0415

    company = provisioning.provision_company(
        db,
        name=DEMO_COMPANY,
        industry_id="advertising",
        owner=user,
        with_default_data=True,
    )
    company.contact_name = "张老板"
    company.contact_phone = "13800000000"
    company.contact_wechat = "xingchen_ad"
    company.address = "杭州市余杭区文一西路 1234 号"
    company.credit_code = "91330110MA2XXXXXXX"
    company.default_footer = "星辰广告制作 · 用心做好每一块招牌"
    db.flush()
    return company


def _ensure_customers(db, company: Company, owner: User) -> list[Customer]:  # noqa: ANN001
    existing = list(db.scalars(select(Customer).where(Customer.company_id == company.id)))
    if existing:
        return existing
    customers: list[Customer] = []
    for index, (name, contact, phone, source, status) in enumerate(CUSTOMERS):
        customer = Customer(
            company_id=company.id,
            name=name,
            contact_name=contact,
            phone=phone,
            wechat=phone,
            source=source,
            status=status,
            owner_user_id=owner.id,
            remark="演示客户数据",
            created_at=utcnow() - timedelta(days=40 - index * 3),
            last_contact_at=utcnow() - timedelta(days=index),
            next_followup_at=utcnow() + timedelta(days=(index % 4) - 1, hours=9),
        )
        db.add(customer)
        customers.append(customer)
    db.flush()
    return customers


def _requirements_for_project(text: str, project_name: str, company: Company) -> dict:  # noqa: ANN001
    """把一个项目描述转换成结构化需求（走与 AI 相同的 Mock 解析链路）。"""
    from app.services.ai import mock_provider  # noqa: PLC0415

    requirement = mock_provider.mock_requirement(text, has_image=False)
    requirement["project_name"] = project_name

    # Demo 模式下补全缺失值，让演示可以完整出单
    for item in requirement["items"]:
        if item["category"] == "门头" and not item.get("height"):
            item["height"] = 1.55
        if item["category"] == "门头" and not item.get("width"):
            item["width"] = 8.0
        if item["category"] == "发光字":
            item["width"] = 0.6
            item["height"] = 0.6

    # 补充安装与运输项（如果有对应产品）
    install_product = _product_for(company, "安装")
    transport_product = _product_for(company, "运输")
    high_install = _product_for(company, "高空安装")

    needs_high = "高空" in text or "楼顶" in text
    if install_product is not None:
        product = high_install if needs_high and high_install else install_product
        requirement["items"].append(
            {
                "category": "安装",
                "product_name": product.name,
                "quantity": 1,
                "unit": product.unit,
                "width": None,
                "height": None,
                "depth": None,
            }
        )
    if transport_product is not None and ("运输" in text or "送货" in text or random.random() < 0.6):
        requirement["items"].append(
            {
                "category": "运输",
                "product_name": transport_product.name,
                "quantity": 1,
                "unit": transport_product.unit,
                "width": None,
                "height": None,
                "depth": None,
            }
        )
    requirement["customer_name"] = None
    requirement["installation_location"] = "杭州市余杭区文一西路 1234 号"
    requirement["missing_fields"] = [field for field in requirement.get("missing_fields", []) if field not in ("门头高度", "安装地址")]
    requirement["confidence"] = 0.9
    return requirement


_PRODUCT_INDEX: dict[tuple[int, str], Product] = {}


def _product_for(company: Company, name: str) -> Product | None:
    return _PRODUCT_INDEX.get((company.id, name))


def _index_products(db, company: Company) -> None:  # noqa: ANN001
    products = db.scalars(select(Product).where(Product.company_id == company.id)).all()
    for product in products:
        _PRODUCT_INDEX[(company.id, product.name)] = product


def _seed_quotes(db, company: Company, owner: User, customers: list[Customer]) -> list[Quote]:  # noqa: ANN001
    existing = int(db.scalar(select(func.count()).select_from(Quote).where(Quote.company_id == company.id)) or 0)
    if existing:
        return list(db.scalars(select(Quote).where(Quote.company_id == company.id)))

    quotes: list[Quote] = []
    for index, (project_name, text, customer_index) in enumerate(PROJECTS):
        customer = customers[customer_index % len(customers)]
        requirement = _requirements_for_project(text, project_name, company)
        requirement["customer_name"] = customer.name

        quote = quote_service.create_quote(
            db,
            company_id=company.id,
            user_id=owner.id,
            requirement=requirement,
            requirement_text=text,
            customer_id=customer.id,
            customer_name=customer.name,
            project_name=project_name,
            source="ai",
        )
        created_at = utcnow() - timedelta(days=max(19 - index, 0), hours=index % 12)
        quote.created_at = created_at
        quote.updated_at = created_at
        status = STATUS_SEQUENCE[index % len(STATUS_SEQUENCE)]
        quote.status = status
        if status in ("sent", "viewed", "following", "won"):
            quote_service.mark_sent(db, quote, valid_days=15)
            quote.sent_at = created_at + timedelta(hours=2)
        if status in ("viewed", "following", "won"):
            quote.view_count = random.randint(1, 5)
            quote.first_viewed_at = created_at + timedelta(hours=6)
            quote.last_viewed_at = created_at + timedelta(hours=random.randint(8, 60))
            db.add(
                QuoteView(
                    company_id=company.id,
                    quote_id=quote.id,
                    viewed_at=quote.last_viewed_at,
                    device_type=random.choice(["mobile", "desktop", "mobile"]),
                    is_first_view=True,
                    user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
                )
            )
        if status == "won":
            quote.won_at = created_at + timedelta(days=random.randint(1, 5))
            quote_service.change_status(db, quote, "won", user_id=owner.id)
        quote.version_no = 1
        quote.created_at = created_at
        queries = list(db.scalars(select(QuoteVersion).where(QuoteVersion.quote_id == quote.id)))
        if not queries:
            db.add(
                QuoteVersion(
                    company_id=company.id,
                    quote_id=quote.id,
                    version_no=1,
                    total_amount=quote.total_amount,
                    total_cost=quote.total_cost,
                    gross_margin=quote.gross_margin,
                    tiers=quote.tiers,
                    snapshot={"total_amount": float(quote.total_amount or 0)},
                    change_note="创建报价",
                    created_by=owner.id,
                    created_at=created_at,
                )
            )
        customer.quote_count = (customer.quote_count or 0) + 1
        quotes.append(quote)

    for customer in customers:
        won = [quote for quote in quotes if quote.customer_id == customer.id and quote.status == "won"]
        customer.deal_count = len(won)
        customer.total_amount = sum((quote.total_amount or Decimal("0")) for quote in won)
    db.flush()
    return quotes


def _seed_followups(  # noqa: ANN001
    db, company: Company, owner: User, customers: list[Customer], quotes: list[Quote]
) -> None:
    existing = int(db.scalar(select(func.count()).select_from(Followup).where(Followup.company_id == company.id)) or 0)
    if existing:
        return
    contents = [
        "已电话沟通，客户要求本周五前给出最终报价，重点看安装费用。",
        "客户觉得价格偏高，已发送材料说明与质保政策，等待回复。",
        "客户确认尺寸无误，等门店负责人签字后即可下单。",
        "已上门测量，实际门头宽度 9.6 米，需要重新调整报价。",
        "客户询问能否分期，已说明公司付款政策，等待领导决策。",
    ]
    statuses = ["communicating", "high_intent", "quoted", "new", "high_intent"]
    for index, content in enumerate(contents):
        customer = customers[index]
        # 把跟进记录关联到该客户最近的一份报价，让转化漏斗（报价→查看→跟进→成交）真实可算。
        related = next(
            (quote for quote in quotes if quote.customer_id == customer.id and quote.status != "draft"),
            None,
        )
        db.add(
            Followup(
                company_id=company.id,
                customer_id=customer.id,
                quote_id=related.id if related else None,
                user_id=owner.id,
                status=statuses[index],
                content=content,
                channel=random.choice(["wechat", "phone", "visit"]),
                next_followup_at=utcnow() + timedelta(days=(index % 3) - 1, hours=10),
                created_at=utcnow() - timedelta(days=index + 1),
            )
        )
    db.flush()


def _seed_ai_history(db, company: Company, owner: User, quotes: list[Quote]) -> None:  # noqa: ANN001
    existing = int(db.scalar(select(func.count()).select_from(AIUsage).where(AIUsage.company_id == company.id)) or 0)
    if existing:
        return
    task_types = [
        ("requirement_extract", "deepseek-v4-flash-vision-exp", 1800, 620),
        ("missing_fields", "deepseek-v4-flash", 900, 300),
        ("reply_draft", "deepseek-v4-flash", 1200, 480),
        ("price_explain", "deepseek-v4-pro", 2200, 900),
        ("price_suggestion", "deepseek-v4-pro", 1600, 520),
    ]
    for index, (task_type, model, tokens_in, tokens_out) in enumerate(task_types * 4):
        created_at = utcnow() - timedelta(days=index % 14, hours=index % 8)
        status = "failed" if index == 17 else "success"
        task = AITask(
            company_id=company.id,
            user_id=owner.id,
            task_type=task_type,
            status=status,
            provider="deepseek",
            model=model,
            mode="mock",
            input_payload={"demo": True},
            output_payload={"demo": True},
            raw_response="(mock mode: 演示数据)",
            error_message="AI 暂时繁忙，请稍后重试。" if status == "failed" else None,
            confidence=0.9 if status == "success" else None,
            input_tokens=tokens_in,
            output_tokens=tokens_out,
            latency_ms=random.randint(800, 4200),
            estimated_cost=estimate_cost(model, tokens_in, tokens_out),
            created_at=created_at,
            finished_at=created_at,
        )
        db.add(task)
        db.flush()
        db.add(
            AIUsage(
                company_id=company.id,
                user_id=owner.id,
                task_id=task.id,
                task_type=task_type,
                model=model,
                input_tokens=tokens_in,
                output_tokens=tokens_out,
                estimated_cost=estimate_cost(model, tokens_in, tokens_out),
                status=status,
                created_at=created_at,
            )
        )
    db.flush()


def _seed_notifications(db, company: Company, owner: User, quotes: list[Quote]) -> None:  # noqa: ANN001
    existing = int(db.scalar(select(func.count()).select_from(Notification).where(Notification.company_id == company.id)) or 0)
    if existing:
        return
    for quote in quotes[:6]:
        if quote.status in ("viewed", "won", "following"):
            db.add(
                Notification(
                    company_id=company.id,
                    user_id=owner.id,
                    type="quote_viewed",
                    title="客户查看了报价",
                    content=f"{quote.customer_name} 查看了报价单 {quote.quote_no}",
                    link=f"/app/quotes/{quote.id}",
                    is_read=False,
                    created_at=(quote.last_viewed_at or utcnow()),
                )
            )
    db.add(
        Notification(
            company_id=company.id,
            user_id=owner.id,
            type="followup",
            title="今日有待跟进客户",
            content="今日有客户需要跟进，建议优先联系高意向客户。",
            link="/app/followups",
            created_at=utcnow(),
        )
    )
    db.flush()


def seed_demo(db) -> dict:  # noqa: ANN001
    user = _ensure_demo_user(db)
    company = _ensure_demo_company(db, user)
    _index_products(db, company)
    customers = _ensure_customers(db, company, user)
    quotes = _seed_quotes(db, company, user, customers)
    _seed_followups(db, company, user, customers, quotes)
    _seed_ai_history(db, company, user, quotes)
    _seed_notifications(db, company, user, quotes)
    return {
        "company": company.name,
        "company_id": company.id,
        "customers": len(customers),
        "quotes": len(quotes),
        "products": int(db.scalar(select(func.count()).select_from(Product).where(Product.company_id == company.id)) or 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化报价引擎演示数据")
    parser.add_argument("--reset", action="store_true", help="清空数据库并重新灌入演示数据")
    parser.add_argument("--no-demo", action="store_true", help="只创建套餐与管理员，不创建演示企业")
    args = parser.parse_args()

    setup_logging()
    if args.reset:
        logger.warning("正在重置数据库结构……")
        reset_database_schema()

    with session_scope() as db:
        info = bootstrap.bootstrap(db)
        result = None
        if not args.no_demo:
            result = seed_demo(db)

    print("\n" + "=" * 62)
    print("  报价引擎 Quote Engine — 初始化完成")
    print("=" * 62)
    print(f"  管理员账号 : {settings.admin_email} / {settings.admin_password}")
    if result:
        print(f"  演示企业   : {DEMO_EMAIL} / {DEMO_PASSWORD}")
        print(f"  企业名称   : {result['company']}（{result['products']} 个产品，"
              f"{result['customers']} 个客户，{result['quotes']} 份报价）")
    print(f"  AI 模式    : {settings.ai_mode}")
    print(f"  数据库     : {'SQLite（本地）' if settings.is_sqlite else 'PostgreSQL'}")
    print("=" * 62 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
