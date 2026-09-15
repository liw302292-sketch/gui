"use client";

import { ArrowRight, BadgeCheck } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import * as React from "react";

import { useSession } from "@/components/providers";
import { Button } from "@/components/ui/button";
import { Field, Input, Select } from "@/components/ui/input";
import { toast } from "@/components/ui/toast";
import { authApi, companyApi, errorMessage } from "@/lib/api";
import type { IndustryTemplateSummary } from "@/lib/types";

export default function RegisterPage() {
  const router = useRouter();
  const { refresh } = useSession();
  const [mode, setMode] = React.useState<"email" | "phone">("email");
  const [form, setForm] = React.useState({
    email: "",
    phone: "",
    password: "",
    name: "",
    company_name: "",
    industry_id: "advertising",
  });
  const [industries, setIndustries] = React.useState<IndustryTemplateSummary[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    companyApi
      .industries()
      .then(setIndustries)
      .catch(() => setIndustries([]));
  }, []);

  function update(key: keyof typeof form, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await authApi.register({
        email: mode === "email" ? form.email.trim() : undefined,
        phone: mode === "phone" ? form.phone.trim() : undefined,
        password: form.password,
        name: form.name.trim(),
        company_name: form.company_name.trim(),
        industry_id: form.industry_id,
      });
      await refresh();
      toast.success("注册成功，已为你创建企业并预置价格库");
      router.push("/app");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-[1fr_1.1fr]">
      <div className="flex items-center justify-center px-5 py-12">
        <div className="w-full max-w-md">
          <Link href="/" className="mb-8 flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-[10px] bg-ink text-[15px] font-semibold text-white">
              报
            </span>
            <span className="text-[15px] font-semibold tracking-tight text-ink">报价引擎</span>
          </Link>

          <h2 className="text-[24px] font-semibold tracking-tight text-ink">免费注册</h2>
          <p className="mt-1.5 text-[13.5px] text-muted">
            注册后自动创建企业并预置广告标识价格库，可直接开始报价
          </p>

          <div className="mt-6 flex gap-1 rounded-xl border border-line bg-surface-2 p-1">
            {[
              { value: "email", label: "邮箱注册" },
              { value: "phone", label: "手机号注册" },
            ].map((item) => (
              <button
                key={item.value}
                type="button"
                onClick={() => setMode(item.value as "email" | "phone")}
                className={`flex-1 rounded-lg px-3 py-1.5 text-[13px] font-medium transition-all ${
                  mode === item.value ? "bg-surface text-ink shadow-[var(--shadow-subtle)]" : "text-muted"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          <form className="mt-5 space-y-4" onSubmit={submit}>
            {mode === "email" ? (
              <Field label="邮箱" required>
                <Input
                  type="email"
                  value={form.email}
                  onChange={(event) => update("email", event.target.value)}
                  placeholder="you@company.com"
                  autoComplete="email"
                  required
                />
              </Field>
            ) : (
              <Field label="手机号" required>
                <Input
                  value={form.phone}
                  onChange={(event) => update("phone", event.target.value)}
                  placeholder="13800000000"
                  autoComplete="tel"
                  required
                />
              </Field>
            )}

            <Field label="密码" hint="至少 8 位，需包含字母和数字" required>
              <Input
                type="password"
                value={form.password}
                onChange={(event) => update("password", event.target.value)}
                placeholder="设置登录密码"
                autoComplete="new-password"
                required
              />
            </Field>

            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="你的称呼">
                <Input
                  value={form.name}
                  onChange={(event) => update("name", event.target.value)}
                  placeholder="张老板"
                />
              </Field>
              <Field label="行业模板">
                <Select value={form.industry_id} onChange={(event) => update("industry_id", event.target.value)}>
                  {(industries.length ? industries : [{ code: "advertising", name: "广告标识", status: "available" } as IndustryTemplateSummary]).map(
                    (item) => (
                      <option key={item.code} value={item.code} disabled={item.status !== "available"}>
                        {item.name}
                        {item.status !== "available" ? "（即将上线）" : ""}
                      </option>
                    ),
                  )}
                </Select>
              </Field>
            </div>

            <Field label="公司名称" hint="会显示在你的报价单上，之后可以修改" required>
              <Input
                value={form.company_name}
                onChange={(event) => update("company_name", event.target.value)}
                placeholder="例如：星辰广告制作"
                required
              />
            </Field>

            {error ? (
              <div className="rounded-xl border border-[#f8d3d3] bg-danger-soft px-3.5 py-2.5 text-[13px] text-[#8f1d1d]">
                {error}
              </div>
            ) : null}

            <Button type="submit" size="lg" className="w-full" loading={loading}>
              创建账号并开始报价
              <ArrowRight className="h-4 w-4" />
            </Button>
          </form>

          <p className="mt-6 text-center text-[13px] text-muted">
            已有账号？
            <Link href="/login" className="ml-1 text-accent hover:underline">
              直接登录
            </Link>
          </p>
        </div>
      </div>

      <div className="relative hidden flex-col justify-center border-l border-line bg-surface p-12 lg:flex">
        <h3 className="text-[22px] font-semibold tracking-tight text-ink">注册后你会立刻拥有</h3>
        <div className="mt-8 space-y-5">
          {[
            { title: "10 个产品分类，20+ 常用产品", desc: "门头、发光字、灯箱、标牌、喷绘、写真、展架、导视、安装、运输" },
            { title: "完整的报价规则模板", desc: "面积计价、固定单价、损耗率、人工费、运输费、面积超 20㎡ 自动批发价" },
            { title: "专业报价单与公开链接", desc: "企业信息、付款条款、服务条款自动带上，客户手机上直接打开" },
            { title: "客户与跟进管理", desc: "报价、查看、跟进、成交全程留痕，今天该联系谁一目了然" },
          ].map((item) => (
            <div key={item.title} className="flex gap-3.5">
              <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-accent-soft">
                <BadgeCheck className="h-3.5 w-3.5 text-accent" />
              </span>
              <div>
                <p className="text-[14px] font-medium text-ink">{item.title}</p>
                <p className="mt-1 text-[12.5px] leading-relaxed text-muted">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
        <p className="mt-10 text-[12.5px] text-faint">
          预置价格仅为演示数据，不代表行业统一价格，注册后可以自由修改。
        </p>
      </div>
    </div>
  );
}

