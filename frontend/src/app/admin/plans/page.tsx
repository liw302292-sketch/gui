"use client";
import { Layers, Pencil, Plus } from "lucide-react";
import * as React from "react";
import { PageHeader } from "@/components/app/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Field, Input } from "@/components/ui/input";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/states";
import { Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { toast } from "@/components/ui/toast";
import { useApiData } from "@/hooks/use-api";
import { adminApi, errorMessage } from "@/lib/api";
import type { Plan } from "@/lib/types";
import { formatCurrency } from "@/lib/utils";
const FEATURES = [
  { key: "quotes", label: "报价单与报价闭环" },
  { key: "ai", label: "AI 识别与助手" },
  { key: "analytics", label: "数据统计" },
  { key: "branding", label: "品牌与自定义报价单" },
  { key: "members", label: "多人协作" },
  { key: "api", label: "开放 API" },
  { key: "private_deploy", label: "私有部署" },
];
export default function AdminPlansPage() {
  const { data, loading, error, reload } = useApiData(() => adminApi.plans(), []);
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<Plan | null>(null);
  const [saving, setSaving] = React.useState(false);
  const [form, setForm] = React.useState({
    code: "",
    name: "",
    tagline: "",
    price: 0,
    billing_cycle: "year",
    max_users: 1,
    max_quotes: 20,
    ai_quota: 100,
    storage_quota_mb: 200,
    features: ["quotes", "ai"] as string[],
    description: "",
    is_public: true,
    sort_order: 100,
  });
  function openCreate() {
    setEditing(null);
    setForm({
      code: "",
      name: "",
      tagline: "",
      price: 0,
      billing_cycle: "year",
      max_users: 1,
      max_quotes: 20,
      ai_quota: 100,
      storage_quota_mb: 200,
      features: ["quotes", "ai"],
      description: "",
      is_public: true,
      sort_order: 100,
    });
    setDialogOpen(true);
  }
  function openEdit(plan: Plan) {
    setEditing(plan);
    setForm({
      code: plan.code,
      name: plan.name,
      tagline: plan.tagline ?? "",
      price: plan.price,
      billing_cycle: plan.billing_cycle,
      max_users: plan.max_users,
      max_quotes: plan.max_quotes,
      ai_quota: plan.ai_quota,
      storage_quota_mb: plan.storage_quota_mb,
      features: plan.features ?? [],
      description: plan.description ?? "",
      is_public: true,
      sort_order: 100,
    });
    setDialogOpen(true);
  }
  async function save() {
    if (!form.name.trim() || (!editing && !form.code.trim())) {
      toast.error("请填写套餐名称与代码");
      return;
    }
    setSaving(true);
    try {
      if (editing) {
        await adminApi.updatePlan(editing.id, form);
        toast.success("套餐已更新");
      } else {
        await adminApi.createPlan(form);
        toast.success("套餐已创建");
      }
      setDialogOpen(false);
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
        title="套餐管理"
        description="套餐完全由数据库驱动，新增套餐不需要改代码"
        actions={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" />
            新增套餐
          </Button>
        }
      />
      <Card>
        <CardContent className="pt-5">
          {loading ? (
            <SkeletonRows rows={4} />
          ) : error ? (
            <ErrorState message={error} onRetry={reload} />
          ) : !data?.length ? (
            <EmptyState icon={<Layers className="h-5 w-5" />} title="暂无套餐" />
          ) : (
            <Table>
              <THead>
                <Th>套餐</Th>
                <Th>代码</Th>
                <Th className="text-right">价格</Th>
                <Th className="text-right">报价额度</Th>
                <Th className="text-right">AI 额度</Th>
                <Th className="text-right">成员</Th>
                <Th className="text-right">使用企业</Th>
                <Th />
              </THead>
              <TBody>
                {data.map((plan) => (
                  <Tr key={plan.id}>
                    <Td>
                      <p className="font-medium text-ink">{plan.name}</p>
                      <p className="mt-0.5 text-[11.5px] text-faint">{plan.tagline ?? plan.description ?? ""}</p>
                    </Td>
                    <Td>
                      <Badge tone="neutral">{plan.code}</Badge>
                    </Td>
                    <Td className="text-right tabular-nums text-ink">
                      {formatCurrency(plan.price)}
                      <span className="ml-1 text-[11.5px] text-faint">
                        {plan.billing_cycle === "year" ? "/年" : plan.billing_cycle === "month" ? "/月" : ""}
                      </span>
                    </Td>
                    <Td className="text-right tabular-nums">{plan.max_quotes === 0 ? "不限" : plan.max_quotes}</Td>
                    <Td className="text-right tabular-nums">{plan.ai_quota}</Td>
                    <Td className="text-right tabular-nums">{plan.max_users}</Td>
                    <Td className="text-right tabular-nums text-muted">{plan.company_count ?? 0}</Td>
                    <Td className="text-right">
                      <Button variant="ghost" size="sm" onClick={() => openEdit(plan)}>
                        <Pencil className="h-3.5 w-3.5" />
                        编辑
                      </Button>
                    </Td>
                  </Tr>
                ))}
              </TBody>
            </Table>
          )}
        </CardContent>
      </Card>
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title={editing ? "编辑套餐" : "新增套餐"}
        size="lg"
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
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <Field label="套餐名称" required>
            <Input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="例如 专业版" />
          </Field>
          <Field label="套餐代码" required hint="唯一标识，例如 pro">
            <Input value={form.code} disabled={Boolean(editing)} onChange={(event) => setForm({ ...form, code: event.target.value })} />
          </Field>
          <Field label="一句话卖点">
            <Input value={form.tagline} onChange={(event) => setForm({ ...form, tagline: event.target.value })} />
          </Field>
          <Field label="价格（元）">
            <Input type="number" step="0.01" value={form.price} onChange={(event) => setForm({ ...form, price: Number(event.target.value) })} />
          </Field>
          <Field label="计费周期">
            <select
              value={form.billing_cycle}
              onChange={(event) => setForm({ ...form, billing_cycle: event.target.value })}
              className="h-10 w-full rounded-xl border border-line-strong bg-surface px-3 text-[14px]"
            >
              <option value="month">按月</option>
              <option value="year">按年</option>
              <option value="forever">永久</option>
            </select>
          </Field>
          <Field label="排序">
            <Input
              type="number"
              value={form.sort_order}
              onChange={(event) => setForm({ ...form, sort_order: Number(event.target.value) })}
            />
          </Field>
          <Field label="每月报价数量" hint="0 表示不限">
            <Input
              type="number"
              value={form.max_quotes}
              onChange={(event) => setForm({ ...form, max_quotes: Number(event.target.value) })}
            />
          </Field>
          <Field label="每月 AI 额度">
            <Input type="number" value={form.ai_quota} onChange={(event) => setForm({ ...form, ai_quota: Number(event.target.value) })} />
          </Field>
          <Field label="成员账号数">
            <Input type="number" value={form.max_users} onChange={(event) => setForm({ ...form, max_users: Number(event.target.value) })} />
          </Field>
          <Field label="存储额度（MB）">
            <Input
              type="number"
              value={form.storage_quota_mb}
              onChange={(event) => setForm({ ...form, storage_quota_mb: Number(event.target.value) })}
            />
          </Field>
          <Field label="说明" className="sm:col-span-2 xl:col-span-3">
            <Input value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
          </Field>
          <div className="sm:col-span-2 xl:col-span-3">
            <p className="mb-2 text-[13px] font-medium text-ink-soft">包含功能</p>
            <div className="flex flex-wrap gap-x-5 gap-y-2">
              {FEATURES.map((feature) => (
                <label key={feature.key} className="flex items-center gap-2 text-[13px] text-ink-soft">
                  <input
                    type="checkbox"
                    checked={form.features.includes(feature.key)}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        features: event.target.checked
                          ? [...form.features, feature.key]
                          : form.features.filter((item) => item !== feature.key),
                      })
                    }
                    className="h-4 w-4 accent-[#635BFF]"
                  />
                  {feature.label}
                </label>
              ))}
            </div>
          </div>
        </div>
      </Dialog>
    </div>
  );
}

