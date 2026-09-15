"use client";
import { Check, Download, Lock, Phone, Printer, ShieldCheck } from "lucide-react";
import { useParams } from "next/navigation";
import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { EmptyState, ErrorState, PageLoading } from "@/components/ui/states";
import { toast } from "@/components/ui/toast";
import { errorMessage, publicApi } from "@/lib/api";
import type { PublicQuotePayload } from "@/lib/types";
import { cn, formatCurrency, formatDate } from "@/lib/utils";
type Data = PublicQuotePayload["quote"];
export default function PublicQuotePage() {
  const params = useParams<{ token: string }>();
  const token = params.token;
  const [data, setData] = React.useState<Data | null>(null);
  const [requiresPassword, setRequiresPassword] = React.useState(false);
  const [password, setPassword] = React.useState("");
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [accepted, setAccepted] = React.useState(false);
  const [accepting, setAccepting] = React.useState(false);
  const load = React.useCallback(
    async (pwd?: string) => {
      setLoading(true);
      setError(null);
      try {
        const result = await publicApi.view(token, pwd);
        if (result.requires_password) {
          setRequiresPassword(true);
          setData(null);
        } else {
          setRequiresPassword(false);
          setData(result.quote);
        }
      } catch (err) {
        setError(errorMessage(err));
      } finally {
        setLoading(false);
      }
    },
    [token],
  );
  React.useEffect(() => {
    void load();
  }, [load]);
  async function accept() {
    setAccepting(true);
    try {
      const result = (await publicApi.accept(token)) as unknown as { message?: string };
      setAccepted(true);
      toast.success(result?.message ?? "已收到您的确认");
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setAccepting(false);
    }
  }
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <PageLoading label="正在加载报价单…" />
      </div>
    );
  }
  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background p-6">
        <div className="w-full max-w-md">
          <ErrorState message={error} onRetry={() => void load()} />
        </div>
      </div>
    );
  }
  if (requiresPassword) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background p-6">
        <div className="w-full max-w-sm rounded-[20px] border border-line bg-surface p-6 shadow-[var(--shadow-card)]">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-accent-soft text-accent">
            <Lock className="h-5 w-5" />
          </div>
          <h1 className="mt-4 text-[19px] font-semibold tracking-tight text-ink">该报价单已加密</h1>
          <p className="mt-1.5 text-[13px] text-muted">请输入业务员提供的访问密码查看报价内容</p>
          <div className="mt-5">
            <Field label="访问密码">
              <Input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="请输入密码"
                onKeyDown={(event) => {
                  if (event.key === "Enter") void load(password);
                }}
              />
            </Field>
          </div>
          <Button className="mt-4 w-full" loading={loading} onClick={() => void load(password)}>
            查看报价
          </Button>
        </div>
      </div>
    );
  }
  if (!data) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background p-6">
        <EmptyState title="报价单不存在" description="请联系业务员重新获取报价链接。" />
      </div>
    );
  }
  const tiers = ["economy", "standard", "premium"]
    .map((level) => data.tiers?.[level])
    .filter((tier): tier is NonNullable<typeof tier> => Boolean(tier));
  const company = data.company ?? {};
  return (
    <div className="min-h-screen bg-background pb-16">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-4 px-5 py-4">
          <div className="min-w-0">
            <p className="truncate text-[15px] font-semibold text-ink">{company.name ?? "报价单"}</p>
            <p className="mt-0.5 text-[11.5px] text-faint">{company.address ?? ""}</p>
          </div>
          <Badge tone="success">正式报价</Badge>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-6">
        <div className="rounded-[20px] border border-line bg-surface p-5 shadow-[var(--shadow-card)] sm:p-7">
          <div className="flex flex-wrap items-start justify-between gap-4 border-b border-line pb-5">
            <div>
              <p className="text-[12px] uppercase tracking-wider text-faint">报价单号</p>
              <p className="mt-1 font-mono text-[15px] font-semibold text-ink">{data.quote_no}</p>
              <p className="mt-1 text-[12px] text-faint">版本 V{data.version_no}</p>
            </div>
            <div className="text-right text-[12.5px] text-muted">
              <p>报价日期：{formatDate(data.created_at)}</p>
              <p className="mt-1">有效期至：{formatDate(data.valid_until)}</p>
            </div>
          </div>
          <div className="mt-5 grid gap-4 sm:grid-cols-3">
            <Info label="客户" value={data.customer_name ?? "—"} />
            <Info label="项目名称" value={data.project_name} />
            <Info
              label="联系人"
              value={[company.contact_name, company.contact_phone].filter(Boolean).join(" ") || "—"}
            />
          </div>
          <div className="mt-6 overflow-hidden rounded-[14px] border border-line">
            <table className="w-full text-[12.5px]">
              <thead>
                <tr className="bg-surface-2 text-[11.5px] text-muted">
                  <th className="px-4 py-2.5 text-left font-medium">项目</th>
                  <th className="px-4 py-2.5 text-right font-medium">数量</th>
                  <th className="px-4 py-2.5 text-right font-medium">单价</th>
                  <th className="px-4 py-2.5 text-right font-medium">金额</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.id} className="border-t border-line/70">
                    <td className="px-4 py-3">
                      <p className="font-medium text-ink">{item.product_name}</p>
                      <p className="mt-0.5 text-[11.5px] text-faint">
                        {[item.category_name, item.spec, item.width && item.height ? item.width + "m × " + item.height + "m" : null]
                          .filter(Boolean)
                          .join(" · ")}
                      </p>
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-muted">
                      {item.quantity} {item.unit}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-muted">{formatCurrency(item.unit_price)}</td>
                    <td className="px-4 py-3 text-right font-medium tabular-nums text-ink">
                      {formatCurrency(item.final_price)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-5 ml-auto max-w-xs space-y-2 text-[13px]">
            <div className="flex items-center justify-between">
              <span className="text-muted">小计</span>
              <span className="tabular-nums text-ink-soft">{formatCurrency(data.subtotal)}</span>
            </div>
            {data.discount_amount ? (
              <div className="flex items-center justify-between">
                <span className="text-muted">优惠</span>
                <span className="tabular-nums text-ink-soft">-{formatCurrency(data.discount_amount)}</span>
              </div>
            ) : null}
            {data.tax_amount ? (
              <div className="flex items-center justify-between">
                <span className="text-muted">税费</span>
                <span className="tabular-nums text-ink-soft">{formatCurrency(data.tax_amount)}</span>
              </div>
            ) : null}
            <div className="flex items-center justify-between border-t-2 border-ink pt-3">
              <span className="text-[14px] font-medium text-ink">合计</span>
              <span className="text-[22px] font-semibold tabular-nums text-ink">{formatCurrency(data.total_amount)}</span>
            </div>
          </div>
          {tiers.length ? (
            <div className="mt-6">
              <p className="text-[13px] font-medium text-ink">可选方案</p>
              <div className="mt-3 grid gap-3 sm:grid-cols-3">
                {tiers.map((tier) => (
                  <div
                    key={tier.level}
                    className={cn(
                      "rounded-[14px] border p-4",
                      tier.level === "standard" ? "border-accent bg-accent-soft/40" : "border-line bg-surface-2/60",
                    )}
                  >
                    <p className="text-[12px] text-muted">{tier.name}</p>
                    <p className="mt-1.5 text-[17px] font-semibold tabular-nums text-ink">
                      {formatCurrency(tier.total_amount)}
                    </p>
                    {tier.level === "standard" ? (
                      <p className="mt-1 text-[11.5px] text-accent">推荐方案</p>
                    ) : null}
                  </div>
                ))}
              </div>
            </div>
          ) : null}
          <div className="mt-6 space-y-3 border-t border-line pt-5 text-[12.5px] text-muted">
            {data.payment_terms ? (
              <div>
                <p className="font-medium text-ink">付款条款</p>
                <p className="mt-1 whitespace-pre-wrap leading-relaxed">{data.payment_terms}</p>
              </div>
            ) : null}
            {data.service_terms ? (
              <div>
                <p className="font-medium text-ink">服务条款</p>
                <p className="mt-1 whitespace-pre-wrap leading-relaxed">{data.service_terms}</p>
              </div>
            ) : null}
            {data.notes ? (
              <div>
                <p className="font-medium text-ink">备注</p>
                <p className="mt-1 whitespace-pre-wrap leading-relaxed">{data.notes}</p>
              </div>
            ) : null}
          </div>
          <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-5 text-[12px] text-faint">
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="h-3.5 w-3.5" />
              本报价单由 {company.name ?? "报价引擎"} 生成
            </span>
            <span>微信：{company.contact_wechat ?? "—"}</span>
          </div>
        </div>
        <div className="no-print mt-5 flex flex-wrap gap-3">
          {!accepted ? (
            <Button size="lg" className="flex-1" loading={accepting} onClick={() => void accept()}>
              <Check className="h-4 w-4" />
              确认这份报价
            </Button>
          ) : (
            <div className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-[#c8ecd7] bg-success-soft px-4 py-3 text-[13.5px] text-[#0b6b36]">
              <Check className="h-4 w-4" />
              已收到您的确认，业务员会尽快与您联系
            </div>
          )}
          {data.allow_download ? (
            <a href={publicApi.pdfUrl(token, password || undefined)} target="_blank" rel="noreferrer">
              <Button variant="secondary" size="lg">
                <Download className="h-4 w-4" />
                下载 / 打印
              </Button>
            </a>
          ) : null}
          <Button variant="ghost" size="lg" onClick={() => window.print()}>
            <Printer className="h-4 w-4" />
            打印
          </Button>
        </div>
        {company.contact_phone ? (
          <a href={"tel:" + company.contact_phone} className="no-print mt-3 block">
            <Button variant="secondary" size="lg" className="w-full">
              <Phone className="h-4 w-4" />
              联系业务员 {company.contact_phone}
            </Button>
          </a>
        ) : null}
        <p className="mt-5 text-center text-[11.5px] text-faint">
          报价有效期至 {formatDate(data.valid_until)}，逾期请重新确认价格。
        </p>
      </main>
    </div>
  );
}
function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10.5px] uppercase tracking-wider text-faint">{label}</p>
      <p className="mt-1 text-[13.5px] font-medium text-ink">{value}</p>
    </div>
  );
}

