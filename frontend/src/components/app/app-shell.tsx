"use client";

import {
  BarChart3,
  Bell,
  ChevronDown,
  CreditCard,
  FileText,
  HelpCircle,
  LayoutDashboard,
  ListChecks,
  LogOut,
  Menu,
  Package,
  Plus,
  Search,
  Settings,
  Sparkles,
  Tags,
  UserRound,
  Users,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import * as React from "react";

import { useSession } from "@/components/providers";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Drawer } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { PageLoading } from "@/components/ui/states";
import { companyApi, errorMessage } from "@/lib/api";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/app", label: "工作台", icon: LayoutDashboard },
  { href: "/app/quotes", label: "报价", icon: FileText },
  { href: "/app/customers", label: "客户", icon: Users },
  { href: "/app/products", label: "产品与价格", icon: Package },
  { href: "/app/templates", label: "报价模板", icon: Tags },
  { href: "/app/followups", label: "跟进", icon: ListChecks },
  { href: "/app/analytics", label: "数据", icon: BarChart3 },
  { href: "/app/ai", label: "AI 助手", icon: Sparkles },
  { href: "/app/settings", label: "企业设置", icon: Settings },
];

const MOBILE_TABS = [
  { href: "/app/quotes/new", label: "新建报价", icon: Plus, accent: true },
  { href: "/app/quotes", label: "报价", icon: FileText },
  { href: "/app/customers", label: "客户", icon: Users },
  { href: "/app/followups", label: "跟进", icon: ListChecks },
  { href: "/app/settings", label: "我的", icon: UserRound },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const { session, loading, logout } = useSession();
  const pathname = usePathname();
  const router = useRouter();
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [userMenuOpen, setUserMenuOpen] = React.useState(false);
  const [notifications, setNotifications] = React.useState(0);
  const [searchOpen, setSearchOpen] = React.useState(false);
  const [searchTerm, setSearchTerm] = React.useState("");
  const [searchResult, setSearchResult] = React.useState<{
    customers: { id: number; name: string }[];
    quotes: { id: number; quote_no: string; project_name: string }[];
  } | null>(null);

  React.useEffect(() => {
    if (!loading && !session) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [loading, session, router, pathname]);

  React.useEffect(() => {
    setDrawerOpen(false);
    setUserMenuOpen(false);
    setSearchOpen(false);
  }, [pathname]);

  React.useEffect(() => {
    if (!session) return;
    companyApi
      .notifications()
      .then((data) => setNotifications(data.unread))
      .catch(() => setNotifications(0));
  }, [session, pathname]);

  React.useEffect(() => {
    if (!searchTerm.trim()) {
      setSearchResult(null);
      return;
    }
    const timer = window.setTimeout(() => {
      companyApi
        .search(searchTerm.trim())
        .then((data) =>
          setSearchResult({
            customers: data.customers.map((item) => ({ id: item.id, name: item.name })),
            quotes: data.quotes.map((item) => ({
              id: item.id,
              quote_no: item.quote_no,
              project_name: item.project_name,
            })),
          }),
        )
        .catch(() => setSearchResult(null));
    }, 260);
    return () => window.clearTimeout(timer);
  }, [searchTerm]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <PageLoading label="正在加载工作台…" />
      </div>
    );
  }

  if (!session) return null;

  const company = session.company;
  const planName = company?.plan_name ?? "免费版";
  const usageRatio = Math.min(company?.ai_quota ? 1 : 0, 1);

  const sidebar = (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2.5 px-5 py-5">
        <span className="flex h-8 w-8 items-center justify-center rounded-[10px] bg-ink text-[15px] font-semibold text-white">
          报
        </span>
        <div className="min-w-0">
          <p className="truncate text-[14px] font-semibold tracking-tight text-ink">
            {company?.name ?? "报价引擎"}
          </p>
          <p className="text-[11.5px] text-faint">{planName}</p>
        </div>
      </div>

      <div className="px-3">
        <Link href="/app/quotes/new">
          <Button className="w-full" size="md">
            <Plus className="h-4 w-4" />
            新建报价
          </Button>
        </Link>
      </div>

      <nav className="mt-4 flex-1 space-y-0.5 overflow-y-auto px-3 pb-3">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = item.href === "/app" ? pathname === "/app" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
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

      <div className="space-y-0.5 border-t border-line px-3 py-3">
        <Link
          href="/app/billing"
          className={cn(
            "flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-[13.5px] font-medium transition-colors",
            pathname.startsWith("/app/billing") ? "bg-surface text-ink" : "text-muted hover:bg-surface/70 hover:text-ink",
          )}
        >
          <CreditCard className="h-4 w-4 text-faint" />
          套餐
        </Link>
        <Link
          href="/features"
          className="flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-[13.5px] font-medium text-muted transition-colors hover:bg-surface/70 hover:text-ink"
        >
          <HelpCircle className="h-4 w-4 text-faint" />
          帮助
        </Link>
      </div>

      <div className="border-t border-line px-4 py-3">
        <div className="flex items-center justify-between text-[11.5px] text-muted">
          <span>本月 AI 额度</span>
          <span className="text-ink-soft">{company?.ai_quota ?? 0} 次</span>
        </div>
        <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-line/70">
          <div className="h-full rounded-full bg-accent" style={{ width: `${usageRatio * 100}%` }} />
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 hidden w-[248px] border-r border-line bg-surface/60 backdrop-blur lg:block">
        {sidebar}
      </aside>

      <Drawer open={drawerOpen} onClose={() => setDrawerOpen(false)} title="报价引擎">
        {sidebar}
      </Drawer>

      <div className="lg:pl-[248px]">
        <header className="sticky top-0 z-30 border-b border-line bg-surface/85 backdrop-blur-xl">
          <div className="flex h-14 items-center gap-3 px-4 sm:px-6">
            <Button
              variant="ghost"
              size="iconSm"
              className="lg:hidden"
              onClick={() => setDrawerOpen(true)}
              aria-label="打开菜单"
            >
              <Menu className="h-4 w-4" />
            </Button>

            <button
              type="button"
              onClick={() => setSearchOpen(true)}
              className="flex h-9 flex-1 items-center gap-2 rounded-xl border border-line bg-surface-2 px-3 text-[13px] text-faint transition-colors hover:border-line-strong sm:max-w-sm"
            >
              <Search className="h-3.5 w-3.5" />
              搜索客户、项目或报价编号
            </button>

            <div className="ml-auto flex items-center gap-2">
              <Link href="/app/ai">
                <Button variant="ghost" size="iconSm" aria-label="AI 助手">
                  <Sparkles className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/app/followups" className="relative">
                <Button variant="ghost" size="iconSm" aria-label="通知">
                  <Bell className="h-4 w-4" />
                </Button>
                {notifications ? (
                  <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-danger px-1 text-[10px] font-medium text-white">
                    {notifications > 9 ? "9+" : notifications}
                  </span>
                ) : null}
              </Link>

              <div className="relative">
                <button
                  type="button"
                  onClick={() => setUserMenuOpen((value) => !value)}
                  className="flex items-center gap-2 rounded-xl border border-line bg-surface px-2.5 py-1.5 text-[13px] text-ink-soft transition-colors hover:border-line-strong"
                >
                  <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-accent-soft text-[11px] font-semibold text-accent">
                    {(session.user.name || "U").slice(0, 1)}
                  </span>
                  <span className="hidden max-w-[80px] truncate sm:inline">{session.user.name}</span>
                  <ChevronDown className="h-3.5 w-3.5 text-faint" />
                </button>

                {userMenuOpen ? (
                  <div className="absolute right-0 top-11 z-40 w-52 overflow-hidden rounded-[14px] border border-line bg-surface shadow-[var(--shadow-float)]">
                    <div className="border-b border-line px-4 py-3">
                      <p className="truncate text-[13px] font-medium text-ink">{session.user.name}</p>
                      <p className="truncate text-[12px] text-faint">{session.user.email ?? session.user.phone}</p>
                    </div>
                    <div className="p-1.5">
                      <Link
                        href="/app/settings"
                        className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] text-ink-soft hover:bg-surface-2"
                      >
                        <Settings className="h-3.5 w-3.5 text-faint" />
                        企业设置
                      </Link>
                      <Link
                        href="/app/billing"
                        className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] text-ink-soft hover:bg-surface-2"
                      >
                        <CreditCard className="h-3.5 w-3.5 text-faint" />
                        套餐与订单
                      </Link>
                      {session.user.is_superadmin ? (
                        <Link
                          href="/admin"
                          className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] text-ink-soft hover:bg-surface-2"
                        >
                          <BarChart3 className="h-3.5 w-3.5 text-faint" />
                          管理员后台
                        </Link>
                      ) : null}
                      <button
                        type="button"
                        onClick={() => void logout()}
                        className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-[13px] text-danger hover:bg-danger-soft"
                      >
                        <LogOut className="h-3.5 w-3.5" />
                        退出登录
                      </button>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1240px] px-4 pb-24 pt-6 sm:px-6 lg:pb-10">{children}</main>
      </div>

      <nav className="fixed bottom-0 left-0 right-0 z-30 border-t border-line bg-surface/95 backdrop-blur lg:hidden">
        <div className="flex items-stretch justify-around">
          {MOBILE_TABS.map((tab) => {
            const Icon = tab.icon;
            const active = pathname === tab.href || (tab.href !== "/app" && pathname.startsWith(tab.href));
            return (
              <Link
                key={tab.href}
                href={tab.href}
                className={cn(
                  "flex flex-1 flex-col items-center gap-0.5 py-2.5 text-[11px]",
                  active ? "text-accent" : "text-faint",
                  tab.accent && !active && "text-ink",
                )}
              >
                <Icon className={cn("h-4.5 w-4.5", tab.accent && "text-accent")} />
                {tab.label}
              </Link>
            );
          })}
        </div>
      </nav>

      {searchOpen ? (
        <div className="fixed inset-0 z-50 flex items-start justify-center p-4 pt-24">
          <div className="absolute inset-0 bg-ink/30 backdrop-blur-[2px]" onClick={() => setSearchOpen(false)} aria-hidden />
          <div className="relative z-10 w-full max-w-lg overflow-hidden rounded-[16px] border border-line bg-surface shadow-[var(--shadow-float)]">
            <div className="border-b border-line p-3">
              <Input
                autoFocus
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="搜索客户名称、项目名称或报价编号…"
              />
            </div>
            <div className="max-h-[380px] overflow-y-auto p-2">
              {!searchResult ? (
                <p className="px-3 py-6 text-center text-[13px] text-faint">
                  {searchTerm ? "没有找到匹配结果" : "输入关键词开始搜索"}
                </p>
              ) : (
                <>
                  {searchResult.customers.length ? (
                    <div className="mb-2">
                      <p className="px-3 py-1.5 text-[11.5px] uppercase tracking-wide text-faint">客户</p>
                      {searchResult.customers.map((item) => (
                        <Link
                          key={item.id}
                          href={`/app/customers/${item.id}`}
                          className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] text-ink-soft hover:bg-surface-2"
                        >
                          <Users className="h-3.5 w-3.5 text-faint" />
                          {item.name}
                        </Link>
                      ))}
                    </div>
                  ) : null}
                  {searchResult.quotes.length ? (
                    <div>
                      <p className="px-3 py-1.5 text-[11.5px] uppercase tracking-wide text-faint">报价</p>
                      {searchResult.quotes.map((item) => (
                        <Link
                          key={item.id}
                          href={`/app/quotes/${item.id}`}
                          className="flex items-center justify-between gap-2.5 rounded-lg px-3 py-2 text-[13px] text-ink-soft hover:bg-surface-2"
                        >
                          <span className="flex items-center gap-2.5">
                            <FileText className="h-3.5 w-3.5 text-faint" />
                            {item.project_name}
                          </span>
                          <Badge tone="neutral">{item.quote_no}</Badge>
                        </Link>
                      ))}
                    </div>
                  ) : null}
                  {!searchResult.customers.length && !searchResult.quotes.length ? (
                    <p className="px-3 py-6 text-center text-[13px] text-faint">没有找到匹配结果</p>
                  ) : null}
                </>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

