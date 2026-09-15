"""Mock AI：没有 API Key 时的确定性输出，保证产品完整可演示。"""

from __future__ import annotations

import re
from typing import Any


def _find_number(text: str, keywords: list[str]) -> float | None:
    for keyword in keywords:
        match = re.search(rf"(\d+(?:\.\d+)?)\s*(?:米|m|M)?\s*{keyword}", text)
        if match:
            return float(match.group(1))
        match = re.search(rf"{keyword}\D{{0,6}}(\d+(?:\.\d+)?)", text)
        if match:
            return float(match.group(1))
    return None


def mock_requirement(text: str = "", has_image: bool = False) -> dict[str, Any]:
    """根据输入文本生成结构化需求；未提供的信息一律 null 并进入 missing_fields。"""
    content = text or ""
    if not content and has_image:
        content = "帮我做一个10米门头，铝塑板底，12个发光字，月底安装"

    items: list[dict[str, Any]] = []
    missing: list[str] = []
    unknown: list[str] = []

    has_door = bool(re.search(r"门头|招牌|店招", content))
    height = _find_number(content, ["高", "高度"]) if has_door else None
    width = _find_number(content, ["米", "m", "M"]) if has_door else None

    if has_door:
        if width and width >= 1000:
            width = width / 1000
        elif width and width >= 100:
            width = width / 100
        material = "铝塑板" if "铝塑板" in content else ("不锈钢" if "不锈钢" in content else None)
        items.append(
            {
                "category": "门头",
                "product_name": f"{material}门头" if material else "门头制作",
                "width": width,
                "height": height,
                "depth": None,
                "quantity": 1,
                "unit": "平方米",
                "material": material,
                "process": [],
                "installation": True,
                "remark": None,
                "source": content[:80],
            }
        )
        if height is None:
            missing.append("门头高度")

    letter_match = re.search(r"(\d+)\s*(?:个|块)?\s*(?:发光字|字)", content)
    letter_count = int(letter_match.group(1)) if letter_match else None
    if letter_count is not None or "发光字" in content:
        material = "不锈钢" if "不锈钢" in content else ("亚克力" if "亚克力" in content else None)
        items.append(
            {
                "category": "发光字",
                "product_name": f"{material}发光字" if material else "发光字",
                "width": None,
                "height": None,
                "depth": None,
                "quantity": letter_count or 1,
                "unit": "个",
                "material": material,
                "process": [],
                "installation": True,
                "remark": None,
                "source": f"{letter_count}个发光字" if letter_count else "发光字",
            }
        )
        if letter_count is None:
            missing.append("发光字数量")
        missing.append("发光字单个尺寸")

    if "灯箱" in content and not any(item["category"] == "灯箱" for item in items):
        items.append(
            {
                "category": "灯箱",
                "product_name": "LED灯箱",
                "width": None,
                "height": None,
                "depth": None,
                "quantity": 1,
                "unit": "个",
                "material": None,
                "process": [],
                "installation": True,
                "remark": None,
                "source": "灯箱",
            }
        )
        missing.append("灯箱尺寸")

    if not items:
        unknown.append("未识别到明确的广告制作需求，请补充文字说明或上传更清晰的截图")

    deadline = None
    for keyword in ("月底", "本周", "下周", "月底前", "尽快", "这个月"):
        if keyword in content:
            deadline = keyword
            break
    if deadline is None:
        match = re.search(r"(\d+月\d+[日号]前?)", content)
        if match:
            deadline = match.group(1)

    installation_required = bool(re.search(r"安装|上门|施工", content)) or bool(items)
    if installation_required and not re.search(r"地址|位置|哪里|XX|xx", content):
        missing.append("安装地址")
    if not re.search(r"运输|送货|自提|运费", content):
        missing.append("是否需要运输")
    if deadline is None:
        missing.append("交付时间")

    project_name = "门头制作项目" if has_door else (f"{items[0]['category']}制作项目" if items else None)

    return {
        "project_name": project_name,
        "customer_name": None,
        "items": items,
        "transport_required": True if "运输" in content else None,
        "installation_required": installation_required if items else None,
        "installation_location": None,
        "deadline": deadline,
        "missing_fields": sorted(set(missing)),
        "unknown_fields": unknown,
        "inference": {"notes": "Mock 模式：以上为演示用识别结果，缺失信息已标记，需要人工确认后报价。"},
        "confidence": 0.86 if items else 0.2,
    }


def mock_missing_fields(requirement: dict[str, Any]) -> dict[str, Any]:
    question_map = {
        "门头高度": ("门头高度", "您好，门头的高度大概是多少米？这样我才能准确算出面积。", "high"),
        "发光字单个尺寸": ("发光字尺寸", "发光字大概多大？例如 0.6 米高还是 1 米高？", "high"),
        "发光字数量": ("发光字数量", "门头上一共需要几个字？", "high"),
        "安装地址": ("安装地址", "安装的具体位置在哪里？在市区还是周边？", "medium"),
        "是否需要运输": ("运输需求", "需要我们送货到现场吗？还是您自己取货？", "medium"),
        "交付时间": ("交付时间", "您希望什么时候安装完成？", "medium"),
        "灯箱尺寸": ("灯箱尺寸", "灯箱大概多大？长宽各是多少？", "high"),
    }
    questions = []
    for field in requirement.get("missing_fields") or []:
        mapped = question_map.get(field)
        if mapped:
            questions.append({"field": mapped[0], "question": mapped[1], "impact": mapped[2]})
        else:
            questions.append({"field": field, "question": f"请补充一下{field}的信息。", "impact": "medium"})
    return {
        "questions": questions[:6],
        "summary": f"还有 {len(questions[:6])} 项信息可能影响最终报价" if questions else "信息已经比较完整",
    }


