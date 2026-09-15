"use client";
import { Building2, KeyRound, Save, Upload } from "lucide-react";
import * as React from "react";
import { PageHeader } from "@/components/app/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input, Select, Textarea } from "@/components/ui/input";
import { ErrorState, PageLoading } from "@/components/ui/states";
import { toast } from "@/components/ui/toast";
import { useSession } from "@/components/providers";
import { useApiData } from "@/hooks/use-api";
import { authApi, companyApi, errorMessage, fileApi } from "@/lib/api";
interface CompanyDetail {
  id: number;
  name: string;
  short_name: string | null;
  industry_id: string;
  contact_name: string | null;
  contact_phone: string | null;
  contact_wechat: string | null;
  address: string | null;
  credit_code: string | null;
  default_tax_rate: number;
  default_profit_margin: number;
  default_quote_valid_days: number;
  default_payment_terms: string | null;
  default_service_terms: string | null;
  default_footer: string | null;
  rounding_mode: string;
  quote_no_prefix: string;
  ai_monthly_quota: number;
  logo_file_id: number | null;
}
export default function SettingsPage() {
  const { session, refresh } = useSession();
  const { data, loading, error, reload } = useApiData<CompanyDetail>(
    () => companyApi.detail() as unknown as Promise<CompanyDetail>,
    [],
  );
  const industries = useApiData(() => companyApi.industries(), []);
  const storage = useApiData(() => fileApi.storage(), []);
  const [form, setForm] = React.useState<Partial<CompanyDetail>>({});
  const [saving, setSaving] = React.useState(false);
  const [passwordForm, setPasswordForm] = React.useState({ old_password: "", new_password: "" });
  const [changing, setChanging] = React.useState(false);
  const logoRef = React.useRef<HTMLInputElement>(null);
  React.useEffect(() => {
    if (data) setForm(data);
  }, [data]);
  if (loading) return <PageLoading label="正在加载企业设置…" />;
  if (error || !data) return <ErrorState message={error ?? "加载失败"} onRetry={reload} />;
  async function save() {
    setSaving(true);
    try {
      await companyApi.update({
        name: form.name,
        short_name: form.short_name,
        contact_name: form.contact_name,
        contact_phone: form.contact_phone,
        contact_wechat: form.contact_wechat,
        address: form.address,
        credit_code: form.credit_code,
        default_tax_rate: form.default_tax_rate,
        default_profit_margin: form.default_profit_margin,
        default_quote_valid_days: form.default_quote_valid_days,
        default_payment_terms: form.default_payment_terms,
        default_service_terms: form.default_service_terms,
        default_footer: form.default_footer,
        rounding_mode: form.rounding_mode,
        quote_no_prefix: form.quote_no_prefix,
      });
      toast.success("企业设置已保存");
      await refresh();
      reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }
  async function uploadLogo(file: File | undefined) {
    if (!file) return;
    try {
      const uploaded = await fileApi.upload(file);
      await companyApi.update({ logo_file_id: uploaded.id });
      toast.success("Logo 已更新");
      reload();
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      if (logoRef.current) logoRef.current.value = "";
    }
  }
  async function changePassword() {
    if (passwordForm.new_password.length < 8) {
      toast.error("新密码至少 8 位");
      return;
    }
    setChanging(true);
    try {
      await authApi.changePassword(passwordForm.old_password, passwordForm.new_password);
      toast.success("密码已更新，请重新登录");
      setPasswordForm({ old_password: "", new_password: "" });
      window.location.href = "/login";
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setChanging(false);
    }
  }
  return (
    <div>
      <PageHeader
        title="企业设置"
        description="公司信息、默认利润率、报价取整规则与报价单条款"
        actions={
          <Button loading={saving} onClick={() => void save()}>
            <Save className="h-4 w-4" />
            保存设置
          </Button>
        }
      />
      {session?.user.must_change_password ? (
        <div className="mb-4 rounded-xl border border-[#f6e0bd] bg-warning-soft px-4 py-3 text-[13px] text-[#8a4b00]">
          为了账号安全，请先修改初始密码。
        </div>
      ) : null}
      <div className="grid gap-4 xl:grid-cols-[1.5fr_1fr]">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>公司信息</CardTitle>
              <Building2 className="h-4 w-4 text-faint" />
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <Field label="公司名称" required className="sm:col-span-2" hint="会显示在报价单与公开报价页">
                <Input value={form.name ?? ""} onChange={(event) => setForm({ ...form, name: event.target.value })} />
              </Field>
              <Field label="公司简称">
                <Input value={form.short_name ?? ""} onChange={(event) => setForm({ ...form, short_name: event.target.value })} />
              </Field>
              <Field label="行业模板" hint="第一版开放广告标识">
                <Select value={form.industry_id ?? "advertising"} disabled>
                  {(industries.data ?? []).map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.name}
                      {item.status === "available" ? "" : "（即将上线）"}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="联系人">
                <Input value={form.contact_name ?? ""} onChange={(event) => setForm({ ...form, contact_name: event.target.value })} />
              </Field>
              <Field label="联系电话">
                <Input value={form.contact_phone ?? ""} onChange={(event) => setForm({ ...form, contact_phone: event.target.value })} />
              </Field>
              <Field label="微信号">
                <Input value={form.contact_wechat ?? ""} onChange={(event) => setForm({ ...form, contact_wechat: event.target.value })} />
              </Field>
              <Field label="统一社会信用代码">
                <Input value={form.credit_code ?? ""} onChange={(event) => setForm({ ...form, credit_code: event.target.value })} />
              </Field>
              <Field label="公司地址" className="sm:col-span-2">
                <Input value={form.address ?? ""} onChange={(event) => setForm({ ...form, address: event.target.value })} />
              </Field>
              <div className="sm:col-span-2">
                <p className="mb-1.5 text-[13px] font-medium text-ink-soft">企业 Logo</p>
                <div className="flex items-center gap-3">
                  <div className="flex h-14 w-14 items-center justify-center overflow-hidden rounded-xl border border-line bg-surface-2">
                    {form.logo_file_id ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={fileApi.url(form.logo_file_id)} alt="企业 Logo" className="h-full w-full object-contain" />
                    ) : (
                      <span className="text-[11px] text-faint">未设置</span>
                    )}
                  </div>
                  <input
                    ref={logoRef}
                    type="file"
                    accept=".png,.jpg,.jpeg,.webp"
                    className="hidden"
                    onChange={(event) => void uploadLogo(event.target.files?.[0])}
                  />
                  <Button variant="secondary" size="sm" onClick={() => logoRef.current?.click()}>
                    <Upload className="h-3.5 w-3.5" />
                    上传 Logo
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>报价默认规则</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <Field label="默认利润率" hint="0.3 表示 30%">
                <Input
                  type="number"
                  step="0.01"
                  value={form.default_profit_margin ?? 0.3}
                  onChange={(event) => setForm({ ...form, default_profit_margin: Number(event.target.value) })}
                />
              </Field>
              <Field label="默认税率" hint="0 表示不含税">
                <Input
                  type="number"
                  step="0.01"
                  value={form.default_tax_rate ?? 0}
                  onChange={(event) => setForm({ ...form, default_tax_rate: Number(event.target.value) })}
                />
              </Field>
              <Field label="报价有效期（天）">
                <Input
                  type="number"
                  value={form.default_quote_valid_days ?? 15}
                  onChange={(event) => setForm({ ...form, default_quote_valid_days: Number(event.target.value) })}
                />
              </Field>
              <Field label="报价取整方式" hint="心理价：10857 → 10880">
                <Select
                  value={form.rounding_mode ?? "10"}
                  onChange={(event) => setForm({ ...form, rounding_mode: event.target.value })}
                >
                  <option value="none">精确到分</option>
                  <option value="1">精确到元</option>
                  <option value="10">精确到 10 元</option>
                  <option value="100">精确到 100 元</option>
                  <option value="psychological">心理价（…80）</option>
                </Select>
              </Field>
              <Field label="报价编号前缀" hint="例如 Q → Q-20260915-0001">
                <Input
                  value={form.quote_no_prefix ?? "Q"}
                  onChange={(event) => setForm({ ...form, quote_no_prefix: event.target.value })}
                />
              </Field>
              <Field label="AI 每月额度" hint="由套餐决定，可在套餐页升级">
                <Input value={form.ai_monthly_quota ?? 0} readOnly />
              </Field>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>报价单条款</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Field label="默认付款条款">
                <Textarea
                  value={form.default_payment_terms ?? ""}
                  onChange={(event) => setForm({ ...form, default_payment_terms: event.target.value })}
                />
              </Field>
              <Field label="默认服务条款">
                <Textarea
                  value={form.default_service_terms ?? ""}
                  onChange={(event) => setForm({ ...form, default_service_terms: event.target.value })}
                  className="min-h-[120px]"
                />
              </Field>
              <Field label="报价单页脚">
                <Input value={form.default_footer ?? ""} onChange={(event) => setForm({ ...form, default_footer: event.target.value })} />
              </Field>
            </CardContent>
          </Card>
        </div>
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>套餐与存储</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2.5 text-[13px]">
              <Row label="当前套餐" value={session?.company?.plan_name ?? "免费版"} />
              <Row label="AI 每月额度" value={String(form.ai_monthly_quota ?? 0) + " 次"} />
              <Row
                label="文件存储"
                value={(storage.data?.used_mb ?? 0) + " MB / " + (storage.data?.quota_mb ?? 0) + " MB"}
              />
              <Row label="存储方式" value={(storage.data?.backend ?? "local") === "s3" ? "S3 对象存储" : "服务器本地"} />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>修改密码</CardTitle>
              <KeyRound className="h-4 w-4 text-faint" />
            </CardHeader>
            <CardContent className="space-y-3">
              <Field label="当前密码">
                <Input
                  type="password"
                  value={passwordForm.old_password}
                  onChange={(event) => setPasswordForm({ ...passwordForm, old_password: event.target.value })}
                />
              </Field>
              <Field label="新密码" hint="至少 8 位，包含字母与数字">
                <Input
                  type="password"
                  value={passwordForm.new_password}
                  onChange={(event) => setPasswordForm({ ...passwordForm, new_password: event.target.value })}
                />
              </Field>
              <Button variant="secondary" loading={changing} onClick={() => void changePassword()}>
                修改密码
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-line/70 pb-2 last:border-0 last:pb-0">
      <span className="text-muted">{label}</span>
      <span className="font-medium text-ink">{value}</span>
    </div>
  );
}
