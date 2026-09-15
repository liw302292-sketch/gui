"use client";

import { ArrowRight, ShieldCheck, Sparkles } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import * as React from "react";

import { useSession } from "@/components/providers";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { toast } from "@/components/ui/toast";
import { authApi, errorMessage } from "@/lib/api";

const DEMO_ACCOUNTS = [
  { label: "演示企业", email: "demo@example.com", password: "Demo123456!" },
  { label: "平台管理员", email: "admin@example.com", password: "Admin123456!" },
];

export default function LoginPage() {
  const router = useRouter();
  const { refresh } = useSession();
  const [identifier, setIdentifier] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [remember, setRemember] = React.useState(true);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await authApi.login(identifier.trim(), password, remember);
      const me = await refresh();
      toast.success("登录成功");
      const next = new URLSearchParams(window.location.search).get("next");
      if (result.must_change_password) {
        router.push("/app/settings?force_password=1");
      } else if (next) {
        router.push(next);
      } else {
        router.push(me?.user.is_superadmin ? "/admin" : "/app");
      }
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden flex-col justify-between border-r border-line bg-surface p-12 lg:flex">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-[10px] bg-ink text-[15px] font-semibold text-white">
            报
          </span>
          <span className="text-[15px] font-semibold tracking-tight text-ink">报价引擎</span>
        </Link>

        <div className="max-w-md">
          <h1 className="text-[32px] font-semibold leading-tight tracking-tight text-ink">
            客户发张图，
            <br />
            <span className="text-gradient">30 秒出报价。</span>
          </h1>
          <p className="mt-4 text-[14.5px] leading-relaxed text-muted">
            登录后可以看到你的价格库、历史报价、客户跟进与 AI 用量。
          </p>
          <div className="mt-8 space-y-3">
            {[
              "微信截图一键转成结构化需求",
              "价格由你自己的规则引擎计算",
              "客户打开报价自动提醒你跟进",
            ].map((item) => (
              <div key={item} className="flex items-center gap-2.5 text-[13.5px] text-ink-soft">
                <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-accent-soft">
                  <Sparkles className="h-3 w-3 text-accent" />
                </span>
                {item}
              </div>
            ))}
          </div>
        </div>

        <p className="flex items-center gap-2 text-[12.5px] text-faint">
          <ShieldCheck className="h-3.5 w-3.5" />
          密码加密存储 · 企业数据严格隔离 · AI Key 只放在后端
        </p>
      </div>

      <div className="flex items-center justify-center px-5 py-12">
        <div className="w-full max-w-sm">
          <Link href="/" className="mb-8 flex items-center gap-2.5 lg:hidden">
            <span className="flex h-8 w-8 items-center justify-center rounded-[10px] bg-ink text-[15px] font-semibold text-white">
              报
            </span>
            <span className="text-[15px] font-semibold tracking-tight text-ink">报价引擎</span>
          </Link>

          <h2 className="text-[24px] font-semibold tracking-tight text-ink">登录</h2>
          <p className="mt-1.5 text-[13.5px] text-muted">用邮箱或手机号登录你的报价工作台</p>

          <form className="mt-8 space-y-4" onSubmit={submit}>
            <Field label="邮箱 / 手机号" required>
              <Input
                value={identifier}
                onChange={(event) => setIdentifier(event.target.value)}
                placeholder="you@company.com"
                autoComplete="username"
                required
              />
            </Field>
            <Field label="密码" required error={error}>
              <Input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="请输入密码"
                autoComplete="current-password"
                required
              />
            </Field>

            <label className="flex items-center gap-2 text-[13px] text-muted">
              <input
                type="checkbox"
                checked={remember}
                onChange={(event) => setRemember(event.target.checked)}
                className="h-4 w-4 rounded-[5px] accent-[#635BFF]"
              />
              30 天内免登录
            </label>

            <Button type="submit" className="w-full" size="lg" loading={loading}>
              登录
              <ArrowRight className="h-4 w-4" />
            </Button>
          </form>

          <div className="mt-6 rounded-[14px] border border-line bg-surface-2 p-4">
            <p className="text-[12.5px] font-medium text-ink-soft">演示账号（即点即用）</p>
            <div className="mt-2.5 flex flex-wrap gap-2">
              {DEMO_ACCOUNTS.map((account) => (
                <Button
                  key={account.email}
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    setIdentifier(account.email);
                    setPassword(account.password);
                  }}
                >
                  {account.label}
                </Button>
              ))}
            </div>
          </div>

          <p className="mt-6 text-center text-[13px] text-muted">
            还没有账号？
            <Link href="/register" className="ml-1 text-accent hover:underline">
              免费注册
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