def mock_reply(requirement: dict[str, Any], quote: dict[str, Any], style: str) -> dict[str, Any]:
    total = quote.get("total_amount") or 0
    amount = f"{float(total):,.0f}" if total else "待确认"
    lines = []
    for item in (requirement.get("items") or [])[:4]:
        size = ""
        if item.get("width") and item.get("height"):
            size = f"（{item['width']}m × {item['height']}m）"
        lines.append(
            f"· {item.get('product_name') or item.get('category')} {size} × "
            f"{item.get('quantity', 1)}{item.get('unit', '')}"
        )
    detail = "\n".join(lines) if lines else "· 需求待确认"

    if style == "concise":
        content = (
            f"您好，您的需求我们看了，报价约 ¥{amount}（含材料、制作与安装）。\n{detail}\n"
            "确认细节后即可安排生产，您看什么时候方便？"
        )
    elif style == "closing":
        content = (
            f"您好，方案已经按您的需求做好了：\n{detail}\n合计 ¥{amount}，含材料、制作、安装与售后。\n"
            "本周确认下单，我们可以优先排产，确保不耽误您的开业时间。需要我现在把详细报价单发您吗？"
        )
    else:
        content = (
            "您好，感谢信任，我们已经根据您的需求整理出报价：\n"
            f"{detail}\n合计：¥{amount}（含材料、制作、安装，不含额外增项）\n\n"
            "报价已包含标准工艺与现场安装。如需调整材质或工艺，我们可以再优化方案。您确认后我们即可安排生产。"
        )
    if requirement.get("missing_fields"):
        content += "\n\n另外还需要确认：" + "、".join(requirement["missing_fields"][:3]) + "。"

    return {
        "style": style,
        "title": None,
        "content": content,
        "follow_up_suggestion": "建议 24 小时内跟进一次，确认尺寸与安装地址后重新出正式报价。",
    }


def mock_explain(question: str, quote: dict[str, Any]) -> dict[str, Any]:
    return {
        "reasons": [
            "材料成本：门头底板与发光字使用户外级材料，抗晒抗雨，正常使用 3-5 年不褪色。",
            "工艺成本：发光字需要开槽、布灯、做防水处理，工艺越精细成型效果越均匀。",
            "安装成本：门头属于高空作业，涉及脚手架、人工与安全措施，安装费用占比不低。",
            "运输与损耗：大尺寸板材运输损耗较高，这部分已按行业常规预留。",
            "售后保障：含质保与一次免费上门维护，出现问题我们负责到底。",
        ],
        "customer_reply": (
            "理解您的顾虑，给您说明一下：这份报价里的门头底板和发光字都是户外级材料，"
            "发光字还要做开槽、布灯和防水，安装属于高空作业需要脚手架和人工。"
            "我们报的是含材料、制作、安装和售后的整体价格，不是单纯的板材价格。"
            "同价位下我们可以保证用料和安装质量，后续有问题我们负责维护。"
        ),
        "adjust_options": [
            "把不锈钢发光字换成亚克力发光字，外观接近但成本更低。",
            "门头底板改用更经济的材料做局部处理。",
            "安装安排在非高峰期，可适当降低人工成本。",
        ],
        "tone": "自信、专业、不卑不亢",
    }


def mock_suggestion(requirement: dict[str, Any], history: dict[str, Any]) -> dict[str, Any]:
    samples = history.get("samples") or []
    average = history.get("average_amount") or 0
    low = history.get("min_amount") or 0
    high = history.get("max_amount") or 0
    if not samples or not average:
        return {
            "range_low": None,
            "range_high": None,
            "unit_suggestion": "按平方米计价",
            "basis": "历史成交样本不足，无法给出可靠区间。",
            "sample_size": 0,
            "confidence": 0.0,
            "caution": "样本不足，本建议仅供参考，最终价格以企业规则引擎计算为准。",
        }
    return {
        "range_low": round(low * 0.95, 0),
        "range_high": round(high * 1.05, 0),
        "unit_suggestion": "按平方米 / 按个 组合计价",
        "basis": (
            f"参考 {len(samples)} 条同类历史成交报价，成交均价 ¥{average:,.0f}，"
            f"区间 ¥{low:,.0f} ~ ¥{high:,.0f}。"
        ),
        "sample_size": len(samples),
        "confidence": min(0.5 + len(samples) * 0.05, 0.9),
        "caution": "本区间仅为参考建议，最终价格必须由企业规则引擎计算产生。",
    }

