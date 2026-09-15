"use client";

import { Calculator, Check, FileText, ScanLine, Sparkles } from "lucide-react";
import * as React from "react";

import { cn, formatCurrency } from "@/lib/utils";

const STEPS = [
  { key: "screenshot", label: "客户微信截图", icon: FileText },
  { key: "recognize", label: "AI 识别", icon: ScanLine },
  { key: "structure", label: "参数结构化", icon: Sparkles },
  { key: "quote", label: "生成报价单", icon: Calculator },
];

const STRUCTURED = [
  { label: "项目", value: "XX餐饮门头制作" },
  { label: "产品", value: "铝塑板门头" },
  { label: "尺寸", value: "10m × 1.55m", missing: false },
  { label: "发光字", value: "12 个", missing: false },
  { label: "安装", value: "需要安装" },
  { label: "安装地址", value: "待补充", missing: true },
];

const QUOTE_ITEMS = [
  { name: "铝塑板门头", spec: "10m × 1.55m", amount: 4500 },
  { name: "发光字", spec: "12 个", amount: 1140 },
  { name: "安装", spec: "含现场安装", amount: 800 },
];

/** Hero 右侧：真实模拟产品流程的产品动画。 */
export function HeroDemo() {
  const [step, setStep] = React.useState(0);

  React.useEffect(() => {
    const timer = window.setInterval(() => setStep((value) => (value + 1) % STEPS.length), 3200);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <div className="relative">
      <div className="absolute -inset-6 -z-10 rounded-[32px] bg-gradient-to-br from-accent/12 via-transparent to-transparent blur-2xl" />
      <div className="overflow-hidden rounded-[20px] border border-line bg-surface shadow-[var(--shadow-float)]">
        {/* 顶部步骤条 */}
        <div className="flex items-center gap-1.5 border-b border-line bg-surface-2/70 px-3 py-2.5">
          {STEPS.map((item, index) => {
            const Icon = item.icon;
            const active = index === step;
            const done = index < step;
            return (
              <button
                key={item.key}
                type="button"
                onClick={() => setStep(index)}
                className={cn(
                  "flex flex-1 items-center gap-1.5 rounded-lg px-2 py-1.5 text-[11.5px] transition-all",
                  active ? "bg-white text-ink shadow-[var(--shadow-subtle)]" : "text-faint hover:text-ink-soft",
                )}
              >
                <span
                  className={cn(
                    "flex h-5 w-5 shrink-0 items-center justify-center rounded-md",
                    active ? "bg-accent text-white" : done ? "bg-success-soft text-success" : "bg-line/70 text-faint",
                  )}
                >
                  {done ? <Check className="h-3 w-3" /> : <Icon className="h-3 w-3" />}
                </span>
                <span className="hidden truncate sm:inline">{item.label}</span>
              </button>
            );
          })}
        </div>

        <div className="relative h-[392px] bg-surface px-4 py-4">
          {/* 1. 微信截图 */}
          <div
            className={cn(
              "absolute inset-0 px-4 py-4 transition-all duration-500",
              step === 0 ? "opacity-100" : "pointer-events-none translate-y-2 opacity-0",
            )}
          >
            <div className="mx-auto h-full w-full max-w-[300px] overflow-hidden rounded-2xl border border-line bg-[#ededed] p-3">
              <div className="mb-3 flex items-center justify-between text-[11px] text-muted">
                <span>XX餐饮 · 李经理</span>
                <span>10:24</span>
              </div>
              <div className="space-y-2.5">
                <Bubble>帮我做一个10米门头，铝塑板底</Bubble>
                <Bubble>再加12个发光字，月底要安装</Bubble>
                <Bubble self>好的，我算一下给您报价</Bubble>
              </div>
              <div className="mt-4 rounded-xl border border-dashed border-line-strong bg-white/70 p-3">
                <div className="flex items-center gap-2 text-[11px] text-muted">
                  <ScanLine className="h-3.5 w-3.5 text-accent" />
                  已识别为一段真实客户需求
                </div>
              </div>
            </div>
          </div>

          {/* 2. AI 识别 */}
          <div
            className={cn(
              "absolute inset-0 px-4 py-4 transition-all duration-500",
              step === 1 ? "opacity-100" : "pointer-events-none translate-y-2 opacity-0",
            )}
          >
            <div className="mx-auto h-full w-full max-w-[320px] overflow-hidden rounded-2xl border border-line bg-[#fafaff] p-4">
              <div className="flex items-center gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent text-white">
                  <Sparkles className="h-3.5 w-3.5" />
                </span>
                <div>
                  <p className="text-[13px] font-medium text-ink">AI 正在理解客户需求</p>
                  <p className="text-[11px] text-faint">识别产品 · 提取尺寸 · 检查缺失项</p>
                </div>
              </div>
              <div className="relative mt-4 space-y-2.5">
                {["读取图片内容", "分析文字需求", "识别产品类别", "提取尺寸数量", "检查缺失信息"].map(
                  (label, index) => (
                    <div
                      key={label}
                      className="flex items-center gap-2.5 rounded-lg border border-line/70 bg-white px-3 py-2"
                      style={{ animation: `fade-up 0.5s ${index * 0.12}s both` }}
                    >
                      <span className="flex h-4 w-4 items-center justify-center rounded-full bg-success-soft">
                        <Check className="h-2.5 w-2.5 text-success" />
                      </span>
                      <span className="text-[12.5px] text-ink-soft">{label}</span>
                      <span className="ml-auto text-[11px] text-faint">{0.4 + index * 0.12}s</span>
                    </div>
                  ),
                )}
              </div>
            </div>
          </div>

          {/* 3. 参数结构化 */}
          <div
            className={cn(
              "absolute inset-0 px-4 py-4 transition-all duration-500",
              step === 2 ? "opacity-100" : "pointer-events-none translate-y-2 opacity-0",
            )}
          >
            <div className="mx-auto h-full w-full max-w-[340px] overflow-hidden rounded-2xl border border-line bg-white p-4">
              <div className="flex items-center justify-between">
                <p className="text-[13px] font-medium text-ink">识别结果（可人工修改）</p>
                <span className="rounded-full bg-accent-soft px-2 py-0.5 text-[11px] text-accent">置信度 91%</span>
              </div>
              <div className="mt-3 divide-y divide-line/70">
                {STRUCTURED.map((row) => (
                  <div key={row.label} className="flex items-center justify-between py-2">
                    <span className="text-[12.5px] text-muted">{row.label}</span>
                    <span className={cn("text-[12.5px]", row.missing ? "text-warning" : "font-medium text-ink")}>
                      {row.value}
                    </span>
                  </div>
                ))}
              </div>
              <div className="mt-3 rounded-xl border border-[#f6e0bd] bg-warning-soft px-3 py-2 text-[11.5px] text-[#8a4b00]">
                还有 3 项信息可能影响最终报价
              </div>
            </div>
          </div>

          {/* 4. 报价单 */}
          <div
            className={cn(
              "absolute inset-0 px-4 py-4 transition-all duration-500",
              step === 3 ? "opacity-100" : "pointer-events-none translate-y-2 opacity-0",
            )}
          >
            <div className="mx-auto h-full w-full max-w-[340px] overflow-hidden rounded-2xl border border-line bg-white p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-[13px] font-semibold text-ink">星辰广告制作</p>
                  <p className="text-[11px] text-faint">报价单 Q-20260915-0001</p>
                </div>
                <span className="rounded-full bg-success-soft px-2 py-0.5 text-[11px] text-success">已生成</span>
              </div>
              <div className="mt-3 space-y-2">
                {QUOTE_ITEMS.map((item) => (
                  <div key={item.name} className="flex items-center justify-between border-b border-line/60 pb-2">
                    <div>
                      <p className="text-[12.5px] font-medium text-ink">{item.name}</p>
                      <p className="text-[11px] text-faint">{item.spec}</p>
                    </div>
                    <span className="text-[12.5px] tabular-nums text-ink-soft">{formatCurrency(item.amount)}</span>
                  </div>
                ))}
              </div>
              <div className="mt-3 flex items-center justify-between rounded-xl bg-surface-2 px-3 py-2.5">
                <span className="text-[12.5px] text-muted">合计</span>
                <span className="text-[17px] font-semibold tabular-nums text-ink">{formatCurrency(6440)}</span>
              </div>
              <div className="mt-2.5 flex gap-2">
                <span className="flex-1 rounded-lg bg-ink px-3 py-2 text-center text-[11.5px] text-white">
                  生成公开链接
                </span>
                <span className="flex-1 rounded-lg border border-line px-3 py-2 text-center text-[11.5px] text-ink-soft">
                  下载 PDF
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-center gap-1.5">
        {STEPS.map((item, index) => (
          <button
            key={item.key}
            type="button"
            aria-label={`查看第 ${index + 1} 步`}
            onClick={() => setStep(index)}
            className={cn(
              "h-1.5 rounded-full transition-all",
              index === step ? "w-6 bg-accent" : "w-1.5 bg-line-strong hover:bg-faint",
            )}
          />
        ))}
      </div>
    </div>
  );
}

function Bubble({ children, self = false }: { children: React.ReactNode; self?: boolean }) {
  return (
    <div className={cn("flex", self ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[85%] rounded-2xl px-3 py-2 text-[12.5px] leading-relaxed shadow-[var(--shadow-subtle)]",
          self ? "bg-[#c6f0cf] text-[#0b4d22]" : "bg-white text-ink",
        )}
      >
        {children}
      </div>
    </div>
  );
}

