"use client";

import { AlertTriangle, Inbox, Loader2, RefreshCw } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils";
import { Button } from "./button";

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn("h-4 w-4 animate-spin text-accent", className)} />;
}

export function PageLoading({ label = "加载中…" }: { label?: string }) {
  return (
    <div className="flex min-h-[320px] flex-col items-center justify-center gap-3 text-muted">
      <div className="relative flex h-11 w-11 items-center justify-center">
        <span className="absolute inset-0 rounded-full border-2 border-accent/20" />
        <span className="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-t-accent" />
      </div>
      <p className="text-[13px]">{label}</p>
    </div>
  );
}

export function SkeletonRows({ rows = 5, className }: { rows?: number; className?: string }) {
  return (
    <div className={cn("space-y-2.5", className)}>
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="skeleton h-11 w-full" />
      ))}
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-[16px] border border-dashed border-line-strong bg-surface-2 px-6 py-14 text-center",
        className,
      )}
    >
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl border border-line bg-surface text-accent shadow-[var(--shadow-subtle)]">
        {icon ?? <Inbox className="h-5 w-5" />}
      </div>
      <h3 className="text-[15px] font-semibold text-ink">{title}</h3>
      {description ? <p className="mt-1.5 max-w-md text-[13px] leading-relaxed text-muted">{description}</p> : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
  className,
}: {
  message: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-[16px] border border-[#f8d3d3] bg-danger-soft px-6 py-12 text-center",
        className,
      )}
    >
      <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-danger shadow-[var(--shadow-subtle)]">
        <AlertTriangle className="h-5 w-5" />
      </div>
      <p className="text-[14px] font-medium text-ink">{message}</p>
      {onRetry ? (
        <Button variant="secondary" size="sm" className="mt-4" onClick={onRetry}>
          <RefreshCw className="h-3.5 w-3.5" />
          重新加载
        </Button>
      ) : null}
    </div>
  );
}

export function InlineAlert({
  tone = "warning",
  title,
  children,
  action,
}: {
  tone?: "warning" | "danger" | "info" | "success";
  title: string;
  children?: React.ReactNode;
  action?: React.ReactNode;
}) {
  const tones = {
    warning: "border-[#f6e0bd] bg-warning-soft text-[#8a4b00]",
    danger: "border-[#f8d3d3] bg-danger-soft text-[#8f1d1d]",
    info: "border-[#cfe0ff] bg-info-soft text-[#1a3f8f]",
    success: "border-[#c8ecd7] bg-success-soft text-[#0b6b36]",
  }[tone];

  return (
    <div className={cn("flex flex-wrap items-center justify-between gap-3 rounded-xl border px-4 py-3", tones)}>
      <div>
        <p className="text-[13.5px] font-medium">{title}</p>
        {children ? <div className="mt-0.5 text-[12.5px] opacity-90">{children}</div> : null}
      </div>
      {action}
    </div>
  );
}

