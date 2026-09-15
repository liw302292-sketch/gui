"use client";
import { ArrowLeft, Calculator, Pencil, Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import * as React from "react";
import { PageHeader } from "@/components/app/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ConfirmDialog, Dialog } from "@/components/ui/dialog";
import { Field, Input, Select, Textarea } from "@/components/ui/input";
import { EmptyState, ErrorState, InlineAlert, SkeletonRows } from "@/components/ui/states";
import { Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { toast } from "@/components/ui/toast";
import { useApiData } from "@/hooks/use-api";
import { errorMessage, priceRuleApi, productApi } from "@/lib/api";
import type { Category, PriceRule, Product } from "@/lib/types";
const RULE_PARAM_HINTS: Record<string, string> = {
  fixed: '{"unit_price": 100, "cost_price": 40}',
  area: '{"unit_price": 280, "cost_price": 145, "loss_rate": 0.06}',
  volume: '{"unit_price": 1000, "cost_price": 400}',
  weight: '{"unit_price": 8, "cost_price": 5}',
  cost_plus: '{"markup_rate": 0.35}',
  margin: '{"target_margin": 0.3}',
  loss: '{"loss_rate": 0.08}',
  labor: '{"labor_cost": 600, "labor_price_per_unit": 55}',
  transport: '{"transport_cost": 300}',
  condition: '{"unit_price": 245, "min_profit_margin": 0.28}',
  tiered: '{"unit_price": 220}',
};
const CONDITION_HINT = '{"all": [{"field": "area", "op": ">", "value": 20}]}';
export default function PriceRulesPage() {
  const rules = useApiData(() => priceRuleApi.list(), []);
  const types = useApiData(() => priceRuleApi.types(), []);
  const products = useApiData(() => productApi.list({ page_size: 200 }), []);
  const categories = useApiData(() => productApi.categories(), []);
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<PriceRule | null>(null);
  const [deleteTarget, setDeleteTarget] = React.useState<PriceRule | null>(null);
  const [saving, setSaving] = React.useState(false);
  const [form, setForm] = React.useState({
    name: "",
    scope: "category",
    scope_id: "",
    rule_type: "area",
    priority: 100,
    conditions: "",
    params: RULE_PARAM_HINTS.area ?? "{}",
    description: "",
  });
  function openCreate() {
    setEditing(null);
    setForm({
      name: "",
      scope: "category",
      scope_id: categories.data?.[0] ? String(categories.data[0].id) : "",
      rule_type: "area",
      priority: 100,
      conditions: "",
      params: RULE_PARAM_HINTS.area ?? "{}",
      description: "",
    });
    setDialogOpen(true);
  }
  function openEdit(rule: PriceRule) {
    setEditing(rule);
    setForm({
      name: rule.name,
      scope: rule.product_id ? "product" : "category",
      scope_id: String(rule.product_id ?? rule.category_id ?? ""),
      rule_type: rule.rule_type,
      priority: rule.priority,
      conditions: Object.keys(rule.conditions ?? {}).length ? JSON.stringify(rule.conditions) : "",
      params: JSON.stringify(rule.params ?? {}),
      description: rule.description ?? "",
    });
    setDialogOpen(true);
  }
  async function save() {
    if (!form.name.trim()) {
      toast.error("请填写规则名称");
      return;
    }
    let params: Record<string, unknown> = {};
    let conditions: Record<string, unknown> = {};
    try {
      params = form.params.trim() ? JSON.parse(form.params) : {};
    } catch {
      toast.error("参数不是合法 JSON");
      return;
    }
    if (form.conditions.trim()) {
      try {
        conditions = JSON.parse(form.conditions);
      } catch {
        toast.error("条件不是合法 JSON");
        return;
      }
    }
    setSaving(true);
    const payload: Record<string, unknown> = {
      name: form.name.trim(),
      rule_type: form.rule_type,
      priority: form.priority,
      params,
      conditions,
      description: form.description || null,
      product_id: form.scope === "product" && form.scope_id ? Number(form.scope_id) : null,
      category_id: form.scope === "category" && form.scope_id ? Number(form.scope_id) : null,
    };
    try {
      if (editing) {
        await priceRuleApi.update(editing.id, payload);
        toast.success("规则已更新");
      } else {
        await priceRuleApi.create(payload);
        toast.success("规则已创建");
      }
      setDialogOpen(false);
      rules.reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }
  async function remove() {
    if (!deleteTarget) return;
    setSaving(true);
    try {
      await priceRuleApi.remove(deleteTarget.id);
      toast.success("规则已删除");
      setDeleteTarget(null);
      rules.reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }
  return (
    <div>
      <PageHeader
        title="价格规则"
        description="规则引擎按这些规则计算成本与售价，AI 不参与"
        breadcrumb={
          <Link href="/app/products" className="inline-flex items-center gap-1 hover:text-ink">
            <ArrowLeft className="h-3.5 w-3.5" />
            返回产品与价格
          </Link>
        }
        actions={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" />
            新增规则
          </Button>
        }
      />
      <InlineAlert tone="info" title="规则的优先级：产品规则 > 分类规则 > 企业通用规则">
        priority 数字越小越先匹配；条件价格可以写成
        <span className="mx-1 font-mono text-[12px]">{CONDITION_HINT}</span>
        表示面积大于 20㎡ 时使用批发价。
      </InlineAlert>
      <div className="mt-5 grid gap-4 xl:grid-cols-[1.6fr_1fr]">
        <Card>
          <CardContent className="pt-5">
            {rules.loading ? (
              <SkeletonRows rows={5} />
            ) : rules.error ? (
              <ErrorState message={rules.error} onRetry={rules.reload} />
            ) : !rules.data?.length ? (
              <EmptyState
                icon={<Calculator className="h-5 w-5" />}
                title="暂无价格规则"
                description="没有规则时，报价将只使用产品自身的成本与报价。"
                action={
                  <Button onClick={openCreate}>
                    <Plus className="h-4 w-4" />
                    新增规则
                  </Button>
                }
              />
            ) : (
              <Table>
                <THead>
                  <Th>规则名称</Th>
                  <Th>作用范围</Th>
                  <Th>类型</Th>
                  <Th className="text-right">优先级</Th>
                  <Th>条件</Th>
                  <Th />
                </THead>
                <TBody>
                  {rules.data.map((rule) => (
                    <Tr key={rule.id}>
                      <Td>
                        <p className="font-medium text-ink">{rule.name}</p>
                        {rule.description ? <p className="mt-0.5 text-[12px] text-faint">{rule.description}</p> : null}
                      </Td>
                      <Td className="text-[12.5px] text-muted">
                        {rule.product_name ? "产品：" + rule.product_name : rule.category_name ? "分类：" + rule.category_name : "企业通用"}
                      </Td>
                      <Td>
                        <Badge tone="neutral">
                          {types.data?.find((type) => type.value === rule.rule_type)?.label ?? rule.rule_type}
                        </Badge>
                      </Td>
                      <Td className="text-right tabular-nums text-muted">{rule.priority}</Td>
                      <Td className="max-w-[220px] truncate font-mono text-[11.5px] text-faint">
                        {Object.keys(rule.conditions ?? {}).length ? JSON.stringify(rule.conditions) : "无条件"}
                      </Td>
                      <Td>
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="iconSm" onClick={() => openEdit(rule)} aria-label="编辑">
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                          <Button variant="ghost" size="iconSm" onClick={() => setDeleteTarget(rule)} aria-label="删除">
                            <Trash2 className="h-3.5 w-3.5 text-danger" />
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
        <Card>
          <CardContent className="pt-5">
            <p className="text-[13px] font-medium text-ink">支持的规则类型</p>
            <div className="mt-3 space-y-2.5">
              {(types.data ?? []).map((type) => (
                <div key={type.value} className="rounded-xl border border-line bg-surface-2 p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[13px] font-medium text-ink">{type.label}</span>
                    <span className="font-mono text-[11px] text-faint">{type.value}</span>
                  </div>
                  <p className="mt-1 text-[12px] text-muted">{type.formula}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title={editing ? "编辑规则" : "新增规则"}
        description="规则参数使用 JSON，字段名与产品价格字段保持一致"
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
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="规则名称" required className="sm:col-span-2">
            <Input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="例如 门头大面积批发价" />
          </Field>
          <Field label="作用范围">
            <Select value={form.scope} onChange={(event) => setForm({ ...form, scope: event.target.value, scope_id: "" })}>
              <option value="category">按分类</option>
              <option value="product">按产品</option>
            </Select>
          </Field>
          <Field label={form.scope === "product" ? "选择产品" : "选择分类"}>
            <Select value={form.scope_id} onChange={(event) => setForm({ ...form, scope_id: event.target.value })}>
              <option value="">企业通用（不限定）</option>
              {form.scope === "product"
                ? (products.data?.items ?? []).map((product: Product) => (
                    <option key={product.id} value={product.id}>
                      {product.name}
                    </option>
                  ))
                : (categories.data ?? []).map((category: Category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
            </Select>
          </Field>
          <Field label="规则类型">
            <Select
              value={form.rule_type}
              onChange={(event) =>
                setForm({
                  ...form,
                  rule_type: event.target.value,
                  params: RULE_PARAM_HINTS[event.target.value] ?? "{}",
                })
              }
            >
              {(types.data ?? []).map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="优先级" hint="数字越小越先匹配">
            <Input
              type="number"
              value={form.priority}
              onChange={(event) => setForm({ ...form, priority: Number(event.target.value) })}
            />
          </Field>
          <Field label="触发条件（JSON，可选）" className="sm:col-span-2" hint={'例如 {"all":[{"field":"area","op":">","value":20}]}'}>
            <Textarea
              value={form.conditions}
              onChange={(event) => setForm({ ...form, conditions: event.target.value })}
              placeholder={CONDITION_HINT}
              className="min-h-[72px] font-mono text-[12px]"
            />
          </Field>
          <Field label="规则参数（JSON）" className="sm:col-span-2">
            <Textarea
              value={form.params}
              onChange={(event) => setForm({ ...form, params: event.target.value })}
              className="min-h-[90px] font-mono text-[12px]"
            />
          </Field>
          <Field label="说明" className="sm:col-span-2">
            <Input value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
          </Field>
        </div>
      </Dialog>
      <ConfirmDialog
        open={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        title="确认删除该规则？"
        description="删除后新报价将不再应用此规则，历史报价不受影响。"
        confirmText="删除"
        danger
        loading={saving}
        onConfirm={() => void remove()}
      />
    </div>
  );
}

