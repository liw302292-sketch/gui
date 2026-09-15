"""AI 服务层。

业务代码只与本模块交互，绝不允许直接调用 DeepSeek。
切换模型、切换供应商、切换 mock/real 都只改配置，不改业务代码。
"""

from app.services.ai.quotation_ai import QuotationAI, quotation_ai

__all__ = ["QuotationAI", "quotation_ai"]

