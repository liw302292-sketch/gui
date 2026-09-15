"use client";
import { Bell, Check, ListChecks, MessageSquarePlus, Phone, Plus } from "lucide-react";
import Link from "next/link";
import * as React from "react";
import { PageHeader } from "@/components/app/page-header";
import { StatCard } from "@/components/app/stat-card";
import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/states";
import { Tabs } from "@/components/ui/tabs";
import { toast } from "@/components/ui/toast";
import { useApiData } from "@/hooks/use-api";
import { errorMessage, followupApi } from "@/lib/api";
import { formatDate, relativeTime } from "@/lib/utils";
const SCOPES = [
  { value: "today", label: "今日待跟进" },
  { value: "overdue", label: "已逾期" },
  { value: "all", label: "全部" },
  { value: "done", label: "已完成" },
];
export default function FollowupsPage() {
  const [scope, setScope] = React.useState("today");
  const [page, setPage] = React.useState(1);
  const { data, loading, error, reload } = useApiData(
    () => followupApi.list({ scope, page, page_size: 20 }),
    [scope, page],
  );
  const today = useApiData(() => followupApi.today(), [scope]);
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [form, setForm] = React.useState({ content: "", next_followup_at: "" });
  const [target, setTarget] = React.useState<{ id: number; name: string } | null>(null);
  async function complete(id: number) {
    try {
      await followupApi.update(id, { done: true });
      toast.success("已标记完成");
      reload();
      today.reload();
    } catch (err) {
      toast.error(errorMessage(err));
    }
  }
  async function save() {
    if (!target || !form.content.trim()) {
      toast.error("请填写跟进内容");
      return;
    }
    setSaving(true);
    try {
      await followupApi.create({
        customer_id: target.id,
        content: form.content.trim(),
        next_followup_at: form.next_followup_at ? new Date(form.next_followup_at).toISOString() : null,
      });
      toast.success("跟进记录已保存");
      setDialogOpen(false);
      setForm({ content: "", next_followup_at: "" });
      reload();
      today.reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }
  return (
    <div>
      <PageHeader title="跟进" description="今天该联系谁、上次聊了什么，一眼看清" />
      <div className="grid gap-3 sm:grid-cols-3">
        <StatCard
          label="今日待跟进"
          value={String(today.data?.count ?? 0)}
          unit="个"
          tone={(today.data?.count ?? 0) > 0 ? "warning" : "success"}
          icon={<Bell className="h-4 w-4" />}
        />
        <StatCard label="跟进记录总数" value={String(data?.total ?? 0)} unit="条" icon={<ListChecks className="h-4 w-4" />} />
        <StatCard
          label="当前视图"
          value={SCOPES.find((item) => item.value === scope)?.label ?? "全部"}
          hint={today.data?.hint}
        />
      </div>
      <Card className="mt-5">
        <CardHeader>
          <CardTitle>跟进列表</CardTitle>
          <Tabs
            tabs={SCOPES}
            value={scope}
            onChange={(value) => {
              setScope(value);
              setPage(1);
            }}
          />
        </CardHeader>
        <CardContent>
          {loading ? (
            <SkeletonRows rows={5} />
          ) : error ? (
            <ErrorState message={error} onRetry={reload} />
          ) : !data?.items.length ? (
            <EmptyState
              icon={<Check className="h-5 w-5" />}
              title={scope === "today" ? "今天没有需要跟进的客户" : "暂无跟进记录"}
              description={
                scope === "today"
                  ? "所有安排都跟完了。可以给客户设置下次跟进时间，系统会自动提醒。"
                  : "在客户详情页添加跟进记录后，这里会显示安排。"
              }
              action={
                <Link href="/app/customers">
                  <Button size="sm">去客户列表</Button>
                </Link>
              }
            />
          ) : (
            <div className="space-y-3">
              {data.items.map((item) => (
                <div key={item.id} className="rounded-[14px] border border-line bg-surface p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <Link
                          href={"/app/customers/" + item.customer_id}
                          className="text-[14px] font-medium text-ink hover:text-accent"
                        >
                          {item.customer_name ?? "未命名客户"}
                        </Link>
                        <StatusBadge status={item.status} />
                        {item.done ? <StatusBadge status="won" label="已完成" /> : null}
                      </div>
                      <p className="mt-2 text-[13px] leading-relaxed text-ink-soft">{item.content}</p>
                      <p className="mt-1.5 text-[12px] text-faint">
                        {item.channel === "wechat" ? "微信" : item.channel === "phone" ? "电话" : "上门"} ·{" "}
                        {relativeTime(item.created_at)}
                        {item.next_followup_at ? " · 下次：" + formatDate(item.next_followup_at, true) : ""}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => {
                          setTarget({ id: item.customer_id, name: item.customer_name ?? "客户" });
                          setForm({ content: "", next_followup_at: "" });
                          setDialogOpen(true);
                        }}
                      >
                        <MessageSquarePlus className="h-3.5 w-3.5" />
                        再记录一次
                      </Button>
                      {!item.done ? (
                        <Button variant="ghost" size="sm" onClick={() => void complete(item.id)}>
                          <Check className="h-3.5 w-3.5" />
                          标记完成
                        </Button>
                      ) : null}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      {today.data?.items.length ? (
        <Card className="mt-4">
          <CardHeader>
            <CardTitle>今日待跟进客户</CardTitle>
            <span className="text-[12.5px] text-faint">{today.data.hint}</span>
          </CardHeader>
          <CardContent className="space-y-2">
            {today.data.items.map((item) => (
              <div
                key={item.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-line px-4 py-3"
              >
                <div>
                  <Link href={"/app/customers/" + item.id} className="text-[13.5px] font-medium text-ink hover:text-accent">
                    {item.name}
                  </Link>
                  <p className="mt-0.5 text-[12px] text-faint">
                    {item.contact_name ?? "—"} · {item.phone ?? "无电话"} · 累计 ¥{item.total_amount.toFixed(0)}
                  </p>
                </div>
                <div className="flex gap-2">
                  {item.phone ? (
                    <a href={"tel:" + item.phone}>
                      <Button variant="secondary" size="sm">
                        <Phone className="h-3.5 w-3.5" />
                        打电话
                      </Button>
                    </a>
                  ) : null}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setTarget({ id: item.id, name: item.name });
                      setForm({ content: "", next_followup_at: "" });
                      setDialogOpen(true);
                    }}
                  >
                    <Plus className="h-3.5 w-3.5" />
                    记录跟进
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title={"记录跟进 · " + (target?.name ?? "")}
        size="sm"
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
        <div className="space-y-4">
          <div>
            <label className="mb-1.5 block text-[13px] font-medium text-ink-soft">跟进内容</label>
            <textarea
              value={form.content}
              onChange={(event) => setForm({ ...form, content: event.target.value })}
              placeholder="例如：客户确认尺寸无误，等门店负责人签字后下单"
              className="min-h-[110px] w-full rounded-xl border border-line-strong bg-surface px-3.5 py-2.5 text-[14px] text-ink"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-[13px] font-medium text-ink-soft">下次跟进时间</label>
            <input
              type="datetime-local"
              value={form.next_followup_at}
              onChange={(event) => setForm({ ...form, next_followup_at: event.target.value })}
              className="h-10 w-full rounded-xl border border-line-strong bg-surface px-3.5 text-[14px]"
            />
          </div>
        </div>
      </Dialog>
    </div>
  );
}

