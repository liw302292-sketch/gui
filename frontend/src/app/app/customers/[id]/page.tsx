"use client";
import { ArrowLeft, MessageSquarePlus, Pencil, Phone, Plus } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import * as React from "react";
import { PageHeader } from "@/components/app/page-header";
import { StatCard } from "@/components/app/stat-card";
import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Field, Input, Select, Textarea } from "@/components/ui/input";
import { EmptyState, ErrorState, PageLoading } from "@/components/ui/states";
import { toast } from "@/components/ui/toast";
import { useApiData } from "@/hooks/use-api";
import { customerApi, errorMessage, followupApi } from "@/lib/api";
import { formatAmount, formatCurrency, formatDate, relativeTime } from "@/lib/utils";
export default function CustomerDetailPage() {
  const params = useParams<{ id: string }>();
  const customerId = Number(params.id);
  const { data, loading, error, reload } = useApiData(() => customerApi.detail(customerId), [customerId]);
  const [followupOpen, setFollowupOpen] = React.useState(false);
  const [editOpen, setEditOpen] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [followup, setFollowup] = React.useState({ content: "", status: "communicating", next_followup_at: "" });
  const [form, setForm] = React.useState({
    name: "",
    contact_name: "",
    phone: "",
    wechat: "",
    source: "",
    address: "",
    remark: "",
    status: "new",
  });
  React.useEffect(() => {
    if (!data) return;
    const customer = data.customer;
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
  }, [data]);
  if (loading) return <PageLoading label="正在加载客户档案…" />;
  if (error || !data) return <ErrorState message={error ?? "客户不存在"} onRetry={reload} />;
  const customer = data.customer;
  async function saveFollowup() {
    if (!followup.content.trim()) {
      toast.error("请填写跟进内容");
      return;
    }
    setSaving(true);
    try {
      await followupApi.create({
        customer_id: customerId,
        content: followup.content.trim(),
        status: followup.status,
        next_followup_at: followup.next_followup_at ? new Date(followup.next_followup_at).toISOString() : null,
      });
      toast.success("跟进记录已保存");
      setFollowupOpen(false);
      setFollowup({ content: "", status: "communicating", next_followup_at: "" });
      reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }
  async function saveCustomer() {
    setSaving(true);
    try {
      await customerApi.update(customerId, form);
      toast.success("客户信息已更新");
      setEditOpen(false);
      reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }
  return (
    <div>
      <PageHeader
        title={customer.name}
        description={
          <span className="flex flex-wrap items-center gap-2">
            <StatusBadge status={customer.status} />
            {customer.source ? <span className="text-faint">来源：{customer.source}</span> : null}
            {customer.phone ? <span className="text-faint">电话：{customer.phone}</span> : null}
          </span>
        }
        breadcrumb={
          <Link href="/app/customers" className="inline-flex items-center gap-1 hover:text-ink">
            <ArrowLeft className="h-3.5 w-3.5" />
            返回客户列表
          </Link>
        }
        actions={
          <>
            <Button variant="secondary" onClick={() => setEditOpen(true)}>
              <Pencil className="h-4 w-4" />
              编辑资料
            </Button>
            <Button onClick={() => setFollowupOpen(true)}>
              <MessageSquarePlus className="h-4 w-4" />
              添加跟进
            </Button>
          </>
        }
      />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="报价次数" value={String(customer.quote_count)} unit="次" />
        <StatCard label="成交次数" value={String(customer.deal_count)} unit="次" tone="success" />
        <StatCard label="累计成交金额" value={formatAmount(customer.total_amount)} unit="元" tone="success" />
        <StatCard
          label="下次跟进"
          value={customer.next_followup_at ? formatDate(customer.next_followup_at) : "未设置"}
          hint={customer.last_contact_at ? "最近联系 " + relativeTime(customer.last_contact_at) : undefined}
          tone={customer.next_followup_at ? "warning" : "default"}
        />
      </div>
      <div className="mt-5 grid gap-4 xl:grid-cols-[1.4fr_1fr]">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>报价记录</CardTitle>
              <Badge tone="neutral">{data.quotes.length} 份</Badge>
            </CardHeader>
            <CardContent className="space-y-2">
              {data.quotes.length ? (
                data.quotes.map((quote) => (
                  <Link
                    key={quote.id}
                    href={"/app/quotes/" + quote.id}
                    className="flex items-center justify-between gap-3 rounded-xl border border-line px-4 py-3 transition-colors hover:border-line-strong hover:bg-surface-2"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-[13.5px] font-medium text-ink">{quote.project_name}</p>
                      <p className="mt-0.5 font-mono text-[11.5px] text-faint">
                        {quote.quote_no} · {formatDate(quote.created_at)}
                        {quote.view_count > 0 ? " · 已查看 " + quote.view_count + " 次" : ""}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-[13.5px] font-medium tabular-nums text-ink">{formatCurrency(quote.total_amount)}</p>
                      <StatusBadge status={quote.status} label={quote.status_label} />
                    </div>
                  </Link>
                ))
              ) : (
                <EmptyState
                  title="还没有报价记录"
                  description="为该客户创建第一份报价"
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
              <CardTitle>活动记录</CardTitle>
            </CardHeader>
            <CardContent>
              {data.activities.length ? (
                <div className="space-y-3.5">
                  {data.activities.slice(0, 12).map((activity, index) => (
                    <div key={index} className="flex gap-3">
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                      <div>
                        <p className="text-[13px] text-ink-soft">{activity.title}</p>
                        <p className="mt-0.5 text-[12px] text-faint">
                          {activity.detail} · {relativeTime(activity.at)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="暂无活动记录" className="py-8" />
              )}
            </CardContent>
          </Card>
        </div>
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>客户信息</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2.5 text-[13px]">
              <Row label="联系人" value={customer.contact_name ?? "—"} />
              <Row label="手机号" value={customer.phone ?? "—"} />
              <Row label="微信号" value={customer.wechat ?? "—"} />
              <Row label="地址" value={customer.address ?? "—"} />
              <Row label="来源" value={customer.source ?? "—"} />
              <Row label="创建时间" value={formatDate(customer.created_at)} />
              {customer.remark ? (
                <div className="rounded-xl bg-surface-2 p-3 text-[12.5px] text-muted">{customer.remark}</div>
              ) : null}
              {customer.phone ? (
                <a href={"tel:" + customer.phone}>
                  <Button variant="secondary" size="sm" className="mt-1">
                    <Phone className="h-3.5 w-3.5" />
                    拨打电话
                  </Button>
                </a>
              ) : null}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>跟进记录</CardTitle>
              <Badge tone="neutral">{data.followups.length} 条</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              {data.followups.length ? (
                data.followups.map((item) => (
                  <div key={item.id} className="rounded-xl border border-line bg-surface-2/60 p-3">
                    <div className="flex items-center justify-between">
                      <StatusBadge status={item.status} />
                      <span className="text-[11.5px] text-faint">{relativeTime(item.created_at)}</span>
                    </div>
                    <p className="mt-2 text-[12.5px] leading-relaxed text-ink-soft">{item.content}</p>
                    {item.next_followup_at ? (
                      <p className="mt-1.5 text-[11.5px] text-warning">下次跟进：{formatDate(item.next_followup_at, true)}</p>
                    ) : null}
                  </div>
                ))
              ) : (
                <EmptyState
                  title="暂无跟进记录"
                  description="记录一次沟通，避免遗漏客户"
                  action={
                    <Button size="sm" onClick={() => setFollowupOpen(true)}>
                      <MessageSquarePlus className="h-3.5 w-3.5" />
                      添加跟进
                    </Button>
                  }
                  className="py-8"
                />
              )}
            </CardContent>
          </Card>
        </div>
      </div>
      <Dialog
        open={followupOpen}
        onClose={() => setFollowupOpen(false)}
        title="添加跟进记录"
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setFollowupOpen(false)}>
              取消
            </Button>
            <Button loading={saving} onClick={() => void saveFollowup()}>
              保存
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Field label="跟进内容" required>
            <Textarea
              value={followup.content}
              onChange={(event) => setFollowup({ ...followup, content: event.target.value })}
              placeholder="例如：客户确认尺寸无误，等门店负责人签字后下单"
            />
          </Field>
          <Field label="客户状态">
            <Select value={followup.status} onChange={(event) => setFollowup({ ...followup, status: event.target.value })}>
              <option value="new">新客户</option>
              <option value="quoted">已报价</option>
              <option value="communicating">沟通中</option>
              <option value="high_intent">高意向</option>
              <option value="won">已成交</option>
              <option value="lost">已流失</option>
            </Select>
          </Field>
          <Field label="下次跟进时间" hint="留空表示暂不安排">
            <Input
              type="datetime-local"
              value={followup.next_followup_at}
              onChange={(event) => setFollowup({ ...followup, next_followup_at: event.target.value })}
            />
          </Field>
        </div>
      </Dialog>
      <Dialog
        open={editOpen}
        onClose={() => setEditOpen(false)}
        title="编辑客户资料"
        footer={
          <>
            <Button variant="secondary" onClick={() => setEditOpen(false)}>
              取消
            </Button>
            <Button loading={saving} onClick={() => void saveCustomer()}>
              保存
            </Button>
          </>
        }
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="客户名称" required className="sm:col-span-2">
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
          <Field label="状态">
            <Select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}>
              <option value="new">新客户</option>
              <option value="quoted">已报价</option>
              <option value="communicating">沟通中</option>
              <option value="high_intent">高意向</option>
              <option value="won">已成交</option>
              <option value="lost">已流失</option>
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
    </div>
  );
}
function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-muted">{label}</span>
      <span className="text-right font-medium text-ink-soft">{value}</span>
    </div>
  );
}

