"use client";
import { Download, Package, Pencil, Plus, Search, Trash2, Upload } from "lucide-react";
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
import { errorMessage, productApi } from "@/lib/api";
import type { Category, Product } from "@/lib/types";
import { formatCurrency, formatPercent } from "@/lib/utils";
const PRICING_MODES = [
  { value: "area", label: "面积计价" },
  { value: "fixed", label: "固定单价" },
  { value: "volume", label: "体积计价" },
  { value: "weight", label: "重量计价" },
  { value: "cost_plus", label: "成本加成" },
  { value: "margin", label: "毛利率" },
];
const UNITS = ["平方米", "米", "个", "套", "张", "块", "项", "公斤", "件", "车"];
const emptyForm = {
  name: "",
  category_id: "",
  unit: "平方米",
  pricing_mode: "area",
  spec: "",
  model: "",
  cost_price: 0,
  default_price: 0,
  loss_rate: 0.05,
  labor_cost: 0,
  labor_price_per_unit: 0,
  transport_cost: 0,
  min_profit_margin: 0.25,
  markup_rate: 0.35,
  remark: "",
};
export default function ProductsPage() {
  const [keyword, setKeyword] = React.useState("");
  const [search, setSearch] = React.useState("");
  const [categoryId, setCategoryId] = React.useState("");
  const [page, setPage] = React.useState(1);
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<Product | null>(null);
  const [deleteTarget, setDeleteTarget] = React.useState<Product | null>(null);
  const [saving, setSaving] = React.useState(false);
  const [importing, setImporting] = React.useState(false);
  const [form, setForm] = React.useState({ ...emptyForm });
  const fileRef = React.useRef<HTMLInputElement>(null);
  const categories = useApiData(() => productApi.categories(), []);
  React.useEffect(() => {
    const timer = window.setTimeout(() => {
      setSearch(keyword.trim());
      setPage(1);
    }, 300);
    return () => window.clearTimeout(timer);
  }, [keyword]);
  const { data, loading, error, reload } = useApiData(
    () =>
      productApi.list({
        keyword: search || undefined,
        category_id: categoryId || undefined,
        page,
        page_size: 20,
      }),
    [search, categoryId, page],
  );
  function openCreate() {
    setEditing(null);
    setForm({ ...emptyForm, category_id: categories.data?.[0] ? String(categories.data[0].id) : "" });
    setDialogOpen(true);
  }
  function openEdit(product: Product) {
    setEditing(product);
    setForm({
      name: product.name,
      category_id: product.category_id ? String(product.category_id) : "",
      unit: product.unit,
      pricing_mode: product.pricing_mode,
      spec: product.spec ?? "",
      model: product.model ?? "",
      cost_price: product.cost_price,
      default_price: product.default_price,
      loss_rate: product.loss_rate,
      labor_cost: product.labor_cost,
      labor_price_per_unit: product.labor_price_per_unit,
      transport_cost: product.transport_cost,
      min_profit_margin: product.min_profit_margin,
      markup_rate: product.markup_rate,
      remark: product.remark ?? "",
    });
    setDialogOpen(true);
  }
  async function save() {
    if (!form.name.trim()) {
      toast.error("请填写产品名称");
      return;
    }
    setSaving(true);
    const payload = {
      ...form,
      name: form.name.trim(),
      category_id: form.category_id ? Number(form.category_id) : null,
      spec: form.spec || null,
      model: form.model || null,
      remark: form.remark || null,
    };
    try {
      if (editing) {
        await productApi.update(editing.id, payload);
        toast.success("产品已更新");
      } else {
        await productApi.create(payload);
        toast.success("产品已创建");
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
    setSaving(true);
    try {
      await productApi.remove(deleteTarget.id);
      toast.success("产品已删除");
      setDeleteTarget(null);
      reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }
  async function importFile(file: File | undefined) {
    if (!file) return;
    setImporting(true);
    try {
      const result = await productApi.importFile(file);
      toast.success("导入完成：新增 " + result.created + " 个，更新 " + result.updated + " 个");
      reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setImporting(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }
  const totalPages = data ? Math.max(Math.ceil(data.total / data.page_size), 1) : 1;
  return (
    <div>
      <PageHeader
        title="产品与价格"
        description="你企业的价格库，报价引擎只按这里的数据计算"
        actions={
          <>
            <input
              ref={fileRef}
              type="file"
              accept=".xlsx,.xls,.csv"
              className="hidden"
              onChange={(event) => void importFile(event.target.files?.[0])}
            />
            <Button variant="secondary" loading={importing} onClick={() => fileRef.current?.click()}>
              <Upload className="h-4 w-4" />
              Excel 导入
            </Button>
            <Link href="/app/products/categories">
              <Button variant="secondary">分类管理</Button>
            </Link>
            <Button onClick={openCreate}>
              <Plus className="h-4 w-4" />
              新增产品
            </Button>
          </>
        }
      />
      <InlineAlert tone="info" title="预置产品只是演示数据，不代表行业统一价格">
        请按你自己的实际成本与报价修改，或直接 Excel 导入现有价格表。列名支持：分类、产品名称、单位、计价方式、成本、默认报价、损耗率、人工单价、最低利润率。
      </InlineAlert>
      <Card className="mt-5">
        <CardContent className="pt-5">
          <div className="flex flex-wrap items-center gap-3">
            <Select
              value={categoryId}
              onChange={(event) => {
                setCategoryId(event.target.value);
                setPage(1);
              }}
              className="w-40"
            >
              <option value="">全部分类</option>
              {(categories.data ?? []).map((category: Category) => (
                <option key={category.id} value={category.id}>
                  {category.name}（{category.product_count}）
                </option>
              ))}
            </Select>
            <div className="relative ml-auto">
              <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-faint" />
              <Input
                value={keyword}
                onChange={(event) => setKeyword(event.target.value)}
                placeholder="搜索产品名称 / 型号"
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
                icon={<Package className="h-5 w-5" />}
                title="暂无产品"
                description="新增产品或 Excel 导入你现有的价格表。"
                action={
                  <Button onClick={openCreate}>
                    <Plus className="h-4 w-4" />
                    新增产品
                  </Button>
                }
              />
            ) : (
              <>
                <Table>
                  <THead>
                    <Th>产品</Th>
                    <Th>分类</Th>
                    <Th>计价方式</Th>
                    <Th className="text-right">成本</Th>
                    <Th className="text-right">默认报价</Th>
                    <Th className="text-right">损耗率</Th>
                    <Th className="text-right">毛利率</Th>
                    <Th />
                  </THead>
                  <TBody>
                    {data.items.map((product) => (
                      <Tr key={product.id}>
                        <Td>
                          <p className="font-medium text-ink">{product.name}</p>
                          <p className="mt-0.5 text-[12px] text-faint">{product.spec ?? product.unit}</p>
                        </Td>
                        <Td className="text-[12.5px] text-muted">{product.category_name ?? "—"}</Td>
                        <Td>
                          <Badge tone="neutral">
                            {PRICING_MODES.find((mode) => mode.value === product.pricing_mode)?.label ?? product.pricing_mode}
                          </Badge>
                        </Td>
                        <Td className="text-right tabular-nums text-muted">{formatCurrency(product.cost_price)}</Td>
                        <Td className="text-right font-medium tabular-nums text-ink">
                          {formatCurrency(product.default_price)}
                          <span className="ml-1 text-[11.5px] font-normal text-faint">/{product.unit}</span>
                        </Td>
                        <Td className="text-right tabular-nums text-muted">{formatPercent(product.loss_rate)}</Td>
                        <Td className="text-right tabular-nums text-success">{formatPercent(product.gross_margin_preview)}</Td>
                        <Td>
                          <div className="flex justify-end gap-1">
                            <Button variant="ghost" size="iconSm" onClick={() => openEdit(product)} aria-label="编辑">
                              <Pencil className="h-3.5 w-3.5" />
                            </Button>
                            <Button variant="ghost" size="iconSm" onClick={() => setDeleteTarget(product)} aria-label="删除">
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
                      共 {data.total} 个产品，第 {page} / {totalPages} 页
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
        title={editing ? "编辑产品" : "新增产品"}
        description="成本与报价直接决定最终报价结果"
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
          <Field label="产品名称" required className="sm:col-span-2">
            <Input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="例如 铝塑板门头" />
          </Field>
          <Field label="分类">
            <Select value={form.category_id} onChange={(event) => setForm({ ...form, category_id: event.target.value })}>
              <option value="">未分类</option>
              {(categories.data ?? []).map((category: Category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="规格">
            <Input value={form.spec} onChange={(event) => setForm({ ...form, spec: event.target.value })} placeholder="4mm 铝塑板 + 方管骨架" />
          </Field>
          <Field label="单位">
            <Select value={form.unit} onChange={(event) => setForm({ ...form, unit: event.target.value })}>
              {UNITS.map((unit) => (
                <option key={unit} value={unit}>
                  {unit}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="计价方式">
            <Select value={form.pricing_mode} onChange={(event) => setForm({ ...form, pricing_mode: event.target.value })}>
              {PRICING_MODES.map((mode) => (
                <option key={mode.value} value={mode.value}>
                  {mode.label}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="成本单价（元）">
            <Input type="number" step="0.01" value={form.cost_price} onChange={(event) => setForm({ ...form, cost_price: Number(event.target.value) })} />
          </Field>
          <Field label="默认报价（元）">
            <Input type="number" step="0.01" value={form.default_price} onChange={(event) => setForm({ ...form, default_price: Number(event.target.value) })} />
          </Field>
          <Field label="损耗率" hint="0.06 表示 6%">
            <Input type="number" step="0.01" value={form.loss_rate} onChange={(event) => setForm({ ...form, loss_rate: Number(event.target.value) })} />
          </Field>
          <Field label="固定人工费（元）">
            <Input type="number" step="0.01" value={form.labor_cost} onChange={(event) => setForm({ ...form, labor_cost: Number(event.target.value) })} />
          </Field>
          <Field label="人工单价（元 / 计价单位）">
            <Input
              type="number"
              step="0.01"
              value={form.labor_price_per_unit}
              onChange={(event) => setForm({ ...form, labor_price_per_unit: Number(event.target.value) })}
            />
          </Field>
          <Field label="运输费（元）">
            <Input type="number" step="0.01" value={form.transport_cost} onChange={(event) => setForm({ ...form, transport_cost: Number(event.target.value) })} />
          </Field>
          <Field label="最低利润率" hint="0.25 表示保底 25%">
            <Input
              type="number"
              step="0.01"
              value={form.min_profit_margin}
              onChange={(event) => setForm({ ...form, min_profit_margin: Number(event.target.value) })}
            />
          </Field>
          <Field label="成本加成率" hint="0.35 表示成本 × 1.35">
            <Input type="number" step="0.01" value={form.markup_rate} onChange={(event) => setForm({ ...form, markup_rate: Number(event.target.value) })} />
          </Field>
          <Field label="备注" className="sm:col-span-2 xl:col-span-3">
            <Textarea value={form.remark} onChange={(event) => setForm({ ...form, remark: event.target.value })} />
          </Field>
        </div>
        <div className="mt-4 rounded-xl bg-surface-2 p-3.5 text-[12.5px] text-muted">
          预览：若按 1 {form.unit} 计算，材料成本 {formatCurrency(form.cost_price)}，含损耗后约{" "}
          {formatCurrency(form.cost_price * (1 + form.loss_rate))}，保底售价约{" "}
          {formatCurrency(form.min_profit_margin < 1 ? (form.cost_price * (1 + form.loss_rate)) / (1 - form.min_profit_margin) : 0)}
        </div>
      </Dialog>
      <ConfirmDialog
        open={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        title="确认删除产品？"
        description="已经绑定价格规则的产品需要先删除规则。"
        confirmText="删除"
        danger
        loading={saving}
        onConfirm={() => void remove()}
      />
      <p className="mt-4 flex items-center gap-1.5 text-[12px] text-faint">
        <Download className="h-3.5 w-3.5" />
        提示：Excel 导入时会按「产品名称」自动判断新增或更新。
      </p>
    </div>
  );
}

