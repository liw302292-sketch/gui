import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  unit,
  hint,
  trend,
  icon,
  tone = "default",
}: {
  label: string;
  value: string;
  unit?: string;
  hint?: string;
  trend?: number;
  icon?: React.ReactNode;
  tone?: "default" | "accent" | "success" | "warning";
}) {
  const tones = {
    default: "bg-surface",
    accent: "bg-accent-soft/50 border-accent/20",
    success: "bg-success-soft/50 border-[#c8ecd7]",
    warning: "bg-warning-soft/50 border-[#f6e0bd]",
  }[tone];

  return (
    <div className={cn("rounded-[16px] border border-line p-4 shadow-[var(--shadow-subtle)]", tones)}>
      <div className="flex items-start justify-between gap-3">
        <p className="text-[12.5px] text-muted">{label}</p>
        {icon ? <span className="text-faint">{icon}</span> : null}
      </div>
      <div className="mt-3 flex items-baseline gap-1.5">
        <span className="text-[26px] font-semibold leading-none tracking-tight tabular-nums text-ink">{value}</span>
        {unit ? <span className="text-[12.5px] text-faint">{unit}</span> : null}
      </div>
      <div className="mt-2 flex items-center gap-2">
        {typeof trend === "number" ? (
          <span
            className={cn(
              "inline-flex items-center gap-0.5 text-[12px]",
              trend >= 0 ? "text-success" : "text-danger",
            )}
          >
            {trend >= 0 ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
            {Math.abs(trend * 100).toFixed(1)}%
          </span>
        ) : null}
        {hint ? <span className="text-[12px] text-faint">{hint}</span> : null}
      </div>
    </div>
  );
}

