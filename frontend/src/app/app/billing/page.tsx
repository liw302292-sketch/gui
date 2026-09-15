"use client";
import { BadgeCheck, Check, CreditCard, Sparkles } from "lucide-react";
import * as React from "react";
import { PageHeader } from "@/components/app/page-header";
import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { EmptyState, ErrorState, InlineAlert, PageLoading } from "@/components/ui/states";
import { Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { toast } from "@/components/ui/toast";
import { useApiData } from "@/hooks/use-api";
import { billingApi, errorMessage } from "@/lib/api";
import { cn, formatCurrency, formatDate, formatPercent } from "@/lib/utils";
export default function BillingPage() {
  const current = useApiData(() => billingApi.current(), []);
  const plans = useApiData(() => billingApi.plans(true), []);
  const orders = useApiData(() => billingApi.orders(), []);
  const [busy, setBusy] = React.useState<string | null>(null);
  if (current.loading || plans.loading) return <PageLoading label="正在加载套餐…" />;
  if (current.error || !current.data) return <ErrorState message={current.error ?? "加载失败"} onRetry={current.reload} />;
  const plan = current.data.plan;
  const usage = current.data.ai_usage;
  async function subscribe(code: string) {
    setBusy(code);
    try {
      const order = await billingApi.createOrder(code);
      toast.success(
        order.status === "paid" ? "支付成功，套餐已生效" : "订单已创建，请完成支付",
      );
      current.reload();
      orders.reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setBusy(null);
    }
  }
  return (
    <div>
      <PageHeader title="套餐" description="当前套餐、AI 额度与订单记录" />
      <div className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>当前套餐</CardTitle>
              <p className="mt-1 text-[12.5px] text-muted">
                {plan?.name ?? "免费版"} · {plan?.billing_cycle === "year" ? "按年" : plan?.billing_cycle === "month" ? "按月" : "永久"}
              </p>
            </div>
            <Badge tone="accent">{plan?.code ?? "free"}</Badge>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-3">
              <Metric label="报价额度" value={(plan?.max_quotes ?? 20) === 0 ? "不限" : (plan?.max_quotes ?? 20) + " 份/月"} />
              <Metric label="AI 额度" value={(plan?.ai_quota ?? 100) + " 次/月"} />
              <Metric label="成员账号" value={(plan?.max_users ?? 1) + " 个"} />
            </div>
            <div>
              <div className="flex items-center justify-between text-[12.5px]">
                <span className="text-muted">本月 AI 使用</span>
                <span className="font-medium text-ink">
                  {usage.calls} / {usage.quota || "不限"}（{formatPercent(usage.usage_ratio)}）
                </span>
              </div>
              <Progress
                className="mt-2"
                value={usage.usage_ratio}
                tone={usage.usage_ratio > 0.9 ? "danger" : usage.usage_ratio > 0.7 ? "warning" : "accent"}
              />
              <p className="mt-2 text-[12px] text-faint">
                预估 AI 成本 {formatCurrency(usage.estimated_cost)} · 到期时间{" "}
                {current.data.subscription.end_at ? formatDate(current.data.subscription.end_at) : "长期有效"}
              </p>
            </div>
            {usage.remaining >= 0 && usage.remaining < 20 ? (
              <InlineAlert tone="warning" title={"AI 额度即将用尽，剩余 " + usage.remaining + " 次"}>
                升级套餐可以获得更多额度。
              </InlineAlert>
            ) : null}
            {current.data.subscription.auto_renew ? (
              <Button
                variant="secondary"
                size="sm"
                onClick={async () => {
                  try {
                    await billingApi.cancelAutoRenew();
                    toast.success("已取消自动续费");
                    current.reload();
                  } catch (err) {
                    toast.error(errorMessage(err));
                  }
                }}
              >
                取消自动续费
              </Button>
            ) : null}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>支付说明</CardTitle>
            <CreditCard className="h-4 w-4 text-faint" />
          </CardHeader>
          <CardContent className="space-y-3 text-[13px] text-muted">
            <p>
              第一阶段提供支付抽象层：开发环境使用 mock 支付，下单后自动完成并生效；接入正式微信支付 / 支付宝后即可替换。
            </p>
            <p>套餐配置存放在数据库中，管理员可以随时新增套餐或调整额度，不需要改代码。</p>
            <p className="flex items-center gap-2 text-ink-soft">
              <Sparkles className="h-3.5 w-3.5 text-accent" />
              升级后立即生效，历史报价不受影响。
            </p>
          </CardContent>
        </Card>
      </div>
      <h2 className="mt-6 text-[17px] font-semibold tracking-tight text-ink">选择套餐</h2>
      <div className="mt-3 grid gap-4 lg:grid-cols-3">
        {(plans.data?.items ?? []).map((item) => {
          const active = item.code === plan?.code;
          return (
            <div
              key={item.id}
              className={cn(
                "flex flex-col rounded-[16px] border bg-surface p-5",
                active ? "border-accent bg-accent-soft/30" : "border-line",
              )}
            >
              <div className="flex items-center justify-between">
                <h3 className="text-[15px] font-semibold text-ink">{item.name}</h3>
                {active ? <Badge tone="accent">当前套餐</Badge> : null}
              </div>
              <p className="mt-1 text-[12.5px] text-muted">{item.tagline ?? item.description}</p>
              <div className="mt-4 flex items-end gap-1.5">
                <span className="text-[13px] text-muted">¥</span>
                <span className="text-[28px] font-semibold leading-none text-ink">{item.price}</span>
                <span className="text-[12.5px] text-muted">
                  {item.billing_cycle === "year" ? "/ 年" : item.billing_cycle === "month" ? "/ 月" : "永久"}
                </span>
              </div>
              <ul className="mt-4 flex-1 space-y-2 border-t border-line pt-4">
                <li className="flex items-center gap-2 text-[12.5px] text-ink-soft">
                  <BadgeCheck className="h-3.5 w-3.5 text-accent" />
                  {item.max_quotes === 0 ? "不限报价数量" : "每月 " + item.max_quotes + " 份报价"}
                </li>
                <li className="flex items-center gap-2 text-[12.5px] text-ink-soft">
                  <BadgeCheck className="h-3.5 w-3.5 text-accent" />
                  每月 {item.ai_quota.toLocaleString()} 次 AI
                </li>
                {(item.features ?? []).slice(0, 4).map((feature) => (
                  <li key={feature} className="flex items-center gap-2 text-[12.5px] text-ink-soft">
                    <Check className="h-3.5 w-3.5 text-success" />
                    {plans.data?.feature_labels[feature] ?? feature}
                  </li>
                ))}
              </ul>
              <Button
                className="mt-4"
                variant={active ? "secondary" : "primary"}
                disabled={active}
                loading={busy === item.code}
                onClick={() => void subscribe(item.code)}
              >
                {active ? "已在使用" : "升级到" + item.name}
              </Button>
            </div>
          );
        })}
      </div>
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>订单记录</CardTitle>
        </CardHeader>
        <CardContent className="px-0 pb-0">
          {!orders.data?.length ? (
            <EmptyState
              icon={<CreditCard className="h-5 w-5" />}
              title="暂无订单"
              description="升级套餐后会在这里生成订单记录。"
              className="m-5"
            />
          ) : (
            <Table>
              <THead>
                <Th>订单号</Th>
                <Th>套餐</Th>
                <Th className="text-right">金额</Th>
                <Th>支付方式</Th>
                <Th>状态</Th>
                <Th>创建时间</Th>
                <Th>支付时间</Th>
              </THead>
              <TBody>
                {orders.data.map((order) => (
                  <Tr key={order.id}>
                    <Td className="font-mono text-[12px] text-ink">{order.order_no}</Td>
                    <Td className="text-muted">{order.plan_code}</Td>
                    <Td className="text-right tabular-nums text-ink">{formatCurrency(order.amount)}</Td>
                    <Td className="text-muted">{order.payment_method === "mock" ? "模拟支付" : order.payment_method}</Td>
                    <Td>
                      <StatusBadge status={order.status} />
                    </Td>
                    <Td className="text-[12px] text-faint">{formatDate(order.created_at, true)}</Td>
                    <Td className="text-[12px] text-faint">{order.paid_at ? formatDate(order.paid_at, true) : "—"}</Td>
                  </Tr>
                ))}
              </TBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-line bg-surface-2 px-3.5 py-3">
      <p className="text-[12px] text-muted">{label}</p>
      <p className="mt-1 text-[15px] font-semibold text-ink">{value}</p>
    </div>
  );
}
