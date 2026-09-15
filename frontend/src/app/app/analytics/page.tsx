"use client";
import { BarChart3, TrendingUp } from "lucide-react";
import * as React from "react";
import { BarList, FunnelChart } from "@/components/app/charts";
import { PageHeader } from "@/components/app/page-header";
import { StatCard } from "@/components/app/stat-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, PageLoading } from "@/components/ui/states";
import { Tabs } from "@/components/ui/tabs";
import { Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { useApiData } from "@/hooks/use-api";
import { companyApi } from "@/lib/api";
import { formatAmount, formatCurrency, formatPercent } from "@/lib/utils";
const PERIODS = [
  { value: "day", label: "今日" },
  { value: "week", label: "本周" },
  { value: "month", label: "本月" },
];
export default function AnalyticsPage() {
  const [period, setPeriod] = React.useState<"day" | "week" | "month">("month");
  const analytics = useApiData(() => companyApi.analytics(period), [period]);
  const dashboard = useApiData(() => companyApi.dashboard(), []);
  if (analytics.loading) return <PageLoading label="正在统计经营数据…" />;
  if (analytics.error || !analytics.data) {
    return <ErrorState message={analytics.error ?? "统计加载失败"} onRetry={analytics.reload} />;
  }
  const data = analytics.data;
  return (
    <div>
      <PageHeader
        title="数据"
        description="报价、成交、利润率与客户转化"
        actions={<Tabs tabs={PERIODS} value={period} onChange={(value) => setPeriod(value as "day" | "week" | "month")} />}
      />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="报价数量" value={String(data.quote_count)} unit="份" />
        <StatCard label="报价金额" value={formatAmount(data.quote_amount)} unit="元" tone="accent" />
        <StatCard label="成交金额" value={formatAmount(data.won_amount)} unit="元" tone="success" />
        <StatCard label="成交率" value={formatPercent(data.conversion_rate)} hint={data.won_count + " 份成交"} />
      </div>
      <div className="mt-5 grid gap-4 xl:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>平均指标</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Metric label="平均报价金额" value={formatCurrency(data.average_quote_amount)} />
            <Metric label="平均毛利率" value={formatPercent(data.average_margin)} />
            <Metric label="跟进记录" value={data.followup_count + " 条"} />
            <Metric label="新增客户" value={data.new_customers + " 个"} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>按分类统计</CardTitle>
            <BarChart3 className="h-4 w-4 text-faint" />
          </CardHeader>
          <CardContent>
            {data.by_category.length ? (
              <BarList data={data.by_category.map((item) => ({ label: item.category, value: item.amount }))} />
            ) : (
              <p className="py-6 text-center text-[13px] text-faint">该时间段暂无报价数据</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>报价转化漏斗</CardTitle>
            <TrendingUp className="h-4 w-4 text-faint" />
          </CardHeader>
          <CardContent>
            <FunnelChart data={dashboard.data?.funnel ?? []} />
          </CardContent>
        </Card>
      </div>
      <Card className="mt-4">
        <CardHeader>
          <CardTitle>报价状态分布</CardTitle>
        </CardHeader>
        <CardContent className="px-0 pb-0">
          <Table>
            <THead>
              <Th>状态</Th>
              <Th className="text-right">数量</Th>
              <Th className="text-right">占比</Th>
            </THead>
            <TBody>
              {data.status_breakdown.map((item) => {
                const total = data.status_breakdown.reduce((sum, entry) => sum + entry.count, 0) || 1;
                return (
                  <Tr key={item.status}>
                    <Td className="font-medium text-ink">{item.label}</Td>
                    <Td className="text-right tabular-nums">{item.count}</Td>
                    <Td className="text-right tabular-nums text-muted">{formatPercent(item.count / total)}</Td>
                  </Tr>
                );
              })}
            </TBody>
          </Table>
        </CardContent>
      </Card>
      <p className="mt-4 text-[12px] text-faint">
        统计口径：按报价创建时间统计。数据实时来自数据库，非模拟数据。
      </p>
    </div>
  );
}
function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-line/70 pb-2.5 last:border-0 last:pb-0">
      <span className="text-[13px] text-muted">{label}</span>
      <span className="text-[14px] font-medium tabular-nums text-ink">{value}</span>
    </div>
  );
}

