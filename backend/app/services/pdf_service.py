"""报价单输出：HTML/CSS → PDF。

三级降级策略，保证任何环境都能出单：
  1. WeasyPrint（Docker/Linux，HTML+CSS 高保真排版）
  2. fpdf2 + 中文字体（Windows / 无 Pango 环境）
  3. 打印用 HTML（浏览器直接打印或另存为 PDF）
"""

from __future__ import annotations

import html
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.core.config import settings

logger = logging.getLogger("quote_engine.app")


def _money(value: Any) -> str:
    try:
        return f"{Decimal(str(value or 0)):,.2f}"
    except Exception:  # pragma: no cover
        return "0.00"


def _esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def build_quote_html(payload: dict[str, Any]) -> str:
    """生成报价单 HTML（在线报价页与 PDF 共用同一套样式）。"""
    company = payload.get("company") or {}
    items = payload.get("items") or []
    tiers = payload.get("tiers") or {}
    accent = payload.get("accent_color") or "#635BFF"

    rows = []
    for index, item in enumerate(items, start=1):
        size = ""
        if item.get("width") and item.get("height"):
            size = f"{item['width']}m × {item['height']}m"
        rows.append(
            "<tr>"
            f"<td class='num'>{index}</td>"
            f"<td><div class='pname'>{_esc(item.get('product_name'))}</div>"
            f"<div class='pspec'>{_esc(item.get('category_name') or '')}"
            f"{' · ' + _esc(item.get('spec')) if item.get('spec') else ''}"
            f"{' · ' + _esc(size) if size else ''}</div></td>"
            f"<td class='num'>{_esc(item.get('quantity'))} {_esc(item.get('unit'))}</td>"
            f"<td class='num'>{_money(item.get('unit_price'))}</td>"
            f"<td class='num strong'>{_money(item.get('final_price'))}</td>"
            "</tr>"
        )

    tier_cards = ""
    if tiers:
        order = ["economy", "standard", "premium"]
        cards = []
        for level in order:
            tier = tiers.get(level)
            if not tier:
                continue
            highlight = " highlight" if level == "standard" else ""
            cards.append(
                f"<div class='tier{highlight}'>"
                f"<div class='tier-name'>{_esc(tier.get('name'))}</div>"
                f"<div class='tier-amount'>¥{_money(tier.get('total_amount'))}</div>"
                "</div>"
            )
        tier_cards = f"<div class='tiers'>{''.join(cards)}</div>"

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<title>报价单 {_esc(payload.get('quote_no'))}</title>
<style>
  @page {{ size: A4; margin: 14mm 12mm; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: "Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", sans-serif;
         color: #111827; margin: 0; font-size: 12px; line-height: 1.6; }}
  .head {{ display: flex; justify-content: space-between; align-items: flex-start;
           border-bottom: 2px solid {accent}; padding-bottom: 14px; }}
  .brand {{ font-size: 20px; font-weight: 700; letter-spacing: .5px; }}
  .brand small {{ display: block; font-size: 11px; color: #6B7280; font-weight: 400; margin-top: 4px; }}
  .meta {{ text-align: right; font-size: 11px; color: #6B7280; }}
  .meta .no {{ font-size: 15px; color: #111827; font-weight: 600; }}
  .grid {{ display: flex; gap: 24px; margin: 18px 0 8px; }}
  .grid > div {{ flex: 1; }}
  .label {{ font-size: 10px; letter-spacing: 1px; color: #9CA3AF; text-transform: uppercase; }}
  .value {{ font-size: 13px; font-weight: 600; margin-top: 2px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 14px; }}
  th {{ background: #F6F7FB; font-size: 11px; color: #6B7280; font-weight: 600;
        text-align: left; padding: 9px 10px; border-bottom: 1px solid #E5E7EB; }}
  th.num, td.num {{ text-align: right; }}
  td {{ padding: 11px 10px; border-bottom: 1px solid #F1F2F6; vertical-align: top; }}
  .pname {{ font-weight: 600; }}
  .pspec {{ font-size: 11px; color: #9CA3AF; margin-top: 2px; }}
  .strong {{ font-weight: 700; }}
  .totals {{ margin-top: 16px; margin-left: auto; width: 46%; }}
  .totals .row {{ display: flex; justify-content: space-between; padding: 5px 0; color: #4B5563; }}
  .totals .row.total {{ border-top: 2px solid #111827; margin-top: 6px; padding-top: 10px;
                        font-size: 17px; font-weight: 700; color: #111827; }}
  .tiers {{ display: flex; gap: 12px; margin-top: 20px; }}
  .tier {{ flex: 1; border: 1px solid #E5E7EB; border-radius: 12px; padding: 12px 14px; }}
  .tier.highlight {{ border-color: {accent}; background: #F7F6FF; }}
  .tier-name {{ font-size: 11px; color: #6B7280; }}
  .tier-amount {{ font-size: 16px; font-weight: 700; margin-top: 4px; }}
  .terms {{ margin-top: 22px; font-size: 11px; color: #4B5563; }}
  .terms h4 {{ font-size: 12px; margin: 12px 0 4px; color: #111827; }}
  .terms p {{ margin: 0; white-space: pre-wrap; }}
  .foot {{ margin-top: 26px; padding-top: 12px; border-top: 1px solid #E5E7EB;
           display: flex; justify-content: space-between; font-size: 11px; color: #9CA3AF; }}
</style>
</head>
<body>
  <div class="head">
    <div class="brand">
      {_esc(company.get('name') or '报价单')}
      <small>{_esc(company.get('address') or '')}</small>
    </div>
    <div class="meta">
      <div class="no">{_esc(payload.get('quote_no'))}</div>
      <div>版本 V{_esc(payload.get('version_no') or 1)}</div>
      <div>日期 {_esc((payload.get('created_at') or '')[:10])}</div>
      <div>有效期至 {_esc((payload.get('valid_until') or '')[:10])}</div>
    </div>
  </div>

  <div class="grid">
    <div>
      <div class="label">客户</div>
      <div class="value">{_esc(payload.get('customer_name') or '—')}</div>
    </div>
    <div>
      <div class="label">项目名称</div>
      <div class="value">{_esc(payload.get('project_name') or '—')}</div>
    </div>
    <div>
      <div class="label">联系人</div>
      <div class="value">{_esc(company.get('contact_name') or '—')} {_esc(company.get('contact_phone') or '')}</div>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th style="width:36px">#</th>
        <th>产品 / 规格</th>
        <th class="num">数量</th>
        <th class="num">单价</th>
        <th class="num">金额</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows) if rows else "<tr><td colspan='5'>暂无报价明细</td></tr>"}
    </tbody>
  </table>

  <div class="totals">
    <div class="row"><span>小计</span><span>¥{_money(payload.get('subtotal'))}</span></div>
    {f'<div class="row"><span>优惠</span><span>-¥{_money(payload.get("discount_amount"))}</span></div>' if float(payload.get('discount_amount') or 0) else ''}
    {f'<div class="row"><span>税费</span><span>¥{_money(payload.get("tax_amount"))}</span></div>' if float(payload.get('tax_amount') or 0) else ''}
    <div class="row total"><span>合计</span><span>¥{_money(payload.get('total_amount'))}</span></div>
  </div>

  {tier_cards}

  <div class="terms">
    <h4>付款条款</h4>
    <p>{_esc(payload.get('payment_terms') or '')}</p>
    <h4>服务条款</h4>
    <p>{_esc(payload.get('service_terms') or '')}</p>
    {f'<h4>备注</h4><p>{_esc(payload.get("notes"))}</p>' if payload.get('notes') else ''}
  </div>

  <div class="foot">
    <span>{_esc(company.get('name') or '')} · 微信 {_esc(company.get('contact_wechat') or '—')}</span>
    <span>本报价单由报价引擎生成 · {datetime.now():%Y-%m-%d}</span>
  </div>
</body>
</html>"""


def html_to_pdf(source: str) -> bytes | None:
    """HTML/CSS → PDF。环境不支持时返回 None，由调用方降级为打印页面。"""
    try:  # 1. WeasyPrint（首选，CSS 保真度最高）
        from weasyprint import HTML  # noqa: PLC0415

        return HTML(string=source).write_pdf()
    except Exception as exc:  # pragma: no cover - 依赖系统库
        logger.info("WeasyPrint 不可用（%s），尝试 fpdf2 渲染", type(exc).__name__)

    try:  # 2. fpdf2 + 中文字体
        return _pdf_with_fpdf(source)
    except Exception as exc:  # pragma: no cover
        logger.warning("fpdf2 渲染失败：%s", exc)
        return None


def _plain_text_from_html(source: str) -> list[str]:
    import re  # noqa: PLC0415

    text = re.sub(r"<style.*?</style>", "", source, flags=re.S | re.I)
    text = re.sub(r"<(br|/tr|/table|/div|/p|/h4)\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return [line for line in lines if line]


def _pdf_with_fpdf(source: str) -> bytes:
    """无 Pango 环境下的 PDF 渲染（Windows 本地开发 / 未装系统库的服务器）。"""
    from fpdf import FPDF  # noqa: PLC0415
    from fpdf.enums import XPos, YPos  # noqa: PLC0415

    font_path = settings.cjk_font
    pdf = FPDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    family = "helvetica"
    if font_path:
        try:
            # 常规与加粗都注册，避免 set_font(..., "B") 报 Undefined font。
            pdf.add_font("cjk", "", str(font_path))
            pdf.add_font("cjk", "B", str(font_path))
            family = "cjk"
        except Exception as exc:  # noqa: BLE001
            logger.warning("中文字体注册失败（%s），改用内置字体：%s", font_path.name, exc)
            family = "helvetica"

    def write(text: str, size: int = 10, style: str = "", height: float = 5.4) -> None:
        pdf.set_font(family, style, size)
        # fpdf2 默认 new_x=RIGHT，会让后续 multi_cell 没有可用宽度，必须显式回到左边距。
        pdf.multi_cell(0, height, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    for index, line in enumerate(_plain_text_from_html(source)):
        if index == 0:
            write(line, size=15, style="B", height=8)
        elif index < 4:
            write(line, size=11, style="B")
        else:
            write(line)
    return bytes(pdf.output())


def quote_pdf(payload: dict[str, Any]) -> bytes | None:
    return html_to_pdf(build_quote_html(payload))
