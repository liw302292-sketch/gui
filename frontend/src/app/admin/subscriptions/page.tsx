"use client";
import { FileText } from "lucide-react";
import * as React from "react";
import { PageHeader } from "@/components/app/page-header";
import { StatusBadge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/states";
import { Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { useApiData } from "@/hooks/use-api";
import { adminApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
export default function AdminSubscriptionsPage() {
  const { data, loading, error, reload } = useApiData(() => adminApi.subscriptions(), []);
  return (
    <div>
      <PageHeader title="订阅" description="企业套餐订阅与续费状态" />
      <Card>
        <CardContent className="pt-5">
          {loading ? (
            <SkeletonRows rows={5} />
          ) : error ? (
            <ErrorState message={error} onRetry={reload} />
          ) : !data?.length ? (
            <EmptyState icon={<FileText className="h-5 w-5" />} title="暂无订阅" />
          ) : (
            <Table>
              <THead>
                <Th>企业</Th>
                <Th>套餐</Th>
                <Th>状态</Th>
                <Th>开始时间</Th>
                <Th>结束时间</Th>
                <Th>自动续费</Th>
              </THead>
              <TBody>
                {data.map((item) => (
                  <Tr key={item.id}>
                    <Td className="font-medium text-ink">{item.company_name ?? "—"}</Td>
                    <Td className="text-muted">{item.plan_code ?? "free"}</Td>
                    <Td>
                      <StatusBadge status={item.status} />
                    </Td>
                    <Td className="text-[12.5px] text-muted">{formatDate(item.start_at)}</Td>
                    <Td className="text-[12.5px] text-muted">{item.end_at ? formatDate(item.end_at) : "长期有效"}</Td>
                    <Td className="text-[12.5px] text-muted">{item.auto_renew ? "已开启" : "未开启"}</Td>
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

