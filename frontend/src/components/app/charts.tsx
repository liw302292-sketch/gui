"use client";

import * as React from "react";

import { cn, formatAmount } from "@/lib/utils";

interface Point {
  label: string;
  value: number;
  secondary?: number;
}

/** 轻量 SVG 折线/面积图：无第三方依赖，Linear 风格细线 + 柔和渐变。 */
export function AreaTrendChart({
  data,
  height = 200,
  showSecondary = false,
  valueFormatter = (value: number) => formatAmount(value),
  className,
}: {
  data: Point[];
  height?: number;
  showSecondary?: boolean;
  valueFormatter?: (value: number) => string;
  className?: string;
}) {
  const [hover, setHover] = React.useState<number | null>(null);
  const width = 720;
  const padding = { top: 16, right: 12, bottom: 26, left: 44 };
  const innerW = width - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;

  const maxValue = Math.max(...data.map((point) => Math.max(point.value, point.secondary ?? 0)), 1);
  const step = data.length > 1 ? innerW / (data.length - 1) : innerW;

  const toXY = (index: number, value: number) => ({
    x: padding.left + index * step,
    y: padding.top + innerH - (value / maxValue) * innerH,
  });

  const linePath = (key: "value" | "secondary") =>
    data
      .map((point, index) => {
        const value = key === "value" ? point.value : (point.secondary ?? 0);
        const { x, y } = toXY(index, value);
        return `${index === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");

  const areaPath = `${linePath("value")} L${(padding.left + (data.length - 1) * step).toFixed(1)},${(padding.top + innerH).toFixed(1)} L${padding.left},${(padding.top + innerH).toFixed(1)} Z`;

  return (
    <div className={cn("relative w-full", className)}>
      <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full" role="img" aria-label="趋势图">
        <defs>
          <linearGradient id="area-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#635BFF" stopOpacity="0.18" />
            <stop offset="100%" stopColor="#635BFF" stopOpacity="0" />
          </linearGradient>
        </defs>

        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
          const y = padding.top + innerH - ratio * innerH;
          return (
            <g key={ratio}>
              <line x1={padding.left} x2={width - padding.right} y1={y} y2={y} stroke="#EDEFF5" strokeWidth="1" />
              <text x={padding.left - 8} y={y + 3.5} textAnchor="end" fontSize="10" fill="#9CA3AF">
                {valueFormatter(maxValue * ratio)}
              </text>
            </g>
          );
        })}

        <path d={areaPath} fill="url(#area-fill)" />
        {showSecondary ? (
          <path d={linePath("secondary")} fill="none" stroke="#12A150" strokeWidth="1.6" strokeDasharray="4 4" />
        ) : null}
        <path d={linePath("value")} fill="none" stroke="#635BFF" strokeWidth="2" strokeLinecap="round" />

        {data.map((point, index) => {
          const { x, y } = toXY(index, point.value);
          const stepLabel = Math.ceil(data.length / 7);
          const showLabel = index % stepLabel === 0 || index === data.length - 1;
          return (
            <g key={point.label}>
              <text x={x} y={height - 8} textAnchor="middle" fontSize="10" fill="#9CA3AF">
                {showLabel ? point.label : ""}
              </text>
              <circle cx={x} cy={y} r={hover === index ? 4.5 : 0} fill="#635BFF" stroke="#fff" strokeWidth="2" />
              <rect
                x={x - step / 2}
                y={padding.top}
                width={step}
                height={innerH}
                fill="transparent"
                onMouseEnter={() => setHover(index)}
                onMouseLeave={() => setHover(null)}
              />
            </g>
          );
        })}
      </svg>

      {hover !== null && data[hover] ? (
        <div
          className="pointer-events-none absolute top-1 z-10 -translate-x-1/2 rounded-lg border border-line bg-surface px-3 py-1.5 text-[12px] shadow-[var(--shadow-card)]"
          style={{ left: `${((padding.left + hover * step) / width) * 100}%` }}
        >
          <div className="text-faint">{data[hover]!.label}</div>
          <div className="font-medium text-ink">¥{formatAmount(data[hover]!.value)}</div>
        </div>
      ) : null}
    </div>
  );
}

export function FunnelChart({ data }: { data: { stage: string; value: number }[] }) {
  const max = Math.max(...data.map((item) => item.value), 1);
  return (
    <div className="space-y-3">
      {data.map((item, index) => {
        const ratio = item.value / max;
        const previous = index > 0 ? data[index - 1]!.value : item.value;
        const conversion = previous > 0 ? item.value / previous : 0;
        return (
          <div key={item.stage}>
            <div className="mb-1.5 flex items-center justify-between text-[12.5px]">
              <span className="font-medium text-ink-soft">{item.stage}</span>
              <span className="text-muted">
                {item.value}
                {index > 0 ? <span className="ml-2 text-faint">转化 {(conversion * 100).toFixed(0)}%</span> : null}
              </span>
            </div>
            <div className="h-2.5 w-full overflow-hidden rounded-full bg-line/60">
              <div
                className="h-full rounded-full bg-gradient-to-r from-[#7c74ff] to-[#635BFF] transition-[width] duration-700"
                style={{ width: `${Math.max(ratio * 100, item.value > 0 ? 6 : 0)}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function BarList({
  data,
  formatter = (value: number) => `¥${formatAmount(value)}`,
}: {
  data: { label: string; value: number; hint?: string }[];
  formatter?: (value: number) => string;
}) {
  const max = Math.max(...data.map((item) => item.value), 1);
  return (
    <div className="space-y-2.5">
      {data.map((item) => (
        <div key={item.label} className="flex items-center gap-3">
          <span className="w-24 shrink-0 truncate text-[13px] text-ink-soft">{item.label}</span>
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-line/60">
            <div
              className="h-full rounded-full bg-accent/80"
              style={{ width: `${Math.max((item.value / max) * 100, item.value > 0 ? 4 : 0)}%` }}
            />
          </div>
          <span className="w-24 shrink-0 text-right text-[12.5px] tabular-nums text-muted">{formatter(item.value)}</span>
        </div>
      ))}
    </div>
  );
}

