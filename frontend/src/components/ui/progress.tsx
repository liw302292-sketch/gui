import { cn } from "@/lib/utils";

export function Progress({
  value,
  className,
  tone = "accent",
}: {
  value: number;
  className?: string;
  tone?: "accent" | "success" | "warning" | "danger";
}) {
  const percent = Math.min(Math.max(value, 0), 1) * 100;
  const tones = {
    accent: "bg-accent",
    success: "bg-success",
    warning: "bg-warning",
    danger: "bg-danger",
  }[tone];
  return (
    <div className={cn("h-2 w-full overflow-hidden rounded-full bg-line/70", className)}>
      <div
        className={cn("h-full rounded-full transition-[width] duration-500", tones)}
        style={{ width: `${percent}%` }}
      />
    </div>
  );
}

