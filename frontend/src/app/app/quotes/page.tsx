"use client";

import { FileText, Filter, Plus, Search } from "lucide-react";
import Link from "next/link";
import * as React from "react";

import { PageHeader } from "@/components/app/page-header";
import { StatCard } from "@/components/app/stat-card";
import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input, Select } from "@/components/ui/input";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/states";
import { Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { Tabs } from "@/components/ui/tabs";
import { useApiData } from "@/hooks/use-api";
import { quoteApi } from "@/lib/api";
import { formatAmount, formatCurrency, formatDate, formatPercent, relativeTime } from "@/lib/utils";

const STATUS_TABS = [
  { value: "", label: "全部" },
  { value: "draft", label: "草稿" },
  { value: "sent", label: "已发送" },
  { value: "viewed", label: "已查看" },
  { value: "following", label: "待跟进" },
  { value: "won", label: "已成交" },
  { value: "void", label: "已作废" },
];

export default function QuotesPage() {
  const [status, setStatus] = React.useState("");
  const [keyword, setKeyword] = React.useState("");
  const [search, setSearch] = React.useState("");
  const [page, setPage] = React.useState(1);

  React.useEffect(() => {
    const timer = window.setTimeout(() => {
      setSearch(keyword.trim());
      setPage(1);
    }, 300);
    return () => window.clearTimeout(timer);
  }, [keyword]);

  const { data, loading, error, reload } = useApiData(
    () => quoteApi.list({ status: status || undefined, keyword: search || undefined, page, page_size: 20 }),
    [status, search, page],
  );

  const totalPages = data ? Math.max(Math.ceil(data.total / data.page_size), 1) : 1;

  return (
    <div>
      <PageHeader
        title="报价"
        description="所有报价单、状态与客户查看情况"
        actions={
          <Link href="/app/quotes/new">
            <Button>
              <Plus className="h-4 w-4" />
              新建报价
            </Button>
          </Link>
        }
      />

      {data ? (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="报价总数" value={String(data.summary.quote_count)} unit="份" />
          <StatCard label="报价总金额" value={formatAmount(data.summary.quote_amount)} unit="元" tone="accent" />
          <StatCard label="成交数量" value={String(data.summary.won_count)} unit="份" tone="success" />
          <StatCard label="成交金额" value={formatAmount(data.summary.won_amount)} unit="元" tone="success" />
        </div>
      ) : null}

      <Card className="mt-5">
        <CardContent className="pt-5">
          <div className="flex flex-wrap items-center gap-3">
            <Tabs tabs={STATUS_TABS} value={status} onChange={(value) => { setStatus(value); setPage(1); }} />
            <div className="ml-auto flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-faint" />
                <Input
                  value={keyword}
                  onChange={(event) => setKeyword(event.target.value)}
                  placeholder="搜索报价编号 / 项目 / 客户"
                  className="w-full pl-9 sm:w-64"
                />
              </div>
            </div>
          </div>

          <div className="mt-4">
            {loading ? (
              <SkeletonRows rows={6} />
            ) : error ? (
              <ErrorState message={error} onRetry={reload} />
            ) : !data || data.items.length === 0 ? (
              <EmptyState
                icon={<FileText className="h-5 w-5" />}
                title="暂无报价"
                description="上传一张客户需求截图，30 秒生成第一份专业报价单。"
                action={
                  <Link href="/app/quotes/new">
                    <Button>
                      <Plus className="h-4 w-4" />
                      新建报价
                    </Button>
                  </Link>
                }
              />
            ) : (
              <>
                <Table>
                  <THead>
                    <Th>报价编号</Th>
                    <Th>项目 / 客户</Th>
                    <Th className="text-right">金额</Th>
                    <Th className="text-right">毛利率</Th>
                    <Th>状态</Th>
                    <Th>客户查看</Th>
                    <Th>创建时间</Th>
                    <Th />
                  </THead>
                  <TBody>
                    {data.items.map((quote) => (
                      <Tr key={quote.id} className="hover:bg-surface-2/70">
                        <Td>
                          <Link href={`/app/quotes/${quote.id}`} className="font-mono text-[12.5px] text-ink hover:text-accent">
                            {quote.quote_no}
                          </Link>
                          {quote.version_no > 1 ? (
                            <span className="ml-2 rounded-full bg-surface-2 px-1.5 py-0.5 text-[11px] text-faint">
                              V{quote.version_no}
                            </span>
                          ) : null}
                        </Td>
                        <Td>
                          <Link href={`/app/quotes/${quote.id}`} className="font-medium text-ink hover:text-accent">
                            {quote.project_name}
                          </Link>
                          <p className="mt-0.5 text-[12px] text-faint">
                            {quote.customer_name ?? "未指定客户"} · {quote.item_count} 个报价项
                          </p>
                        </Td>
                        <Td className="text-right font-medium tabular-nums text-ink">
                          {formatCurrency(quote.total_amount)}
                        </Td>
                        <Td className="text-right tabular-nums">{formatPercent(quote.gross_margin)}</Td>
                        <Td>
                          <StatusBadge status={quote.status} label={quote.status_label} />
                        </Td>
                        <Td className="text-[12.5px] text-muted">
                          {quote.view_count > 0 ? (
                            <span className="text-accent">
                              已查看 {quote.view_count} 次
                              <span className="ml-1 text-faint">{relativeTime(quote.last_viewed_at)}</span>
                            </span>
                          ) : (
                            <span className="text-faint">未查看</span>
                          )}
                        </Td>
                        <Td className="text-[12.5px] text-muted">{formatDate(quote.created_at)}</Td>
                        <Td className="text-right">
                          <Link href={`/app/quotes/${quote.id}`}>
                            <Button variant="ghost" size="sm">
                              查看
                            </Button>
                          </Link>
                        </Td>
                      </Tr>
                    ))}
                  </TBody>
                </Table>

                {totalPages > 1 ? (
                  <div className="mt-4 flex items-center justify-between text-[12.5px] text-muted">
                    <span>
                      共 {data.total} 条，第 {page} / {totalPages} 页
                    </span>
                    <div className="flex gap-2">
                      <Button
                        variant="secondary"
                        size="sm"
                        disabled={page <= 1}
                        onClick={() => setPage((value) => Math.max(value - 1, 1))}
                      >
                        上一页
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        disabled={page >= totalPages}
                        onClick={() => setPage((value) => Math.min(value + 1, totalPages))}
                      >
                        下一页
                      </Button>
                    </div>
                  </div>
                ) : null}
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

