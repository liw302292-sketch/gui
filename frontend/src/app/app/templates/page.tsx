"use client";
import { Check, Pencil, Plus, Star, Tags, Trash2 } from "lucide-react";
import * as React from "react";
import { PageHeader } from "@/components/app/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ConfirmDialog, Dialog } from "@/components/ui/dialog";
import { Field, Input, Textarea } from "@/components/ui/input";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/states";
import { toast } from "@/components/ui/toast";
import { useApiData } from "@/hooks/use-api";
import { errorMessage, quoteTemplateApi } from "@/lib/api";
import type { QuoteTemplate } from "@/lib/types";
const COLORS = ["#635BFF", "#12A150", "#111827", "#D97706", "#DC2626", "#2563EB"];
export default function TemplatesPage() {
  const { data, loading, error, reload } = useApiData(() => quoteTemplateApi.list(), []);
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<QuoteTemplate | null>(null);
  const [deleteTarget, setDeleteTarget] = React.useState<QuoteTemplate | null>(null);
  const [saving, setSaving] = React.useState(false);
  const [form, setForm] = React.useState({
    name: "",
    accent_color: "#635BFF",
    show_tiers: true,
    show_unit_price: true,
    payment_terms: "",
    service_terms: "",
    footer: "",
    is_default: false,
  });
  function openCreate() {
    setEditing(null);
    setForm({
      name: "",
      accent_color: "#635BFF",
      show_tiers: true,
      show_unit_price: true,
      payment_terms: "",
      service_terms: "",
      footer: "",
      is_default: false,
    });
    setDialogOpen(true);
  }
  function openEdit(template: QuoteTemplate) {
    setEditing(template);
    setForm({
      name: template.name,
      accent_color: template.accent_color,
      show_tiers: template.show_tiers,
      show_unit_price: template.show_unit_price,
      payment_terms: template.payment_terms ?? "",
      service_terms: template.service_terms ?? "",
      footer: template.footer ?? "",
      is_default: template.is_default,
    });
    setDialogOpen(true);
  }
  async function save() {
    if (!form.name.trim()) {
      toast.error("请填写模板名称");
      return;
    }
    setSaving(true);
    try {
      const payload = {
        ...form,
        name: form.name.trim(),
        payment_terms: form.payment_terms || null,
        service_terms: form.service_terms || null,
        footer: form.footer || null,
      };
      if (editing) {
        await quoteTemplateApi.update(editing.id, payload);
        toast.success("模板已更新");
      } else {
        await quoteTemplateApi.create(payload);
        toast.success("模板已创建");
      }
      setDialogOpen(false);
      reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }
  async function setDefault(template: QuoteTemplate) {
    try {
      await quoteTemplateApi.update(template.id, { is_default: true });
      toast.success("已设为默认模板");
      reload();
    } catch (err) {
      toast.error(errorMessage(err));
    }
  }
  async function remove() {
    if (!deleteTarget) return;
    setSaving(true);
    try {
      await quoteTemplateApi.remove(deleteTarget.id);
      toast.success("模板已删除");
      setDeleteTarget(null);
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
        title="报价模板"
        description="报价单的样式、付款条款与服务条款，新建报价时自动套用默认模板"
        actions={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" />
            新增模板
          </Button>
        }
      />
      {loading ? (
        <SkeletonRows rows={3} />
      ) : error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : !data?.length ? (
        <EmptyState
          icon={<Tags className="h-5 w-5" />}
          title="暂无报价模板"
          description="创建模板后，新建报价会自动带上条款与页脚。"
          action={
            <Button onClick={openCreate}>
              <Plus className="h-4 w-4" />
              新增模板
            </Button>
          }
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {data.map((template) => (
            <Card key={template.id}>
              <CardContent className="pt-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <span className="h-8 w-8 rounded-xl border border-line" style={{ background: template.accent_color }} />
                    <div>
                      <p className="text-[14px] font-medium text-ink">{template.name}</p>
                      <p className="text-[11.5px] text-faint">
                        {template.layout?.layout === "classic" ? "经典版式" : "自定义版式"}
                      </p>
                    </div>
                  </div>
                  {template.is_default ? (
                    <Badge tone="accent">
                      <Star className="h-3 w-3" />
                      默认
                    </Badge>
                  ) : null}
                </div>
                <div className="mt-4 space-y-1.5 text-[12.5px]">
                  <Feature enabled={template.show_tiers} label="显示经济/标准/高级三档方案" />
                  <Feature enabled={template.show_unit_price} label="显示单价列" />
                  <Feature enabled={Boolean(template.payment_terms)} label="包含付款条款" />
                  <Feature enabled={Boolean(template.service_terms)} label="包含服务条款" />
                </div>
                {template.payment_terms ? (
                  <p className="mt-3 line-clamp-2 rounded-xl bg-surface-2 p-2.5 text-[12px] text-muted">
                    {template.payment_terms}
                  </p>
                ) : null}
                <div className="mt-4 flex flex-wrap gap-2">
                  <Button variant="secondary" size="sm" onClick={() => openEdit(template)}>
                    <Pencil className="h-3.5 w-3.5" />
                    编辑
                  </Button>
                  {!template.is_default ? (
                    <Button variant="ghost" size="sm" onClick={() => void setDefault(template)}>
                      设为默认
                    </Button>
                  ) : null}
                  <Button variant="dangerGhost" size="sm" onClick={() => setDeleteTarget(template)}>
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title={editing ? "编辑报价模板" : "新增报价模板"}
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
          <Field label="模板名称" required>
            <Input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="例如 广告标识标准报价模板" />
          </Field>
          <Field label="主色">
            <div className="flex flex-wrap gap-2">
              {COLORS.map((color) => (
                <button
                  key={color}
                  type="button"
                  onClick={() => setForm({ ...form, accent_color: color })}
                  className={
                    "h-8 w-8 rounded-xl border transition-transform " +
                    (form.accent_color === color ? "scale-110 border-ink" : "border-line")
                  }
                  style={{ background: color }}
                  aria-label={color}
                />
              ))}
            </div>
          </Field>
          <div className="flex flex-wrap gap-5">
            <label className="flex items-center gap-2 text-[13px] text-ink-soft">
              <input
                type="checkbox"
                checked={form.show_tiers}
                onChange={(event) => setForm({ ...form, show_tiers: event.target.checked })}
                className="h-4 w-4 accent-[#635BFF]"
              />
              显示三档方案
            </label>
            <label className="flex items-center gap-2 text-[13px] text-ink-soft">
              <input
                type="checkbox"
                checked={form.show_unit_price}
                onChange={(event) => setForm({ ...form, show_unit_price: event.target.checked })}
                className="h-4 w-4 accent-[#635BFF]"
              />
              显示单价列
            </label>
            <label className="flex items-center gap-2 text-[13px] text-ink-soft">
              <input
                type="checkbox"
                checked={form.is_default}
                onChange={(event) => setForm({ ...form, is_default: event.target.checked })}
                className="h-4 w-4 accent-[#635BFF]"
              />
              设为默认模板
            </label>
          </div>
          <Field label="付款条款">
            <Textarea
              value={form.payment_terms}
              onChange={(event) => setForm({ ...form, payment_terms: event.target.value })}
              placeholder="例如：签订合同预付 50%，验收合格后付清余款。"
            />
          </Field>
          <Field label="服务条款">
            <Textarea
              value={form.service_terms}
              onChange={(event) => setForm({ ...form, service_terms: event.target.value })}
              className="min-h-[120px]"
            />
          </Field>
          <Field label="页脚">
            <Input value={form.footer} onChange={(event) => setForm({ ...form, footer: event.target.value })} />
          </Field>
        </div>
      </Dialog>
      <ConfirmDialog
        open={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        title="确认删除该模板？"
        description="默认模板不能删除，请先设置其他模板为默认。"
        confirmText="删除"
        danger
        loading={saving}
        onConfirm={() => void remove()}
      />
    </div>
  );
}
function Feature({ enabled, label }: { enabled: boolean; label: string }) {
  return (
    <div className="flex items-center gap-2">
      {enabled ? (
        <Check className="h-3.5 w-3.5 text-success" />
      ) : (
        <span className="h-3.5 w-3.5 rounded-full border border-line" />
      )}
      <span className={enabled ? "text-ink-soft" : "text-faint"}>{label}</span>
    </div>
  );
}

