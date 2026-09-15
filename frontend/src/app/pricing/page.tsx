"use client";

import { BadgeCheck, Check, HelpCircle, Minus } from "lucide-react";
import Link from "next/link";
import * as React from "react";

import { SiteFooter, SiteHeader } from "@/components/marketing/site-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SkeletonRows } from "@/components/ui/states";
import { billingApi } from "@/lib/api";
import type { Plan } from "@/lib/types";
import { cn } from "@/lib/utils";

const FEATURE_ROWS: { key: string; label: string }[] = [
  { key: "quotes", label: "报价单与报价闭环" },
  { key: "ai", label: "AI 识别与 AI 助手" },
  { key: "analytics", label: "数据统计与转化漏斗" },
  { key: "branding", label: "企业品牌与自定义报价单" },
  { key: "members", label: "多人协作账号" },
  { key: "api", label: "开放 API" },
  { key: "private_deploy", label: "私有部署" },
];

const FAQ: { q: string; a: string }[] = [
  {
    q: "没有 DeepSeek API Key 能用吗？",
    a: "可以。系统检测不到 Key 时会自动进入 Mock 模式，用确定性演示数据跑通完整闭环；配上 Key 后自动切换真实 AI，无需改代码。",
  },
  {
    q: "AI 会不会自己改我的价格？",
    a: "不会。AI 只负责识别需求与生成文案，最终价格一律由后端规则引擎按你的价格库计算，AI 甚至连成本字段都看不到。",
  },
  {
    q: "我现有的 Excel 价格表怎么迁进来？",
    a: "在「产品与价格」页面直接导入 .xlsx / .csv，系统会按列名自动识别分类、产品、单位、成本、报价、损耗率与利润率。",
  },
  {
    q: "能部署到我们自己的服务器吗？",
    a: "可以。项目提供 Docker Compose 一键部署（前端 / 后端 / PostgreSQL / Redis / Nginx），企业版还支持替换成自己的域名与对象存储。",
  },
  {
    q: "报价单会不会暴露我的成本？",
    a: "不会。公开报价页与 PDF 只输出产品、规格、数量、单价与总价，成本、利润、毛利率只在企业内部界面可见。",
  },
];

