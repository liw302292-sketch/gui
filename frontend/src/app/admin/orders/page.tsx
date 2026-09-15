"use client";
import { CreditCard } from "lucide-react";
import * as React from "react";
import { PageHeader } from "@/components/app/page-header";
import { StatusBadge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/states";
import { Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { useApiData } from "@/hooks/use-api";
import { adminApi } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
export default function AdminOrdersPage() {
  const { data, loading, error, reload } = useApiData(() => adminApi.orders(), []);
  return (
    <div>
      <PageHeader title="订单" description="所有企业订单与支付状态" />
      <Card>
        <CardContent className="pt-5">
          {loading ? (
            <SkeletonRows rows={5} />
          ) : error ? (
            <ErrorState message={error} onRetry={reload} />
          ) : !data?.length ? (
            <EmptyState icon={<CreditCard className="h-5 w-5" />} title="暂无订单" />
          ) : (
            <Table>
              <THead>
                <Th>订单号</Th>
                <Th>企业</Th>
                <Th>套餐</Th>
                <Th className="text-right">金额</Th>
                <Th>支付方式</Th>
                <Th>状态</Th>
                <Th>创建时间</Th>
                <Th>支付时间</Th>
              </THead>
              <TBody>
                {data.map((order) => (
                  <Tr key={order.id}>
                    <Td className="font-mono text-[12px] text-ink">{order.order_no}</Td>
                    <Td className="text-ink-soft">{order.company_name ?? "—"}</Td>
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

