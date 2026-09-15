"use client";
import { Building2, Search, Settings2 } from "lucide-react";
import * as React from "react";
import { PageHeader } from "@/components/app/page-header";
import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Field, Input } from "@/components/ui/input";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/states";
import { Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { toast } from "@/components/ui/toast";
import { useApiData } from "@/hooks/use-api";
import { adminApi, errorMessage } from "@/lib/api";
import { formatDate } from "@/lib/utils";
export default function AdminCompaniesPage() {
  const [keyword, setKeyword] = React.useState("");
  const [search, setSearch] = React.useState("");
  const [status, setStatus] = React.useState("");
  const [page, setPage] = React.useState(1);
  const { data, loading, error, reload } = useApiData(
    () => adminApi.companies({ keyword: search || undefined, status: status || undefined, page, page_size: 20 }),
    [search, status, page],
  );
  const [detailId, setDetailId] = React.useState<number | null>(null);
  const detail = useApiData(() => (detailId ? adminApi.companyDetail(detailId) : Promise.resolve(null)), [detailId]);
  const [quota, setQuota] = React.useState(0);
  React.useEffect(() => {
    const timer = window.setTimeout(() => {
      setSearch(keyword.trim());
      setPage(1);
    }, 300);
    return () => window.clearTimeout(timer);
  }, [keyword]);
  async function toggleStatus(id: number, current: string) {
    try {
      await adminApi.setCompanyStatus(id, current === "active" ? "disabled" : "active");
      toast.success(current === "active" ? "企业已停用" : "企业已启用");
      reload();
    } catch (err) {
      toast.error(errorMessage(err));
    }
  }
  async function saveQuota(id: number) {
    try {
      await adminApi.setQuota(id, quota);
      toast.success("AI 额度已更新");
      detail.reload();
      reload();
    } catch (err) {
      toast.error(errorMessage(err));
    }
  }
  return (
    <div>
      <PageHeader
        title="企业管理"
        description="查看企业信息、套餐、员工人数、报价数量与 AI 用量"
        actions={
          <div className="flex items-center gap-2">
            <select
              value={status}
              onChange={(event) => setStatus(event.target.value)}
              className="h-10 rounded-xl border border-line-strong bg-surface px-3 text-[13px]"
            >
              <option value="">全部状态</option>
              <option value="active">正常</option>
              <option value="disabled">已停用</option>
            </select>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-faint" />
              <Input
                value={keyword}
                onChange={(event) => setKeyword(event.target.value)}
                placeholder="搜索企业名称 / 手机号"
                className="w-56 pl-9"
              />
            </div>
          </div>
        }
      />
      <Card>
        <CardContent className="pt-5">
          {loading ? (
            <SkeletonRows rows={6} />
          ) : error ? (
            <ErrorState message={error} onRetry={reload} />
          ) : !data?.items.length ? (
            <EmptyState icon={<Building2 className="h-5 w-5" />} title="暂无企业" />
          ) : (
            <Table>
              <THead>
                <Th>企业名称</Th>
                <Th>老板 / 联系方式</Th>
                <Th>套餐</Th>
                <Th className="text-right">员工</Th>
                <Th className="text-right">报价</Th>
                <Th className="text-right">AI 用量</Th>
                <Th>注册时间</Th>
                <Th>状态</Th>
                <Th />
              </THead>
              <TBody>
                {data.items.map((company) => (
                  <Tr key={company.id}>
                    <Td>
                      <p className="font-medium text-ink">{company.name}</p>
                      <p className="mt-0.5 text-[11.5px] text-faint">#{company.id} · {company.industry_id}</p>
                    </Td>
                    <Td>
                      <p className="text-ink-soft">{company.owner_name ?? "—"}</p>
                      <p className="text-[12px] text-faint">{company.owner_email ?? company.owner_phone ?? "—"}</p>
                    </Td>
                    <Td>
                      <Badge tone={company.plan_code === "free" ? "neutral" : "accent"}>{company.plan_name ?? "免费版"}</Badge>
                    </Td>
                    <Td className="text-right tabular-nums">{company.member_count}</Td>
                    <Td className="text-right tabular-nums">{company.quote_count}</Td>
                    <Td className="text-right tabular-nums">{company.ai_calls}</Td>
                    <Td className="text-[12px] text-muted">{formatDate(company.created_at)}</Td>
                    <Td>
                      <StatusBadge status={company.status} label={company.status === "active" ? "正常" : "已停用"} />
                    </Td>
                    <Td>
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="sm" onClick={() => { setDetailId(company.id); setQuota(0); }}>
                          <Settings2 className="h-3.5 w-3.5" />
                          管理
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => void toggleStatus(company.id, company.status)}>
                          {company.status === "active" ? "停用" : "启用"}
                        </Button>
                      </div>
                    </Td>
                  </Tr>
                ))}
              </TBody>
            </Table>
          )}
        </CardContent>
      </Card>
      <Dialog
        open={Boolean(detailId)}
        onClose={() => setDetailId(null)}
        title="企业详情"
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={() => setDetailId(null)}>
              关闭
            </Button>
            {detailId ? (
              <Button onClick={() => void saveQuota(detailId)} disabled={!quota}>
                保存 AI 额度
              </Button>
            ) : null}
          </>
        }
      >
        {detail.loading ? (
          <SkeletonRows rows={4} />
        ) : detail.data ? (
          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              {Object.entries(detail.data.company).map(([key, value]) => (
                <div key={key} className="rounded-xl border border-line bg-surface-2 p-3">
                  <p className="text-[11.5px] text-faint">{labelMap[key] ?? key}</p>
                  <p className="mt-1 text-[13px] font-medium text-ink">{String(value ?? "—")}</p>
                </div>
              ))}
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <Metric label="报价数量" value={String(detail.data.quote_count)} />
              <Metric label="客户数量" value={String(detail.data.customer_count)} />
              <Metric label="本月 AI 调用" value={String(detail.data.ai_usage.calls)} />
            </div>
            <div>
              <p className="text-[13px] font-medium text-ink">成员</p>
              <div className="mt-2 space-y-2">
                {detail.data.members.map((member) => (
                  <div key={member.id} className="flex items-center justify-between rounded-xl border border-line px-3.5 py-2.5">
                    <div>
                      <p className="text-[13px] font-medium text-ink">{member.name}</p>
                      <p className="text-[11.5px] text-faint">{member.email ?? member.phone ?? "—"}</p>
                    </div>
                    <Badge tone={member.role === "owner" ? "accent" : "neutral"}>{member.role}</Badge>
                  </div>
                ))}
              </div>
            </div>
            <Field label="设置 AI 每月额度（次）" hint="0 表示不限制">
              <Input
                type="number"
                value={quota || ""}
                onChange={(event) => setQuota(Number(event.target.value))}
                placeholder="例如 2000"
              />
            </Field>
          </div>
        ) : (
          <EmptyState title="加载失败" />
        )}
      </Dialog>
    </div>
  );
}
function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-line bg-surface-2 p-3">
      <p className="text-[11.5px] text-faint">{label}</p>
      <p className="mt-1 text-[16px] font-semibold text-ink">{value}</p>
    </div>
  );
}
const labelMap: Record<string, string> = {
  id: "企业 ID",
  name: "企业名称",
  industry_id: "行业模板",
  status: "状态",
  contact_name: "联系人",
  contact_phone: "联系电话",
  address: "地址",
  ai_monthly_quota: "AI 每月额度",
  created_at: "注册时间",
};

