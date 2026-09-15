"""广告标识 / 广告制作行业模板（第一版唯一开放行业）。

注意：以下产品与价格仅为演示数据，不代表真实行业统一价格，企业创建后可自由修改。
"""

from __future__ import annotations

from app.industry.base import FieldDef, IndustryTemplate, SeedProduct, SeedRule

DOOR = "门头"
LETTER = "发光字"
LIGHTBOX = "灯箱"
SIGN = "标牌"
PRINT = "喷绘"
PHOTO = "写真"
DISPLAY = "展架"
GUIDE = "导视"
INSTALL = "安装"
TRANSPORT = "运输"

PRODUCTS: tuple[SeedProduct, ...] = (
    SeedProduct(DOOR, "铝塑板门头", "平方米", "area", 145, 280, 0.06, labor_price_per_unit=55, min_profit_margin=0.28, spec="4mm 铝塑板 + 方管骨架"),
    SeedProduct(DOOR, "不锈钢门头", "平方米", "area", 320, 620, 0.05, labor_price_per_unit=75, min_profit_margin=0.3, spec="201 不锈钢板 + 骨架"),
    SeedProduct(DOOR, "亚克力门头", "平方米", "area", 260, 520, 0.06, labor_price_per_unit=65, min_profit_margin=0.3, spec="亚克力面板 + LED 背光"),
    SeedProduct(DOOR, "烤漆门头", "平方米", "area", 210, 430, 0.07, labor_price_per_unit=70, min_profit_margin=0.28, spec="镀锌板 + 汽车漆"),
    SeedProduct(LETTER, "发光字", "个", "fixed", 45, 95, 0.05, min_profit_margin=0.3, spec="常规 0.6m 内"),
    SeedProduct(LETTER, "不锈钢发光字", "个", "fixed", 120, 245, 0.05, min_profit_margin=0.32, spec="不锈钢围边 + LED 模组"),
    SeedProduct(LETTER, "亚克力发光字", "个", "fixed", 85, 175, 0.05, min_profit_margin=0.32, spec="亚克力面板 + LED 模组"),
    SeedProduct(LETTER, "PVC发光字", "个", "fixed", 55, 118, 0.06, min_profit_margin=0.3, spec="PVC 面板 + LED"),
    SeedProduct(LETTER, "树脂发光字", "个", "fixed", 150, 320, 0.05, min_profit_margin=0.33, spec="树脂浇注 + LED"),
    SeedProduct(LIGHTBOX, "LED灯箱", "个", "fixed", 180, 380, 0.05, min_profit_margin=0.3, spec="铝型材 + 灯布"),
    SeedProduct(LIGHTBOX, "超薄灯箱", "个", "fixed", 150, 320, 0.05, min_profit_margin=0.3, spec="导光板 + 铝框"),
    SeedProduct(LIGHTBOX, "拉布灯箱", "平方米", "area", 165, 330, 0.05, min_profit_margin=0.28, spec="铝型材 + 拉布"),
    SeedProduct(PRINT, "喷绘布", "平方米", "area", 12, 30, 0.08, min_profit_margin=0.35, spec="550 高精喷绘"),
    SeedProduct(PRINT, "UV打印", "平方米", "area", 40, 95, 0.06, min_profit_margin=0.35, spec="UV 硬质材料打印"),
    SeedProduct(PHOTO, "高清写真", "平方米", "area", 18, 45, 0.07, min_profit_margin=0.35, spec="室内写真 + 覆膜"),
    SeedProduct(SIGN, "PVC展板", "块", "fixed", 35, 80, 0.05, min_profit_margin=0.35, spec="5mm PVC 板"),
    SeedProduct(SIGN, "亚克力牌", "块", "fixed", 60, 140, 0.05, min_profit_margin=0.35, spec="5mm 亚克力"),
    SeedProduct(SIGN, "不锈钢牌", "块", "fixed", 110, 240, 0.05, min_profit_margin=0.35, spec="拉丝不锈钢"),
    SeedProduct(DISPLAY, "X展架", "套", "fixed", 45, 110, 0.05, min_profit_margin=0.35, spec="80×180cm 含画面"),
    SeedProduct(GUIDE, "导视牌", "块", "fixed", 180, 420, 0.05, min_profit_margin=0.32, spec="定制尺寸"),
    SeedProduct(INSTALL, "安装", "项", "fixed", 0, 800, 0.0, min_profit_margin=0.2, remark="常规门头安装，按项目计"),
    SeedProduct(INSTALL, "高空安装", "项", "fixed", 0, 1600, 0.0, min_profit_margin=0.2, remark="含脚手架与高空作业"),
    SeedProduct(TRANSPORT, "运输", "车", "fixed", 0, 300, 0.0, min_profit_margin=0.15, remark="市区内单趟"),
)