export default function PricingPage() {
  const [plans, setPlans] = React.useState<Plan[]>([]);
  const [labels, setLabels] = React.useState<Record<string, string>>({});
  const [loading, setLoading] = React.useState(true);
  const [openFaq, setOpenFaq] = React.useState<number | null>(0);

  React.useEffect(() => {
    billingApi
      .plans()
      .then((data) => {
        setPlans(data.items);
        setLabels(data.feature_labels);
      })
      .catch(() => setPlans([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="bg-background">
      <SiteHeader />

      <section className="border-b border-line bg-surface py-16">
        <div className="container-page text-center">
          <Badge tone="accent">价格</Badge>
          <h1 className="mt-4 text-[34px] font-semibold leading-tight tracking-tight text-ink sm:text-[40px]">
            按公司规模付费，不按人头抽成
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-[15.5px] leading-relaxed text-muted">
            免费版就能跑完「识别 → 计算 → 出单 → 跟进」全流程。用得顺手了再升级，随时可以换。
          </p>
        </div>
      </section>

      <section className="py-14">
        <div className="container-page">
          {loading ? (
            <div className="grid gap-5 lg:grid-cols-3">
              <SkeletonRows rows={1} className="h-72" />
              <SkeletonRows rows={1} className="h-72" />
              <SkeletonRows rows={1} className="h-72" />
            </div>
          ) : (
            <div className="grid gap-5 lg:grid-cols-3">
              {plans.map((plan) => (
                <PriceCard key={plan.id} plan={plan} />
              ))}
            </div>
          )}

          <div className="mt-5 rounded-[18px] border border-dashed border-line-strong bg-surface p-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h3 className="text-[16px] font-semibold text-ink">私有部署 / 源码授权</h3>
                <p className="mt-1.5 text-[13px] text-muted">
                  部署到你自己的服务器，数据完全自持。含 Docker Compose、Nginx 配置与部署说明。
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[15px] font-semibold text-ink">联系客服报价</span>
                <Link href="/register">
                  <Button variant="secondary">先免费试用</Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-y border-line bg-surface py-14">
        <div className="container-page">
          <h2 className="text-[22px] font-semibold tracking-tight text-ink">功能对比</h2>
          <div className="mt-6 overflow-x-auto">
            <table className="w-full min-w-[640px] text-[13.5px]">
              <thead>
                <tr className="border-b border-line text-left text-[12.5px] text-muted">
                  <th className="py-3 pr-4 font-medium">功能</th>
                  {plans.map((plan) => (
                    <th key={plan.id} className="px-4 py-3 text-center font-medium">
                      {plan.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {FEATURE_ROWS.map((row) => (
                  <tr key={row.key} className="border-b border-line/70">
                    <td className="py-3.5 pr-4 text-ink-soft">{row.label}</td>
                    {plans.map((plan) => (
                      <td key={plan.id} className="px-4 py-3.5 text-center">
                        {plan.features.includes(row.key) ? (
                          <Check className="mx-auto h-4 w-4 text-success" />
                        ) : (
                          <Minus className="mx-auto h-4 w-4 text-faint" />
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
                <tr className="border-b border-line/70">
                  <td className="py-3.5 pr-4 text-ink-soft">每月报价数量</td>
                  {plans.map((plan) => (
                    <td key={plan.id} className="px-4 py-3.5 text-center text-ink">
                      {plan.max_quotes === 0 ? "不限" : `${plan.max_quotes} 份`}
                    </td>
                  ))}
                </tr>
                <tr className="border-b border-line/70">
                  <td className="py-3.5 pr-4 text-ink-soft">每月 AI 调用额度</td>
                  {plans.map((plan) => (
                    <td key={plan.id} className="px-4 py-3.5 text-center text-ink">
                      {plan.ai_quota.toLocaleString()} 次
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-3.5 pr-4 text-ink-soft">成员账号</td>
                  {plans.map((plan) => (
                    <td key={plan.id} className="px-4 py-3.5 text-center text-ink">
                      {plan.max_users} 个
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
          {Object.keys(labels).length ? (
            <p className="mt-4 text-[12px] text-faint">
              套餐配置存放在数据库中，管理员可随时新增或调整，不需要改代码。
            </p>
          ) : null}
        </div>
      </section>

      <section className="py-14">
        <div className="container-page">
          <h2 className="text-[22px] font-semibold tracking-tight text-ink">常见问题</h2>
          <div className="mt-6 space-y-3">
            {FAQ.map((item, index) => {
              const open = openFaq === index;
              return (
                <div key={item.q} className="overflow-hidden rounded-[16px] border border-line bg-surface">
                  <button
                    type="button"
                    onClick={() => setOpenFaq(open ? null : index)}
                    className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
                  >
                    <span className="flex items-center gap-2.5 text-[14px] font-medium text-ink">
                      <HelpCircle className="h-4 w-4 shrink-0 text-accent" />
                      {item.q}
                    </span>
                    <span className={cn("text-faint transition-transform", open && "rotate-45")}>+</span>
                  </button>
                  {open ? (
                    <p className="border-t border-line px-5 py-4 text-[13.5px] leading-relaxed text-muted">{item.a}</p>
                  ) : null}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="border-t border-line bg-surface py-14">
        <div className="container-page flex flex-wrap items-center justify-between gap-6">
          <div>
            <h2 className="text-[22px] font-semibold tracking-tight text-ink">先用免费版做一份真实报价</h2>
            <p className="mt-2 text-[14px] text-muted">不需要绑卡，注册后立刻有完整价格库与演示数据。</p>
          </div>
          <Link href="/register">
            <Button size="lg">免费开始报价</Button>
          </Link>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}

function PriceCard({ plan }: { plan: Plan }) {
  const highlight = plan.code === "pro";
  const cycleText = plan.billing_cycle === "forever" ? "永久免费" : plan.billing_cycle === "year" ? "/ 年" : "/ 月";
  return (
    <div
      className={cn(
        "relative flex flex-col rounded-[18px] border bg-surface p-6",
        highlight ? "border-accent/40 shadow-[var(--shadow-card)]" : "border-line",
      )}
    >
      {highlight ? (
        <span className="absolute -top-3 left-6">
          <Badge tone="dark">最受欢迎</Badge>
        </span>
      ) : null}
      <h3 className="text-[16px] font-semibold text-ink">{plan.name}</h3>
      <p className="mt-1 text-[12.5px] text-muted">{plan.tagline ?? plan.description}</p>
      <div className="mt-5 flex items-end gap-1.5">
        <span className="text-[14px] text-muted">¥</span>
        <span className="text-[34px] font-semibold leading-none tracking-tight text-ink">{plan.price}</span>
        <span className="text-[13px] text-muted">{cycleText}</span>
      </div>
      <ul className="mt-6 flex-1 space-y-2.5 border-t border-line pt-5">
        <li className="flex items-center gap-2 text-[13px] text-ink-soft">
          <BadgeCheck className="h-4 w-4 shrink-0 text-accent" />
          {plan.max_quotes === 0 ? "不限报价数量" : `每月 ${plan.max_quotes} 份报价`}
        </li>
        <li className="flex items-center gap-2 text-[13px] text-ink-soft">
          <BadgeCheck className="h-4 w-4 shrink-0 text-accent" />
          每月 {plan.ai_quota.toLocaleString()} 次 AI 识别
        </li>
        <li className="flex items-center gap-2 text-[13px] text-ink-soft">
          <BadgeCheck className="h-4 w-4 shrink-0 text-accent" />
          {plan.max_users} 个成员账号
        </li>
        {plan.description ? (
          <li className="pt-1 text-[12.5px] leading-relaxed text-muted">{plan.description}</li>
        ) : null}
      </ul>
      <Link href="/register" className="mt-6">
        <Button variant={highlight ? "primary" : "secondary"} className="w-full">
          {plan.price > 0 ? `开始${plan.name}` : "免费开始"}
        </Button>
      </Link>
    </div>
  );
}

