"use client";
import { Activity, AlertOctagon, BarChart3, Building2, CreditCard, FileText, Layers, LayoutDashboard, LogOut, Menu, ScrollText, Settings, Users } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import * as React from "react";
import { useSession } from "@/components/providers";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageLoading } from "@/components/ui/states";
import { cn } from "@/lib/utils";
const NAV = [
  { href: "/admin", label: "Dashboard", icon: LayoutDashboard },
  { href: "/admin/companies", label: "企业", icon: Building2 },
  { href: "/admin/users", label: "用户", icon: Users },
  { href: "/admin/plans", label: "套餐", icon: Layers },
  { href: "/admin/orders", label: "订单", icon: CreditCard },
  { href: "/admin/subscriptions", label: "订阅", icon: FileText },
  { href: "/admin/ai", label: "AI 使用", icon: Activity },
  { href: "/admin/logs", label: "日志与异常", icon: ScrollText },
  { href: "/admin/settings", label: "系统设置", icon: Settings },
];
export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { session, loading, logout } = useSession();
  const pathname = usePathname();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = React.useState(false);
  React.useEffect(() => {
    if (loading) return;
    if (!session) {
      router.replace("/login?next=/admin");
      return;
    }
    if (!session.user.is_superadmin) {
      router.replace("/app");
    }
  }, [loading, session, router]);
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <PageLoading label="正在校验管理员权限…" />
      </div>
    );
  }
  if (!session?.user.is_superadmin) return null;
  const sidebar = (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2.5 px-5 py-5">
        <span className="flex h-8 w-8 items-center justify-center rounded-[10px] bg-ink text-[15px] font-semibold text-white">报</span>
        <div>
          <p className="text-[14px] font-semibold tracking-tight text-ink">平台管理后台</p>
          <p className="text-[11.5px] text-faint">Quote Engine Admin</p>
        </div>
      </div>
      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 pb-3">
        {NAV.map((item) => {
          const Icon = item.icon;
          const active = item.href === "/admin" ? pathname === "/admin" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMenuOpen(false)}
              className={cn(
                "flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-[13.5px] font-medium transition-colors",
                active ? "bg-surface text-ink shadow-[var(--shadow-subtle)]" : "text-muted hover:bg-surface/70 hover:text-ink",
              )}
            >
              <Icon className={cn("h-4 w-4", active ? "text-accent" : "text-faint")} />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-line px-3 py-3">
        <Link
          href="/app"
          className="flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-[13.5px] text-muted hover:bg-surface/70 hover:text-ink"
        >
          <BarChart3 className="h-4 w-4 text-faint" />
          切换到企业后台
        </Link>
        <button
          type="button"
          onClick={() => void logout()}
          className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-[13.5px] text-danger hover:bg-danger-soft"
        >
          <LogOut className="h-4 w-4" />
          退出登录
        </button>
      </div>
    </div>
  );
  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 hidden w-[240px] border-r border-line bg-surface/60 backdrop-blur lg:block">{sidebar}</aside>
      {menuOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-ink/35" onClick={() => setMenuOpen(false)} aria-hidden />
          <aside className="absolute left-0 top-0 h-full w-[270px] border-r border-line bg-surface shadow-[var(--shadow-float)]">{sidebar}</aside>
        </div>
      ) : null}
      <div className="lg:pl-[240px]">
        <header className="sticky top-0 z-30 border-b border-line bg-surface/85 backdrop-blur-xl">
          <div className="flex h-14 items-center gap-3 px-4 sm:px-6">
            <Button variant="ghost" size="iconSm" className="lg:hidden" onClick={() => setMenuOpen(true)} aria-label="菜单">
              <Menu className="h-4 w-4" />
            </Button>
            <span className="flex items-center gap-2 text-[13.5px] text-muted">
              <AlertOctagon className="h-3.5 w-3.5 text-faint" />
              管理员模式：可查看全平台数据
            </span>
            <div className="ml-auto flex items-center gap-2">
              <Badge tone="dark">{session.user.name}</Badge>
            </div>
          </div>
        </header>
        <main className="mx-auto w-full max-w-[1280px] px-4 py-6 sm:px-6">{children}</main>
      </div>
    </div>
  );
}

