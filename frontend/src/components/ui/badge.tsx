import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[12px] font-medium leading-5",
  {
    variants: {
      tone: {
        neutral: "border-line bg-surface-2 text-muted",
        accent: "border-[#ddd9ff] bg-accent-soft text-accent",
        success: "border-[#c8ecd7] bg-success-soft text-success",
        warning: "border-[#f6e0bd] bg-warning-soft text-warning",
        danger: "border-[#f8d3d3] bg-danger-soft text-danger",
        info: "border-[#cfe0ff] bg-info-soft text-info",
        dark: "border-ink bg-ink text-white",
      },
    },
    defaultVariants: { tone: "neutral" },
  },
);

export function Badge({
  className,
  tone,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ tone }), className)} {...props} />;
}

const STATUS_TONE: Record<string, VariantProps<typeof badgeVariants>["tone"]> = {
  draft: "neutral",
  sent: "info",
  viewed: "accent",
  following: "warning",
  won: "success",
  void: "danger",
  new: "neutral",
  quoted: "info",
  communicating: "warning",
  high_intent: "accent",
  lost: "danger",
  active: "success",
  disabled: "danger",
  paid: "success",
  pending: "warning",
  failed: "danger",
  success: "success",
  expired: "neutral",
  cancelled: "neutral",
};

/** 状态中文文案：后端字典与前端保持一致，避免界面出现英文枚举值。 */
export const STATUS_LABELS: Record<string, string> = {
  draft: "草稿",
  sent: "已发送",
  viewed: "已查看",
  following: "待跟进",
  won: "已成交",
  void: "已作废",
  new: "新客户",
  quoted: "已报价",
  communicating: "沟通中",
  high_intent: "高意向",
  lost: "已流失",
  active: "正常",
  disabled: "已停用",
  paid: "已支付",
  pending: "待支付",
  refunded: "已退款",
  cancelled: "已取消",
  expired: "已过期",
  success: "成功",
  failed: "失败",
};

export function StatusBadge({
  status,
  label,
  className,
}: {
  status: string;
  label?: string;
  className?: string;
}) {
  return (
    <Badge tone={STATUS_TONE[status] ?? "neutral"} className={className}>
      {label ?? STATUS_LABELS[status] ?? status}
    </Badge>
  );
}

export { badgeVariants };
