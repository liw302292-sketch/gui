"use client";
import { ArrowLeft, FolderTree, Pencil, Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import * as React from "react";
import { PageHeader } from "@/components/app/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ConfirmDialog, Dialog } from "@/components/ui/dialog";
import { Field, Input, Textarea } from "@/components/ui/input";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/states";
import { Table, TBody, Td, Th, THead, Tr } from "@/components/ui/table";
import { toast } from "@/components/ui/toast";
import { useApiData } from "@/hooks/use-api";
import { errorMessage, productApi } from "@/lib/api";
import type { Category } from "@/lib/types";
export default function CategoriesPage() {
  const { data, loading, error, reload } = useApiData(() => productApi.categories(), []);
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<Category | null>(null);
  const [deleteTarget, setDeleteTarget] = React.useState<Category | null>(null);
  const [saving, setSaving] = React.useState(false);
  const [form, setForm] = React.useState({ name: "", code: "", description: "", sort_order: 0 });
  function openCreate() {
    setEditing(null);
    setForm({ name: "", code: "", description: "", sort_order: (data?.length ?? 0) + 1 });
    setDialogOpen(true);
  }
  function openEdit(category: Category) {
    setEditing(category);
    setForm({
      name: category.name,
      code: category.code ?? "",
      description: category.description ?? "",
      sort_order: category.sort_order,
    });
    setDialogOpen(true);
  }
  async function save() {
    if (!form.name.trim()) {
      toast.error("请填写分类名称");
      return;
    }
    setSaving(true);
    try {
      const payload = { ...form, name: form.name.trim(), code: form.code || null, description: form.description || null };
      if (editing) {
        await productApi.updateCategory(editing.id, payload);
        toast.success("分类已更新");
      } else {
        await productApi.createCategory(payload);
        toast.success("分类已创建");
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
      await productApi.removeCategory(deleteTarget.id);
      toast.success("分类已删除");
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
        title="产品分类"
        description="分类用于组织价格库，也可以绑定分类级价格规则"
        breadcrumb={
          <Link href="/app/products" className="inline-flex items-center gap-1 hover:text-ink">
            <ArrowLeft className="h-3.5 w-3.5" />
            返回产品列表
          </Link>
        }
        actions={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" />
            新增分类
          </Button>
        }
      />
      <Card>
        <CardContent className="pt-5">
          {loading ? (
            <SkeletonRows rows={5} />
          ) : error ? (
            <ErrorState message={error} onRetry={reload} />
          ) : !data?.length ? (
            <EmptyState
              icon={<FolderTree className="h-5 w-5" />}
              title="暂无分类"
              description="新增分类后，产品可以归入对应分类。"
              action={
                <Button onClick={openCreate}>
                  <Plus className="h-4 w-4" />
                  新增分类
                </Button>
              }
            />
          ) : (
            <Table>
              <THead>
                <Th>分类名称</Th>
                <Th>编码</Th>
                <Th>说明</Th>
                <Th className="text-right">产品数量</Th>
                <Th>排序</Th>
                <Th />
              </THead>
              <TBody>
                {data.map((category) => (
                  <Tr key={category.id}>
                    <Td className="font-medium text-ink">{category.name}</Td>
                    <Td className="font-mono text-[12px] text-muted">{category.code ?? "—"}</Td>
                    <Td className="text-[12.5px] text-muted">{category.description ?? "—"}</Td>
                    <Td className="text-right">
                      <Badge tone={category.product_count ? "accent" : "neutral"}>{category.product_count}</Badge>
                    </Td>
                    <Td className="tabular-nums text-muted">{category.sort_order}</Td>
                    <Td>
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="iconSm" onClick={() => openEdit(category)} aria-label="编辑">
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        <Button variant="ghost" size="iconSm" onClick={() => setDeleteTarget(category)} aria-label="删除">
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
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title={editing ? "编辑分类" : "新增分类"}
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
          <Field label="分类名称" required>
            <Input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="例如 门头" />
          </Field>
          <Field label="编码（可选）">
            <Input value={form.code} onChange={(event) => setForm({ ...form, code: event.target.value })} placeholder="door" />
          </Field>
          <Field label="排序" hint="数字越小越靠前">
            <Input
              type="number"
              value={form.sort_order}
              onChange={(event) => setForm({ ...form, sort_order: Number(event.target.value) })}
            />
          </Field>
          <Field label="说明">
            <Textarea value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
          </Field>
        </div>
      </Dialog>
      <ConfirmDialog
        open={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        title="确认删除分类？"
        description="分类下还有产品时无法删除。"
        confirmText="删除"
        danger
        loading={saving}
        onConfirm={() => void remove()}
      />
    </div>
  );
}

