"use client";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import * as React from "react";
import { PageHeader } from "@/components/app/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input, Select } from "@/components/ui/input";
import { InlineAlert } from "@/components/ui/states";
import { toast } from "@/components/ui/toast";
import { errorMessage, productApi, quoteApi } from "@/lib/api";
import type { Product } from "@/lib/types";
interface ManualItem {
  product_id: number | null;
  product_name: string;
  category: string | null;
  unit: string;
  quantity: number;
  width: number | null;
  height: number | null;
  unit_price: number | null;
}
const UNITS = ["平方米", "米", "个", "套", "张", "块", "项", "公斤", "件", "车"];
const emptyItem = (): ManualItem => ({
  product_id: null,
  product_name: "",
  category: null,
  unit: "平方米",
  quantity: 1,
  width: null,
  height: null,
  unit_price: null,
});
export default function ManualQuotePage() {
  const router = useRouter();
  const [products, setProducts] = React.useState<Product[]>([]);
  const [projectName, setProjectName] = React.useState("");
  const [customerName, setCustomerName] = React.useState("");
  const [items, setItems] = React.useState<ManualItem[]>([emptyItem()]);
  const [creating, setCreating] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  React.useEffect(() => {
    productApi
      .list({ page_size: 200 })
      .then((data) => setProducts(data.items))
      .catch(() => setProducts([]));
  }, []);
  function update(index: number, patch: Partial<ManualItem>) {
    setItems((prev) => prev.map((item, itemIndex) => (itemIndex === index ? { ...item, ...patch } : item)));
  }
  function selectProduct(index: number, productId: string) {
    const product = products.find((item) => item.id === Number(productId));
    if (!product) {
      update(index, { product_id: null });
      return;
    }
    update(index, {
      product_id: product.id,
      product_name: product.name,
      category: product.category_name,
      unit: product.unit,
      unit_price: product.default_price,
    });
  }
  async function submit() {
    if (!projectName.trim()) {
      setError("请填写项目名称");
      return;
    }
    const valid = items.filter((item) => item.product_name.trim() && item.quantity > 0);
    if (!valid.length) {
      setError("请至少添加一个报价项目");
      return;
    }
    setCreating(true);
    setError(null);
    try {
      const quote = await quoteApi.create({
        project_name: projectName.trim(),
        customer_name: customerName.trim() || null,
        items: valid.map((item) => ({
          product_id: item.product_id,
          product_name: item.product_name,
          category: item.category,
          unit: item.unit,
          quantity: item.quantity,
          width: item.width,
          height: item.height,
          unit_price: item.unit_price,
        })),
      });
      toast.success("报价已生成：" + quote.quote_no);
      router.push("/app/quotes/" + quote.id);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setCreating(false);
    }
  }
  return (
    <div>
      <PageHeader
        title="手动创建报价"
        description="不经过 AI，直接从价格库挑选产品并计算"
        breadcrumb={
          <Link href="/app/quotes/new" className="inline-flex items-center gap-1 hover:text-ink">
            <ArrowLeft className="h-3.5 w-3.5" />
            返回 AI 识别
          </Link>
        }
      />
      {error ? (
        <div className="mb-4">
          <InlineAlert tone="danger" title={error} />
        </div>
      ) : null}
      <div className="grid gap-4 xl:grid-cols-[1.6fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>报价项目</CardTitle>
            <Button variant="ghost" size="sm" onClick={() => setItems((prev) => [...prev, emptyItem()])}>
              <Plus className="h-3.5 w-3.5" />
              添加一行
            </Button>
          </CardHeader>
          <CardContent className="space-y-3">
            {items.map((item, index) => (
              <div key={index} className="rounded-[14px] border border-line bg-surface-2/60 p-4">
                <div className="flex items-center justify-between">
                  <span className="text-[12.5px] text-faint">第 {index + 1} 项</span>
                  <Button
                    variant="ghost"
                    size="iconSm"
                    onClick={() => setItems((prev) => prev.filter((_, itemIndex) => itemIndex !== index))}
                    aria-label="删除"
                  >
                    <Trash2 className="h-3.5 w-3.5 text-danger" />
                  </Button>
                </div>
                <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  <Field label="从价格库选择" className="sm:col-span-2 xl:col-span-3">
                    <Select value={item.product_id ?? ""} onChange={(event) => selectProduct(index, event.target.value)}>
                      <option value="">— 手动填写 —</option>
                      {products.map((product) => (
                        <option key={product.id} value={product.id}>
                          {(product.category_name ? product.category_name + " / " : "") + product.name} · {product.unit} · ¥
                          {product.default_price}
                        </option>
                      ))}
                    </Select>
                  </Field>
                  <Field label="产品名称">
                    <Input value={item.product_name} onChange={(event) => update(index, { product_name: event.target.value })} />
                  </Field>
                  <Field label="数量">
                    <Input
                      type="number"
                      step="0.01"
                      value={item.quantity}
                      onChange={(event) => update(index, { quantity: Number(event.target.value) })}
                    />
                  </Field>
                  <Field label="单位">
                    <Select value={item.unit} onChange={(event) => update(index, { unit: event.target.value })}>
                      {UNITS.map((unit) => (
                        <option key={unit} value={unit}>
                          {unit}
                        </option>
                      ))}
                    </Select>
                  </Field>
                  <Field label="宽度（米）">
                    <Input
                      type="number"
                      step="0.01"
                      value={item.width ?? ""}
                      onChange={(event) => update(index, { width: event.target.value === "" ? null : Number(event.target.value) })}
                    />
                  </Field>
                  <Field label="高度（米）">
                    <Input
                      type="number"
                      step="0.01"
                      value={item.height ?? ""}
                      onChange={(event) => update(index, { height: event.target.value === "" ? null : Number(event.target.value) })}
                    />
                  </Field>
                  <Field label="指定单价（可选）" hint="留空使用价格库默认报价">
                    <Input
                      type="number"
                      step="0.01"
                      value={item.unit_price ?? ""}
                      onChange={(event) => update(index, { unit_price: event.target.value === "" ? null : Number(event.target.value) })}
                    />
                  </Field>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>项目信息</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Field label="项目名称" required>
                <Input value={projectName} onChange={(event) => setProjectName(event.target.value)} placeholder="例如：XX餐饮门头制作" />
              </Field>
              <Field label="客户名称" hint="填写后会自动创建客户档案">
                <Input value={customerName} onChange={(event) => setCustomerName(event.target.value)} placeholder="例如：XX餐饮" />
              </Field>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-5">
              <div className="rounded-xl bg-surface-2 p-3.5 text-[12.5px] text-muted">
                提交后系统会按价格库匹配产品，并由规则引擎计算成本、损耗、人工、运输与最终售价。
              </div>
              <Button className="mt-4 w-full" size="lg" loading={creating} onClick={() => void submit()}>
                生成报价单
              </Button>
              <p className="mt-3 text-center text-[12px] text-faint">共 {products.length} 个产品可选</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

