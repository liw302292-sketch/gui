"use client";
import { Activity, Cpu, Wallet } from "lucide-react";
import * as React from "react";
import { BarList } from "@/components/app/charts";
import { PageHeader } from "@/components/app/page-header";
import { StatCard } from "@/components/app/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/states";
import { Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { Tabs } from "@/components/ui/tabs";
import { useApiData } from "@/hooks/use-api";
import { adminApi } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
const RANGES = [
  { value: "7", label: "近 7 天" },
  { value: "30", label: "近 30 天" },
  { value: "90", label: "近 90 天" },
];
export default function AdminAiPage() {
  const [range, setRange] = React.useState("30");
  const [status, setStatus] = React.useState("");
  const usage = useApiData(() => adminApi.aiUsage(Number(range)), [range]);
  const tasks = useApiData(() => adminApi.aiTasks(status || undefined), [status]);
  return (
    <div>
      <PageHeader
        title="AI 使用与成本"
        description="按企业、按模型、按任务统计调用量与预估成本"
        actions={<Tabs tabs={RANGES} value={range} onChange={setRange} />}
      />
      {usage.loading ? (
        <SkeletonRows rows={3} />
      ) : usage.error || !usage.data ? (
        <ErrorState message={usage.error ?? "加载失败"} onRetry={usage.reload} />
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="总调用量" value={String(usage.data.total_calls)} unit="次" icon={<Activity className="h-4 w-4" />} />
            <StatCard label="今日调用" value={String(usage.data.today_calls)} unit="次" />
            <StatCard label="预估总成本" value={formatCurrency(usage.data.total_cost)} tone="accent" icon={<Wallet className="h-4 w-4" />} />
            <StatCard label="今日成本" value={formatCurrency(usage.data.today_cost)} />
          </div>
          <div className="mt-5 grid gap-4 xl:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle>按模型</CardTitle>
                <Cpu className="h-4 w-4 text-faint" />
              </CardHeader>
              <CardContent>
                {usage.data.by_model.length ? (
                  <BarList
                    data={usage.data.by_model.map((item) => ({ label: item.model, value: item.calls }))}
                    formatter={(value) => value + " 次"}
                  />
                ) : (
                  <p className="py-6 text-center text-[13px] text-faint">暂无数据</p>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>按企业</CardTitle>
              </CardHeader>
              <CardContent>
                {usage.data.by_company.length ? (
                  <BarList
                    data={usage.data.by_company.map((item) => ({ label: item.company_name, value: item.calls }))}
                    formatter={(value) => value + " 次"}
                  />
                ) : (
                  <p className="py-6 text-center text-[13px] text-faint">暂无数据</p>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>成本明细</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2.5">
                {usage.data.by_model.map((item) => (
                  <div key={item.model} className="flex items-center justify-between border-b border-line/70 pb-2 last:border-0">
                    <span className="truncate font-mono text-[11.5px] text-muted">{item.model}</span>
                    <span className="tabular-nums text-[13px] font-medium text-ink">{formatCurrency(item.cost)}</span>
                  </div>
                ))}
                {usage.data.by_company.map((item) => (
                  <div key={item.company_id} className="flex items-center justify-between text-[12px] text-faint">
                    <span className="truncate">{item.company_name}</span>
                    <span className="tabular-nums">{formatCurrency(item.cost)}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </>
      )}
      <Card className="mt-5">
        <CardHeader>
          <CardTitle>AI 任务明细</CardTitle>
          <Tabs
            tabs={[
              { value: "", label: "全部" },
              { value: "success", label: "成功" },
              { value: "failed", label: "失败" },
            ]}
            value={status}
            onChange={setStatus}
          />
        </CardHeader>
        <CardContent className="px-0 pb-0">
          {tasks.loading ? (
            <SkeletonRows rows={5} className="px-5" />
          ) : !tasks.data?.length ? (
            <EmptyState icon={<Activity className="h-5 w-5" />} title="暂无任务记录" className="m-5" />
          ) : (
            <Table>
              <THead>
                <Th>任务</Th>
                <Th>企业</Th>
                <Th>模型</Th>
                <Th>模式</Th>
                <Th className="text-right">Token</Th>
                <Th className="text-right">成本</Th>
                <Th className="text-right">耗时</Th>
                <Th>状态</Th>
                <Th>时间</Th>
              </THead>
              <TBody>
                {tasks.data.map((task) => (
                  <Tr key={task.id}>
                    <Td className="font-medium text-ink">{task.task_type}</Td>
                    <Td className="text-muted">#{task.company_id}</Td>
                    <Td className="font-mono text-[11.5px] text-muted">{task.model}</Td>
                    <Td>
                      <Badge tone={task.mode === "real" ? "success" : "accent"}>{task.mode}</Badge>
                    </Td>
                    <Td className="text-right tabular-nums text-muted">
                      {task.input_tokens} / {task.output_tokens}
                    </Td>
                    <Td className="text-right tabular-nums text-muted">{formatCurrency(task.estimated_cost)}</Td>
                    <Td className="text-right tabular-nums text-muted">{task.latency_ms} ms</Td>
                    <Td>
                      <Badge tone={task.status === "success" ? "success" : "danger"}>{task.status}</Badge>
                    </Td>
                    <Td className="text-[12px] text-faint">{formatDate(task.created_at, true)}</Td>
                  </Tr>
                ))}
              </TBody>
            </Table>
          )}
        </CardContent>
      </Card>
      <p className="mt-4 text-[12px] text-faint">
        DeepSeek 采用峰谷计价，模型单价通过环境变量配置，系统只做调用量与成本统计，不把价格写死在前端。
      </p>
      <div className="mt-2">
        <Button variant="ghost" size="sm" onClick={() => { tasks.reload(); usage.reload(); }}>
          刷新数据
        </Button>
      </div>
    </div>
  );
}

