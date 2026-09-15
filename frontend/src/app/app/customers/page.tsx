"use client";
import { Pencil, Plus, Search, Trash2, Users } from "lucide-react";
import Link from "next/link";
import * as React from "react";
import { PageHeader } from "@/components/app/page-header";
import { StatCard } from "@/components/app/stat-card";
import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ConfirmDialog, Dialog } from "@/components/ui/dialog";
import { Field, Input, Select, Textarea } from "@/components/ui/input";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/states";
import { Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { Tabs } from "@/components/ui/tabs";
import { toast } from "@/components/ui/toast";
import { useApiData } from "@/hooks/use-api";
import { customerApi, errorMessage } from "@/lib/api";
import type { Customer } from "@/lib/types";
import { formatAmount, formatCurrency, formatDate } from "@/lib/utils";
const STATUS_TABS = [
  { value: "", label: "全部" },
  { value: "new", label: "新客户" },
  { value: "quoted", label: "已报价" },
  { value: "communicating", label: "沟通中" },
  { value: "high_intent", label: "高意向" },
  { value: "won", label: "已成交" },
  { value: "lost", label: "已流失" },
];
export default function CustomersPage() {
  const [status, setStatus] = React.useState("");
  const [keyword, setKeyword] = React.useState("");
  const [search, setSearch] = React.useState("");
  const [page, setPage] = React.useState(1);
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<Customer | null>(null);
  const [deleteTarget, setDeleteTarget] = React.useState<Customer | null>(null);
  const [saving, setSaving] = React.useState(false);
  const [form, setForm] = React.useState({
    name: "",
    contact_name: "",
    phone: "",
    wechat: "",
    source: "微信",
    address: "",
    remark: "",
    status: "new",
  });
  React.useEffect(() => {
    const timer = window.setTimeout(() => {
      setSearch(keyword.trim());
      setPage(1);
    }, 300);
    return () => window.clearTimeout(timer);
  }, [keyword]);
  const { data, loading, error, reload } = useApiData(
    () => customerApi.list({ status: status || undefined, keyword: search || undefined, page, page_size: 20 }),
    [status, search, page],
  );
  function openCreate() {
    setEditing(null);
    setForm({ name: "", contact_name: "", phone: "", wechat: "", source: "微信", address: "", remark: "", status: "new" });
    setDialogOpen(true);
  }
  function openEdit(customer: Customer) {
    setEditing(customer);
    setForm({
      name: customer.name,
      contact_name: customer.contact_name ?? "",
      phone: customer.phone ?? "",
      wechat: customer.wechat ?? "",
      source: customer.source ?? "",
      address: customer.address ?? "",
      remark: customer.remark ?? "",
      status: customer.status,
    });
    setDialogOpen(true);
  }
  async function save() {
    if (!form.name.trim()) {
      toast.error("请填写客户名称");
      return;
    }
    setSaving(true);
    try {
      if (editing) {
        await customerApi.update(editing.id, form);
        toast.success("客户已更新");
      } else {
        await customerApi.create(form);
        toast.success("客户已创建");
      }
      setDialogOpen(false);
      reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }
  async function remove() {
    if (!deleteTarget) return;
    try {
      await customerApi.remove(deleteTarget.id);
      toast.success("客户已删除");
      setDeleteTarget(null);
      reload();
    } catch (err) {
      toast.error(errorMessage(err));
    }
  }
  const totalPages = data ? Math.max(Math.ceil(data.total / data.page_size), 1) : 1;
  return (
    <div>
      <PageHeader
        title="客户"
        description="客户档案、报价历史与跟进状态"
        actions={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" />
            新增客户
          </Button>
        }
      />
      {data ? (
        <div className="grid gap-3 sm:grid-cols-3">
          <StatCard label="客户总数" value={String(data.summary.total_customers)} unit="个" />
          <StatCard label="累计成交金额" value={formatAmount(data.summary.total_amount)} unit="元" tone="success" />
          <StatCard
            label="高意向客户"
            value={String(data.items.filter((item) => item.status === "high_intent").length)}
            unit="个"
            tone="accent"
          />
        </div>
      ) : null}
      <Card className="mt-5">
        <CardContent className="pt-5">
          <div className="flex flex-wrap items-center gap-3">
            <Tabs tabs={STATUS_TABS} value={status} onChange={(value) => { setStatus(value); setPage(1); }} />
            <div className="relative ml-auto">
              <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-faint" />
              <Input
                value={keyword}
                onChange={(event) => setKeyword(event.target.value)}
                placeholder="搜索客户名称 / 联系人 / 电话"
                className="w-full pl-9 sm:w-64"
              />
            </div>
          </div>
          <div className="mt-4">
            {loading ? (
              <SkeletonRows rows={6} />
            ) : error ? (
              <ErrorState message={error} onRetry={reload} />
            ) : !data || !data.items.length ? (
              <EmptyState
                icon={<Users className="h-5 w-5" />}
                title="暂无客户"
                description="新建报价时填写客户名称，系统会自动创建客户档案。"
                action={
                  <Button onClick={openCreate}>
                    <Plus className="h-4 w-4" />
                    新增客户
                  </Button>
                }
              />
            ) : (
              <>
                <Table>
                  <THead>
                    <Th>客户名称</Th>
                    <Th>联系人</Th>
                    <Th>来源</Th>
                    <Th className="text-right">报价</Th>
                    <Th className="text-right">成交</Th>
                    <Th className="text-right">累计金额</Th>
                    <Th>状态</Th>
                    <Th>下次跟进</Th>
                    <Th />
                  </THead>
                  <TBody>
                    {data.items.map((customer) => (
                      <Tr key={customer.id}>
                        <Td>
                          <Link href={"/app/customers/" + customer.id} className="font-medium text-ink hover:text-accent">
                            {customer.name}
                          </Link>
                          {customer.address ? <p className="mt-0.5 truncate text-[12px] text-faint">{customer.address}</p> : null}
                        </Td>
                        <Td>
                          <p className="text-ink-soft">{customer.contact_name ?? "—"}</p>
                          <p className="text-[12px] text-faint">{customer.phone ?? "无电话"}</p>
                        </Td>
                        <Td className="text-[12.5px] text-muted">{customer.source ?? "—"}</Td>
                        <Td className="text-right tabular-nums">{customer.quote_count}</Td>
                        <Td className="text-right tabular-nums">{customer.deal_count}</Td>
                        <Td className="text-right font-medium tabular-nums text-ink">{formatCurrency(customer.total_amount)}</Td>
                        <Td>
                          <StatusBadge status={customer.status} label={customerStatusLabel(customer.status)} />
                        </Td>
                        <Td className="text-[12.5px] text-muted">
                          {customer.next_followup_at ? formatDate(customer.next_followup_at) : "—"}
                        </Td>
                        <Td>
                          <div className="flex items-center justify-end gap-1">
                            <Button variant="ghost" size="iconSm" onClick={() => openEdit(customer)} aria-label="编辑">
                              <Pencil className="h-3.5 w-3.5" />
                            </Button>
                            <Button variant="ghost" size="iconSm" onClick={() => setDeleteTarget(customer)} aria-label="删除">
                              <Trash2 className="h-3.5 w-3.5 text-danger" />
                            </Button>
                          </div>
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
                      <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>
                        上一页
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        disabled={page >= totalPages}
                        onClick={() => setPage((value) => value + 1)}
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
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title={editing ? "编辑客户" : "新增客户"}
        footer={
          <>
            <Button variant="secondary" onClick={() => setDialogOpen(false)}>
              取消
            </Button>
            <Button loading={saving} onClick={() => void save()}>
              保存
            </Button>
          </>
        }
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="公司名称 / 客户名称" required className="sm:col-span-2">
            <Input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
          </Field>
          <Field label="联系人">
            <Input value={form.contact_name} onChange={(event) => setForm({ ...form, contact_name: event.target.value })} />
          </Field>
          <Field label="手机号">
            <Input value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} />
          </Field>
          <Field label="微信号">
            <Input value={form.wechat} onChange={(event) => setForm({ ...form, wechat: event.target.value })} />
          </Field>
          <Field label="来源">
            <Select value={form.source} onChange={(event) => setForm({ ...form, source: event.target.value })}>
              {["微信", "电话", "转介绍", "朋友介绍", "自然到访", "抖音", "老客户复购", "其他"].map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="状态">
            <Select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}>
              {STATUS_TABS.filter((item) => item.value).map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="地址" className="sm:col-span-2">
            <Input value={form.address} onChange={(event) => setForm({ ...form, address: event.target.value })} />
          </Field>
          <Field label="备注" className="sm:col-span-2">
            <Textarea value={form.remark} onChange={(event) => setForm({ ...form, remark: event.target.value })} />
          </Field>
        </div>
      </Dialog>
      <ConfirmDialog
        open={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        title="确认删除客户？"
        description="如果该客户已有报价单，需要先作废报价才能删除。"
        confirmText="删除"
        danger
        onConfirm={() => void remove()}
      />
    </div>
  );
}
function customerStatusLabel(status: string) {
  const map: Record<string, string> = {
    new: "新客户",
    quoted: "已报价",
    communicating: "沟通中",
    high_intent: "高意向",
    won: "已成交",
    lost: "已流失",
  };
  return map[status] ?? status;
}

