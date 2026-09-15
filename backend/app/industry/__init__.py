"""行业模板：报价引擎的核心抽象。

底层永远是「报价引擎 + 行业模板」：
  - 报价引擎（认证、多租户、规则计算、报价单、AI 编排、计费）与行业无关
  - 行业模板只描述：产品分类、产品、字段、公式、规则、报价模板、Prompt
未来新增门窗/包装/机械加工，只需新增一个模板文件，不复制项目。
"""

from app.industry.base import IndustryTemplate, SeedProduct, SeedRule
from app.industry.registry import get_template, industry_registry, list_templates

__all__ = [
    "IndustryTemplate",
    "SeedProduct",
    "SeedRule",
    "get_template",
    "industry_registry",
    "list_templates",
]

