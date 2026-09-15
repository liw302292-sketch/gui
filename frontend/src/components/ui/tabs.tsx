"use client";

import { cn } from "@/lib/utils";

export function Tabs({
  tabs,
  value,
  onChange,
  className,
}: {
  tabs: { value: string; label: string; count?: number }[];
  value: string;
  onChange: (value: string) => void;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-1 rounded-xl border border-line bg-surface-2 p-1",
        className,
      )}
    >
      {tabs.map((tab) => {
        const active = tab.value === value;
        return (
          <button
            key={tab.value}
            type="button"
            onClick={() => onChange(tab.value)}
            className={cn(
              "rounded-lg px-3.5 py-1.5 text-[13px] font-medium transition-all",
              active ? "bg-surface text-ink shadow-[var(--shadow-subtle)]" : "text-muted hover:text-ink",
            )}
          >
            {tab.label}
            {typeof tab.count === "number" ? (
              <span className={cn("ml-1.5 text-[11.5px]", active ? "text-accent" : "text-faint")}>{tab.count}</span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}

