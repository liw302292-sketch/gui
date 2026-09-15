"""行业模板数据结构定义。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

FieldType = Literal["number", "text", "select", "boolean", "unit"]


@dataclass(frozen=True)
class FieldDef:
    """行业专属字段定义，驱动前端表单与 AI 提取校验。"""

    key: str
    label: str
    type: FieldType = "number"
    unit: str | None = None
    required: bool = False
    options: tuple[str, ...] = ()
    help_text: str = ""


@dataclass(frozen=True)
class SeedProduct:
    """行业预置产品（Demo 数据，企业可自由修改，不代表行业统一价格）。"""

    category: str
    name: str
    unit: str
    pricing_mode: str
    cost_price: float
    default_price: float
    loss_rate: float = 0.05
    labor_cost: float = 0.0
    labor_price_per_unit: float = 0.0
    transport_cost: float = 0.0
    other_cost: float = 0.0
    min_profit_margin: float = 0.25
    markup_rate: float = 0.35
    spec: str = ""
    model: str = ""
    remark: str = ""


@dataclass(frozen=True)
class SeedRule:
    category: str
    name: str
    rule_type: str
    params: dict[str, Any] = field(default_factory=dict)
    conditions: dict[str, Any] = field(default_factory=dict)
    priority: int = 100
    description: str = ""


@dataclass(frozen=True)
class IndustryTemplate:
    code: str
    name: str
    description: str
    status: Literal["available", "coming_soon"] = "coming_soon"
    sort_order: int = 100

    units: tuple[str, ...] = ("平方米", "米", "个", "套", "张", "块", "项", "公斤", "件", "车")
    pricing_modes: tuple[tuple[str, str], ...] = (
        ("fixed", "固定单价（数量 × 单价）"),
        ("area", "面积（宽 × 高 × 数量 × 单价）"),
        ("volume", "体积（长 × 宽 × 高 × 数量 × 单价）"),
        ("weight", "重量（重量 × 单价）"),
        ("cost_plus", "成本加成（成本 × (1 + 加价率)）"),
        ("margin", "毛利率（成本 / (1 - 毛利率)）"),
    )
    fields: tuple[FieldDef, ...] = ()
    categories: tuple[str, ...] = ()
    products: tuple[SeedProduct, ...] = ()
    rules: tuple[SeedRule, ...] = ()
    payment_terms: str = "签订合同预付 50%，验收合格后付清余款。"
    service_terms: str = "报价含标准工艺与现场安装；因现场条件变化产生的额外费用另行协商。"
    footer: str = "感谢您的信任，我们会在每个环节严格把控品质。"
    prompts: dict[str, str] = field(default_factory=dict)
    quote_template_name: str = "标准报价模板"

    @property
    def available(self) -> bool:
        return self.status == "available"

    def to_summary(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "sort_order": self.sort_order,
            "categories": list(self.categories),
            "product_count": len(self.products),
            "pricing_modes": [{"value": value, "label": label} for value, label in self.pricing_modes],
            "fields": [
                {
                    "key": fd.key,
                    "label": fd.label,
                    "type": fd.type,
                    "unit": fd.unit,
                    "required": fd.required,
                    "options": list(fd.options),
                    "help_text": fd.help_text,
                }
                for fd in self.fields
            ],
        }