RULES: tuple[SeedRule, ...] = (
    SeedRule(
        category=DOOR,
        name="门头大面积批发价",
        rule_type="condition",
        conditions={"all": [{"field": "area", "op": ">", "value": 20}]},
        params={"unit_price": 245},
        priority=10,
        description="门头面积超过 20㎡ 时启用批发单价",
    ),
    SeedRule(
        category=LETTER,
        name="发光字批量折扣",
        rule_type="condition",
        conditions={"all": [{"field": "quantity", "op": ">=", "value": 20}]},
        params={"unit_price": 210, "min_profit_margin": 0.28},
        priority=20,
        description="发光字数量 ≥ 20 个时启用批量单价",
    ),
    SeedRule(
        category=INSTALL,
        name="高空安装人工费",
        rule_type="labor",
        params={"labor_cost": 600},
        priority=30,
        description="高空作业固定人工费",
    ),
    SeedRule(
        category=TRANSPORT,
        name="运输按公里计价",
        rule_type="transport",
        params={"transport_cost": 300},
        priority=30,
        description="市区内单趟运输费，超出范围另行协商",
    ),
)

FIELDS: tuple[FieldDef, ...] = (
    FieldDef("width", "宽度", "number", "米", help_text="门头/画面的横向尺寸"),
    FieldDef("height", "高度", "number", "米", help_text="门头/画面的纵向尺寸"),
    FieldDef("depth", "厚度", "number", "米", help_text="灯箱或立体字厚度"),
    FieldDef("quantity", "数量", "number", "个/件", required=True),
    FieldDef("material", "材质", "select", options=("铝塑板", "不锈钢", "亚克力", "PVC", "镀锌板", "其他")),
    FieldDef("process", "工艺", "select", options=("发光", "烤漆", "UV打印", "丝印", "覆膜", "无")),
    FieldDef("installation", "是否需要安装", "boolean"),
    FieldDef("installation_location", "安装地址", "text", help_text="影响运输与高空作业费用"),
    FieldDef("transport_required", "是否需要运输", "boolean"),
    FieldDef("deadline", "交付时间", "text"),
)

ADVERTISING_TEMPLATE = IndustryTemplate(
    code="advertising",
    name="广告标识",
    description="门头、发光字、灯箱、标牌、喷绘写真、展架、导视、安装与运输",
    status="available",
    sort_order=1,
    categories=(DOOR, LETTER, LIGHTBOX, SIGN, PRINT, PHOTO, DISPLAY, GUIDE, INSTALL, TRANSPORT),
    fields=FIELDS,
    products=PRODUCTS,
    rules=RULES,
    payment_terms="签订合同预付 50%，制作完成验收合格后付清余款。",
    service_terms=(
        "1. 本报价含标准工艺制作与现场安装，不含因现场条件变化产生的额外费用。\n"
        "2. 报价有效期内价格不变，逾期需重新确认。\n"
        "3. 发光类产品免费质保 12 个月（人为损坏除外）。"
    ),
    footer="星辰广告制作 · 用心做好每一块招牌",
    prompts={},
    quote_template_name="广告标识标准报价模板",
)
