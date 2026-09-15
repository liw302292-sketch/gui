"use client";

import {
  ArrowRight,
  Bell,
  FileText,
  Flame,
  Handshake,
  Plus,
  Sparkles,
  TrendingUp,
  UserPlus,
} from "lucide-react";
import Link from "next/link";
import * as React from "react";

import { AreaTrendChart, FunnelChart } from "@/components/app/charts";
import { PageHeader } from "@/components/app/page-header";
import { StatCard } from "@/components/app/stat-card";
import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, PageLoading } from "@/components/ui/states";
import { useApiData } from "@/hooks/use-api";
import { companyApi } from "@/lib/api";
import { formatAmount, formatCurrency, formatPercent, relativeTime } from "@/lib/utils";

export default function DashboardPage() {
  const { data, loading, error, reload } = useApiData(() => companyApi.dashboard(), []);

  if (loading) return <PageLoading label="正在加载工作台…" />;
  if (error || !data) return <ErrorState message={error ?? "加载失败"} onRetry={reload} />;

  const { stats } = data;

  return (
    <div>
      <PageHeader
        title={data.greeting}
        description={data.followup_hint}
        actions={
          <>
            <Link href="/app/quotes/new">
              <Button>
                <Plus className="h-4 w-4" />
                新建报价
              </Button>
            </Link>
          </>
        }
      />

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="今日报价"
          value={String(stats.today_quotes)}
          unit="份"
          hint="今天新建的报价单"
          icon={<FileText className="h-4 w-4" />}
        />
        <StatCard
          label="待跟进"
          value={String(stats.pending_followups)}
          unit="个"
          hint="今天及之前需要联系"
          tone={stats.pending_followups > 0 ? "warning" : "default"}
          icon={<Bell className="h-4 w-4" />}
        />
        <StatCard
          label="本月报价金额"
          value={formatAmount(stats.month_quote_amount)}
          unit="元"
          hint={`共 ${stats.total_quotes} 份历史报价`}
          icon={<TrendingUp className="h-4 w-4" />}
          tone="accent"
        />
        <StatCard
          label="本月成交金额"
          value={formatAmount(stats.month_deal_amount)}
          unit="元"
          hint={`成交率 ${formatPercent(stats.conversion_rate)}`}
          icon={<Handshake className="h-4 w-4" />}
          tone="success"
        />
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[1.6fr_1fr]">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>报价与成交趋势</CardTitle>
              <p className="mt-1 text-[12.5px] text-muted">近 14 天</p>
            </div>
            <div className="flex items-center gap-3 text-[12px] text-muted">
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-accent" />
                报价金额
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-success" />
                成交金额
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <AreaTrendChart
              data={data.quote_trend.map((point, index) => ({
                label: point.date,
                value: point.amount,
                secondary: data.deal_trend[index]?.amount ?? 0,
              }))}
              showSecondary
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div>
              <CardTitle>报价转化漏斗</CardTitle>
              <p className="mt-1 text-[12.5px] text-muted">报价 → 查看 → 跟进 → 成交</p>
            </div>
          </CardHeader>
          <CardContent>
            <FunnelChart data={data.funnel} />
            <div className="mt-5 rounded-xl border border-line bg-surface-2 px-3.5 py-3">
              <div className="flex items-center justify-between text-[12.5px]">
                <span className="text-muted">本月 AI 调用</span>
                <span className="font-medium text-ink">
                  {data.ai_usage.calls} / {data.ai_usage.quota || "不限"}
                </span>
              </div>
              <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-line/70">
                <div
                  className="h-full rounded-full bg-accent"
                  style={{ width: `${Math.min(data.ai_usage.usage_ratio * 100, 100)}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>今日待跟进</CardTitle>
            <Link href="/app/followups" className="text-[12.5px] text-accent hover:underline">
              全部
            </Link>
          </CardHeader>
          <CardContent>
            {data.today_followups.length ? (
              <div className="space-y-1">
                {data.today_followups.map((item) => (
                  <Link
                    key={item.id}
                    href={`/app/customers/${item.id}`}
                    className="flex items-center justify-between gap-3 rounded-xl px-3 py-2.5 transition-colors hover:bg-surface-2"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-[13.5px] font-medium text-ink">{item.name}</p>
                      <p className="mt-0.5 text-[12px] text-faint">
                        {item.contact_name ?? "—"} · {item.phone ?? "无电话"}
                      </p>
                    </div>
                    <StatusBadge status={item.status} />
                  </Link>
                ))}
              </div>
            ) : (
              <EmptyState
                icon={<Handshake className="h-5 w-5" />}
                title="今天没有需要跟进的客户"
                description="所有报价都跟完了，可以再新建一份报价。"
                action={
                  <Link href="/app/quotes/new">
                    <Button size="sm">
                      <Plus className="h-3.5 w-3.5" />
                      新建报价
                    </Button>
                  </Link>
                }
                className="py-10"
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>最近报价</CardTitle>
            <Link href="/app/quotes" className="text-[12.5px] text-accent hover:underline">
              全部
            </Link>
          </CardHeader>
          <CardContent>
            {data.recent_quotes.length ? (
              <div className="space-y-1">
                {data.recent_quotes.map((quote) => (
                  <Link
                    key={quote.id}
                    href={`/app/quotes/${quote.id}`}
                    className="flex items-center justify-between gap-3 rounded-xl px-3 py-2.5 transition-colors hover:bg-surface-2"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-[13.5px] font-medium text-ink">{quote.project_name}</p>
                      <p className="mt-0.5 text-[12px] text-faint">
                        {quote.quote_no} · {relativeTime(quote.created_at)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-[13.5px] font-medium tabular-nums text-ink">
                        {formatCurrency(quote.total_amount)}
                      </p>
                      <StatusBadge status={quote.status} label={quote.status_label} />
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <EmptyState
                title="暂无报价"
                description="创建第一份报价，体验 30 秒出报价。"
                action={
                  <Link href="/app/quotes/new">
                    <Button size="sm">新建报价</Button>
                  </Link>
                }
                className="py-10"
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>高金额报价</CardTitle>
            <span className="text-[12.5px] text-faint">优先跟进</span>
          </CardHeader>
          <CardContent>
            {data.high_value_quotes.length ? (
              <div className="space-y-1">
                {data.high_value_quotes.map((quote) => (
                  <Link
                    key={quote.id}
                    href={`/app/quotes/${quote.id}`}
                    className="flex items-center justify-between gap-3 rounded-xl px-3 py-2.5 transition-colors hover:bg-surface-2"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-[13.5px] font-medium text-ink">{quote.project_name}</p>
                      <p className="mt-0.5 truncate text-[12px] text-faint">{quote.customer_name ?? "未指定客户"}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Flame className="h-3.5 w-3.5 text-warning" />
                      <span className="text-[13.5px] font-medium tabular-nums text-ink">
                        {formatCurrency(quote.total_amount)}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <EmptyState title="暂无高金额报价" description="当报价金额累积后，这里会显示需要重点跟进的项目。" className="py-10" />
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="mt-5">
        <CardContent className="flex flex-wrap items-center justify-between gap-4 pt-5">
          <div className="flex items-start gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-soft text-accent">
              <Sparkles className="h-4 w-4" />
            </span>
            <div>
              <p className="text-[14px] font-medium text-ink">客户发来一段需求？直接丢给 AI</p>
              <p className="mt-1 text-[12.5px] text-muted">
                上传微信截图或粘贴文字，AI 自动提取产品、尺寸、数量与缺失信息。
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Link href="/app/ai">
              <Button variant="secondary">
                <Sparkles className="h-4 w-4" />
                打开 AI 助手
              </Button>
            </Link>
            <Link href="/app/quotes/new">
              <Button>
                <Plus className="h-4 w-4" />
                新建报价
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <Link href="/app/customers" className="card flex items-center justify-between p-4 transition-transform hover:-translate-y-0.5">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-surface-2 text-ink-soft">
              <UserPlus className="h-4 w-4" />
            </span>
            <span className="text-[13.5px] font-medium text-ink">管理客户</span>
          </div>
          <ArrowRight className="h-4 w-4 text-faint" />
        </Link>
        <Link href="/app/products" className="card flex items-center justify-between p-4 transition-transform hover:-translate-y-0.5">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-surface-2 text-ink-soft">
              <FileText className="h-4 w-4" />
            </span>
            <span className="text-[13.5px] font-medium text-ink">维护价格库</span>
          </div>
          <ArrowRight className="h-4 w-4 text-faint" />
        </Link>
        <Link href="/app/analytics" className="card flex items-center justify-between p-4 transition-transform hover:-translate-y-0.5">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-surface-2 text-ink-soft">
              <TrendingUp className="h-4 w-4" />
            </span>
            <span className="text-[13.5px] font-medium text-ink">查看经营数据</span>
          </div>
          <ArrowRight className="h-4 w-4 text-faint" />
        </Link>
      </div>

      {data.company?.plan ? (
        <p className="mt-6 text-center text-[12px] text-faint">
          当前套餐：<Badge tone="accent">{data.company.plan}</Badge>
        </p>
      ) : null}
    </div>
  );
}
