"use client";

import { Badge } from "@/components/ui/badge";
import { cn, formatCurrency } from "@/lib/utils";

export function MockChat() {
  return (
    <div className="overflow-hidden rounded-[16px] border border-line bg-surface-2 p-4">
      <div className="mb-3 flex items-center justify-between text-[11.5px] text-muted">
        <span>XX餐饮 · 李经理</span>
        <span>微信</span>
      </div>
      <div className="space-y-2.5">
        <div className="max-w-[85%] rounded-2xl bg-white px-3.5 py-2.5 text-[13px] text-ink shadow-[var(--shadow-subtle)]">
          帮我做一个10米门头，铝塑板底
        </div>
        <div className="max-w-[85%] rounded-2xl bg-white px-3.5 py-2.5 text-[13px] text-ink shadow-[var(--shadow-subtle)]">
          再加12个发光字，月底要安装
        </div>
        <div className="ml-auto max-w-[70%] rounded-2xl bg-[#c6f0cf] px-3.5 py-2.5 text-[13px] text-[#0b4d22]">
          好的，我算一下给您报价
        </div>
      </div>
    </div>
  );
}

export function MockStructured() {
  const rows: [string, string, boolean][] = [
    ["项目", "XX餐饮门头制作", false],
    ["产品", "铝塑板门头", false],
    ["尺寸", "10m × 1.55m", false],
    ["发光字", "12 个", false],
    ["安装", "需要安装", false],
    ["安装地址", "待补充", true],
    ["发光字尺寸", "待补充", true],
  ];
  return (
    <div className="overflow-hidden rounded-[16px] border border-line bg-surface p-4">
      <div className="flex items-center justify-between">
        <span className="text-[13px] font-medium text-ink">识别结果（可人工修改）</span>
        <Badge tone="accent">置信度 91%</Badge>
      </div>
      <div className="mt-3 grid gap-x-6 sm:grid-cols-2">
        {rows.map(([label, value, missing]) => (
          <div key={label} className="flex items-center justify-between border-b border-line/70 py-2">
            <span className="text-[12.5px] text-muted">{label}</span>
            <span className={cn("text-[12.5px]", missing ? "text-warning" : "font-medium text-ink")}>{value}</span>
          </div>
        ))}
      </div>
      <div className="mt-3 rounded-xl border border-[#f6e0bd] bg-warning-soft px-3 py-2 text-[12px] text-[#8a4b00]">
        还有 3 项信息可能影响最终报价
      </div>
    </div>
  );
}

export function MockWorkbench() {
  const rows = [
    { name: "铝塑板门头", qty: "15.5 ㎡", cost: 3234.85, price: 4500, margin: "29.5%" },
    { name: "发光字", qty: "12 个", cost: 567, price: 1140, margin: "50.3%" },
    { name: "安装", qty: "1 项", cost: 600, price: 800, margin: "25.0%" },
  ];
  return (
    <div className="overflow-hidden rounded-[16px] border border-line bg-surface">
      <div className="flex items-center justify-between border-b border-line px-4 py-3">
        <span className="text-[13px] font-medium text-ink">报价明细</span>
        <span className="text-[11.5px] text-faint">价格由规则引擎计算</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-[12.5px]">
          <thead>
            <tr className="bg-surface-2 text-[11.5px] text-muted">
              <th className="px-4 py-2 text-left font-medium">项目</th>
              <th className="px-4 py-2 text-right font-medium">数量</th>
              <th className="px-4 py-2 text-right font-medium">成本</th>
              <th className="px-4 py-2 text-right font-medium">售价</th>
              <th className="px-4 py-2 text-right font-medium">毛利率</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.name} className="border-b border-line/60 last:border-0">
                <td className="px-4 py-2.5 font-medium text-ink">{row.name}</td>
                <td className="px-4 py-2.5 text-right text-muted">{row.qty}</td>
                <td className="px-4 py-2.5 text-right tabular-nums text-muted">{formatCurrency(row.cost)}</td>
                <td className="px-4 py-2.5 text-right tabular-nums text-ink">{formatCurrency(row.price)}</td>
                <td className="px-4 py-2.5 text-right tabular-nums text-success">{row.margin}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between border-t border-line bg-surface-2 px-4 py-3">
        <span className="text-[12.5px] text-muted">合计（标准版）</span>
        <span className="text-[17px] font-semibold tabular-nums text-ink">{formatCurrency(6440)}</span>
      </div>
    </div>
  );
}

