"use client";

import Link from "next/link";
import { Menu, X } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { useSession } from "@/components/providers";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/features", label: "功能" },
  { href: "/pricing", label: "价格" },
  { href: "/demo", label: "演示" },
];

export function SiteHeader() {
  const [scrolled, setScrolled] = React.useState(false);
  const [open, setOpen] = React.useState(false);
  const { session } = useSession();

  React.useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={cn(
        "sticky top-0 z-40 border-b transition-all duration-300",
        scrolled ? "border-line bg-white/85 backdrop-blur-xl" : "border-transparent bg-transparent",
      )}
    >
      <div className="container-page flex h-16 items-center justify-between gap-6">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-[10px] bg-ink text-[15px] font-semibold text-white">
            报
          </span>
          <span className="text-[15px] font-semibold tracking-tight text-ink">报价引擎</span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-lg px-3 py-2 text-[13.5px] text-ink-soft transition-colors hover:bg-surface-2 hover:text-ink"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          {session ? (
            <Link href="/app">
              <Button size="sm">进入工作台</Button>
            </Link>
          ) : (
            <>
              <Link href="/login">
                <Button variant="ghost" size="sm">
                  登录
                </Button>
              </Link>
              <Link href="/register">
                <Button size="sm">免费开始报价</Button>
              </Link>
            </>
          )}
        </div>

        <button
          type="button"
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-line bg-surface md:hidden"
          onClick={() => setOpen((value) => !value)}
          aria-label="菜单"
        >
          {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
        </button>
      </div>

      {open ? (
        <div className="border-t border-line bg-surface px-5 py-4 md:hidden">
          <div className="flex flex-col gap-1">
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className="rounded-lg px-3 py-2.5 text-[14px] text-ink-soft hover:bg-surface-2"
              >
                {item.label}
              </Link>
            ))}
          </div>
          <div className="mt-4 flex flex-col gap-2">
            {session ? (
              <Link href="/app">
                <Button className="w-full">进入工作台</Button>
              </Link>
            ) : (
              <>
                <Link href="/register">
                  <Button className="w-full">免费开始报价</Button>
                </Link>
                <Link href="/login">
                  <Button variant="secondary" className="w-full">
                    登录
                  </Button>
                </Link>
              </>
            )}
          </div>
        </div>
      ) : null}
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="border-t border-line bg-surface">
      <div className="container-page flex flex-col gap-6 py-10 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="flex h-7 w-7 items-center justify-center rounded-[9px] bg-ink text-[13px] font-semibold text-white">
              报
            </span>
            <span className="text-[14px] font-semibold text-ink">报价引擎 Quote Engine</span>
          </div>
          <p className="mt-2 max-w-md text-[12.5px] leading-relaxed text-muted">
            面向非标行业的 AI 报价基础设施。第一行业版本：广告标识 / 广告制作。
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-[13px] text-muted">
          <Link href="/features" className="hover:text-ink">
            功能
          </Link>
          <Link href="/pricing" className="hover:text-ink">
            价格
          </Link>
          <Link href="/demo" className="hover:text-ink">
            演示
          </Link>
          <Link href="/login" className="hover:text-ink">
            登录
          </Link>
          <span className="text-faint">© {new Date().getFullYear()} Quote Engine</span>
        </div>
      </div>
    </footer>
  );
}

