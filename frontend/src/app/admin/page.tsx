"use client";
import { Activity, Building2, CreditCard, FileText, Users, Wallet } from "lucide-react";
import * as React from "react";
import { PageHeader } from "@/components/app/page-header";
import { StatCard } from "@/components/app/stat-card";
import { AreaTrendChart, BarList } from "@/components/app/charts";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, PageLoading } from "@/components/ui/states";
import { useApiData } from "@/hooks/use-api";
import { adminApi } from "@/lib/api";
import { formatAmount, formatCurrency } from "@/lib/utils";
export default function AdminDashboardPage() {
  const { data, loading, error, reload } = useApiData(() => adminApi.dashboard(), []);
  if (loading) return <PageLoading label="正在统计平台数据…" />;
  if (error || !data) return <ErrorState message={error ?? "加载失败"} onRetry={reload} />;
  const stats = data.stats;
  return (
    <div>
      <PageHeader
        title="平台总览"
        description="企业、用户、报价、AI 与收入"
        actions={
          <div className="flex items-center gap-2">
            <Badge tone={data.system.ai_mode === "real" ? "success" : "accent"}>
              AI：{data.system.ai_mode === "real" ? "真实模式" : "Mock 模式"}
            </Badge>
            <Badge tone="neutral">环境：{data.system.env}</Badge>
            <Badge tone="neutral">数据库：{data.system.database}</Badge>
            <Badge tone={data.system.redis ? "success" : "warning"}>Redis：{data.system.redis ? "已连接" : "未连接"}</Badge>
          </div>
        }
      />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="企业总数" value={String(stats.companies_total ?? 0)} unit="家" icon={<Building2 className="h-4 w-4" />} />
        <StatCard label="活跃企业" value={String(stats.companies_active ?? 0)} unit="家" tone="success" />
        <StatCard label="注册用户" value={String(stats.users_total ?? 0)} unit="人" icon={<Users className="h-4 w-4" />} />
        <StatCard label="付费企业" value={String(stats.paid_companies ?? 0)} unit="家" tone="accent" icon={<CreditCard className="h-4 w-4" />} />
      </div>
      <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="今日新注册" value={String(stats.new_users_today ?? 0)} unit="人" />
        <StatCard label="今日报价" value={String(stats.quotes_today ?? 0)} unit="份" icon={<FileText className="h-4 w-4" />} />
        <StatCard label="今日 AI 请求" value={String(data.ai.today_calls)} unit="次" icon={<Activity className="h-4 w-4" />} />
        <StatCard
          label="本月收入"
          value={formatAmount(stats.month_revenue ?? 0)}
          unit="元"
          tone="success"
          icon={<Wallet className="h-4 w-4" />}
        />
      </div>
      <div className="mt-5 grid gap-4 xl:grid-cols-[1.6fr_1fr]">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>平台趋势</CardTitle>
              <p className="mt-1 text-[12.5px] text-muted">近 14 天新增企业与报价</p>
            </div>
            <div className="flex items-center gap-3 text-[12px] text-muted">
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-accent" />
                报价数
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-success" />
                AI 调用
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <AreaTrendChart
              data={data.trend.map((point) => ({ label: point.date, value: point.quotes, secondary: point.ai_calls }))}
              showSecondary
              valueFormatter={(value) => String(Math.round(value))}
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>AI 成本概览</CardTitle>
            <Badge tone="neutral">近 30 天</Badge>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <p className="text-[12px] text-muted">总调用</p>
                <p className="mt-1 text-[18px] font-semibold text-ink">{data.ai.total_calls}</p>
              </div>
              <div className="rounded-xl border border-line bg-surface-2 p-3">
                <p className="text-[12px] text-muted">预估成本</p>
                <p className="mt-1 text-[18px] font-semibold text-ink">{formatCurrency(data.ai.total_cost)}</p>
              </div>
            </div>
            <div>
              <p className="text-[12.5px] font-medium text-ink">按模型</p>
              <div className="mt-2.5">
                <BarList
                  data={data.ai.by_model.map((item) => ({ label: item.model, value: item.calls }))}
                  formatter={(value) => value + " 次"}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>按企业 AI 用量</CardTitle>
          </CardHeader>
          <CardContent>
            {data.ai.by_company.length ? (
              <BarList
                data={data.ai.by_company.map((item) => ({ label: item.company_name, value: item.calls }))}
                formatter={(value) => value + " 次"}
              />
            ) : (
              <p className="py-6 text-center text-[13px] text-faint">暂无数据</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>按任务类型</CardTitle>
          </CardHeader>
          <CardContent>
            {data.ai.by_task.length ? (
              <BarList
                data={data.ai.by_task.map((item) => ({ label: taskLabel(item.task_type), value: item.calls }))}
                formatter={(value) => value + " 次"}
              />
            ) : (
              <p className="py-6 text-center text-[13px] text-faint">暂无数据</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
function taskLabel(type: string) {
  const map: Record<string, string> = {
    requirement_extract: "需求识别",
    missing_fields: "缺失补问",
    reply_draft: "回复文案",
    price_explain: "报价解释",
    price_suggestion: "区间建议",
  };
  return map[type] ?? type;
}