export function MockQuotation() {
  return (
    <div className="overflow-hidden rounded-[16px] border border-line bg-surface">
      <div className="flex items-start justify-between border-b-2 border-accent px-5 py-4">
        <div>
          <p className="text-[15px] font-semibold text-ink">星辰广告制作</p>
          <p className="mt-0.5 text-[11.5px] text-faint">杭州市余杭区文一西路 1234 号</p>
        </div>
        <div className="text-right text-[11.5px] text-muted">
          <p className="text-[13px] font-semibold text-ink">Q-20260915-0001</p>
          <p>有效期至 2026-09-30</p>
        </div>
      </div>
      <div className="px-5 py-4">
        <div className="grid gap-4 sm:grid-cols-3">
          <Info label="客户" value="XX餐饮（万达店）" />
          <Info label="项目" value="XX餐饮门头制作" />
          <Info label="联系人" value="张老板 13800000000" />
        </div>
        <div className="mt-5 space-y-2.5">
          <QuotationLine name="铝塑板门头" spec="10m × 1.55m" amount={4500} />
          <QuotationLine name="发光字" spec="12 个" amount={1140} />
          <QuotationLine name="安装" spec="含现场安装" amount={800} />
        </div>
        <div className="mt-5 flex items-center justify-between border-t-2 border-ink pt-3">
          <span className="text-[13px] font-medium text-ink">合计</span>
          <span className="text-[20px] font-semibold tabular-nums text-ink">{formatCurrency(6440)}</span>
        </div>
        <div className="mt-4 grid gap-2 sm:grid-cols-3">
          {[
            { name: "经济版", value: 6280 },
            { name: "标准版", value: 6440 },
            { name: "高级版", value: 7040 },
          ].map((tier) => (
            <div
              key={tier.name}
              className={cn(
                "rounded-xl border px-3 py-2",
                tier.name === "标准版" ? "border-accent bg-accent-soft/50" : "border-line",
              )}
            >
              <p className="text-[11.5px] text-muted">{tier.name}</p>
              <p className="mt-0.5 text-[15px] font-semibold tabular-nums text-ink">
                ¥{tier.value.toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10.5px] uppercase tracking-wider text-faint">{label}</p>
      <p className="mt-0.5 text-[13px] font-medium text-ink">{value}</p>
    </div>
  );
}

function QuotationLine({ name, spec, amount }: { name: string; spec: string; amount: number }) {
  return (
    <div className="flex items-center justify-between border-b border-line/60 pb-2">
      <div>
        <p className="text-[13px] font-medium text-ink">{name}</p>
        <p className="text-[11.5px] text-faint">{spec}</p>
      </div>
      <span className="text-[13px] tabular-nums text-ink-soft">{formatCurrency(amount)}</span>
    </div>
  );
}

export function MockDashboard() {
  const bars = [38, 52, 44, 66, 58, 72, 61, 84, 70, 92, 78, 96, 88, 100];
  return (
    <div className="overflow-hidden rounded-[20px] border border-line bg-surface p-5 shadow-[var(--shadow-card)]">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[15px] font-semibold text-ink">早上好，张老板</p>
          <p className="mt-0.5 text-[12px] text-muted">今日有 8 个客户需要跟进</p>
        </div>
        <Badge tone="success">AI 额度充足</Badge>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-4">
        {[
          { label: "今日报价", value: "6", unit: "份" },
          { label: "待跟进", value: "8", unit: "个" },
          { label: "本月报价", value: "36.8", unit: "万" },
          { label: "本月成交", value: "12.4", unit: "万" },
        ].map((item) => (
          <div key={item.label} className="rounded-[14px] border border-line bg-surface-2 px-3.5 py-3">
            <p className="text-[11.5px] text-muted">{item.label}</p>
            <p className="mt-1 text-[20px] font-semibold tabular-nums leading-none text-ink">
              {item.value}
              <span className="ml-1 text-[11.5px] font-normal text-faint">{item.unit}</span>
            </p>
          </div>
        ))}
      </div>

      <div className="mt-4 rounded-[14px] border border-line p-4">
        <div className="flex items-center justify-between">
          <span className="text-[13px] font-medium text-ink">报价金额趋势</span>
          <span className="flex items-center gap-3 text-[11.5px] text-muted">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-accent" />
              报价
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-success" />
              成交
            </span>
          </span>
        </div>
        <div className="mt-4 flex h-28 items-end gap-1.5">
          {bars.map((bar, index) => (
            <div key={index} className="flex flex-1 flex-col justify-end gap-1">
              <div
                className="rounded-t-[3px] bg-accent/85"
                style={{ height: `${bar * 0.6}%`, animation: `fade-up 0.6s ${index * 0.03}s both` }}
              />
              <div className="rounded-t-[3px] bg-success/70" style={{ height: `${bar * 0.3}%` }} />
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="rounded-[14px] border border-line p-4">
          <p className="text-[13px] font-medium text-ink">报价转化漏斗</p>
          <div className="mt-3 space-y-2.5">
            {[
              { stage: "报价", value: "128", width: "100%" },
              { stage: "查看", value: "86", width: "72%" },
              { stage: "跟进", value: "52", width: "48%" },
              { stage: "成交", value: "23", width: "30%" },
            ].map((item) => (
              <div key={item.stage} className="flex items-center gap-2.5">
                <span className="w-9 text-[11.5px] text-muted">{item.stage}</span>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-line/60">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-[#7c74ff] to-[#635BFF]"
                    style={{ width: item.width }}
                  />
                </div>
                <span className="w-7 text-right text-[11.5px] tabular-nums text-ink-soft">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-[14px] border border-line p-4">
          <p className="text-[13px] font-medium text-ink">今日待跟进</p>
          <div className="mt-3 space-y-2.5">
            {[
              { name: "XX餐饮（万达店）", tag: "高意向" },
              { name: "XX地产营销中心", tag: "已报价" },
              { name: "XX酒店", tag: "沟通中" },
            ].map((item) => (
              <div key={item.name} className="flex items-center justify-between text-[12.5px]">
                <span className="truncate text-ink-soft">{item.name}</span>
                <Badge tone="accent">{item.tag}</Badge>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

