"""行业模板注册表。新增行业只需在此注册，核心 SaaS 代码不变。"""

from __future__ import annotations

from app.core.errors import NotFoundError
from app.industry.base import IndustryTemplate
from app.industry.templates.advertising import ADVERTISING_TEMPLATE


class IndustryRegistry:
    def __init__(self) -> None:
        self._templates: dict[str, IndustryTemplate] = {}

    def register(self, template: IndustryTemplate) -> None:
        self._templates[template.code] = template

    def get(self, code: str) -> IndustryTemplate:
        template = self._templates.get(code)
        if template is None:
            raise NotFoundError(f"未找到行业模板：{code}")
        return template

    def get_or_default(self, code: str | None) -> IndustryTemplate:
        if code and code in self._templates:
            return self._templates[code]
        return ADVERTISING_TEMPLATE

    def all(self) -> list[IndustryTemplate]:
        return sorted(self._templates.values(), key=lambda item: item.sort_order)

    def available(self) -> list[IndustryTemplate]:
        return [template for template in self.all() if template.available]

    def summaries(self) -> list[dict[str, object]]:
        return [template.to_summary() for template in self.all()]


industry_registry = IndustryRegistry()
industry_registry.register(ADVERTISING_TEMPLATE)

# 未来行业：只需新增一个模板文件并注册，核心 SaaS 代码零改动。
# 以下为占位展示，第一版不开放，避免 MVP 复杂化。
for _code, _name, _desc, _order in (
    ("doors_windows", "门窗", "门窗、阳光房、幕墙的按尺寸报价", 10),
    ("packaging", "包装印刷", "纸箱、彩盒、标签的按量与工艺报价", 20),
    ("machining", "机械加工", "零件加工、非标设备按工时与材料报价", 30),
):
    industry_registry.register(
        IndustryTemplate(code=_code, name=_name, description=_desc, status="coming_soon", sort_order=_order)
    )


def get_template(code: str | None = None) -> IndustryTemplate:
    return industry_registry.get_or_default(code)


def list_templates() -> list[dict[str, object]]:
    return industry_registry.summaries()
