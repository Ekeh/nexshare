"use client";

import { useId, useState } from "react";
import type { DailyPoint } from "@/lib/api";

// Chart-mark colors — brand navy/gold shifted to clear the dataviz skill's
// validator (OKLCH lightness band + chroma floor for categorical marks);
// the raw brand tokens (navy-900, gold-500) are too dark/too light to read
// as chart fills. Values at the bar tip aren't shown (only 7 sparse
// points), so the low mark/surface contrast on gold is offset by the
// legend, axis ticks, and hover tooltip rather than the WARN.
const CLICKS_COLOR = "#4655a0";
const CONVERSIONS_COLOR = "#dba800";

const DAY_LABEL = new Intl.DateTimeFormat("en-US", { weekday: "short" });

function formatDay(iso: string, isToday: boolean): string {
  if (isToday) return "Today";
  const d = new Date(`${iso}T00:00:00`);
  return DAY_LABEL.format(d);
}

export function ClicksVsConversionsChart({ series }: { series: DailyPoint[] }) {
  const [hovered, setHovered] = useState<number | null>(null);
  const titleId = useId();

  const width = 520;
  const height = 220;
  const padding = { top: 12, right: 12, bottom: 28, left: 32 };
  const plotW = width - padding.left - padding.right;
  const plotH = height - padding.top - padding.bottom;

  const maxValue = Math.max(1, ...series.map((d) => Math.max(d.clicks, d.conversions)));
  const yMax = Math.ceil(maxValue / 5) * 5 || 5;
  const yTicks = [0, yMax / 2, yMax];

  const groupW = plotW / series.length;
  const barW = Math.min(24, groupW * 0.28);
  const gap = 3;

  const today = new Date().toISOString().slice(0, 10);
  const scaleY = (v: number) => plotH - (v / yMax) * plotH;

  return (
    <div className="relative">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-labelledby={titleId}
        className="w-full"
        onMouseLeave={() => setHovered(null)}
      >
        <title id={titleId}>Clicks vs conversions, last 7 days</title>
        <g transform={`translate(${padding.left},${padding.top})`}>
          {yTicks.map((t) => (
            <g key={t}>
              <line x1={0} x2={plotW} y1={scaleY(t)} y2={scaleY(t)} stroke="#e5e7eb" strokeWidth={1} />
              <text x={-8} y={scaleY(t)} textAnchor="end" dominantBaseline="middle" className="fill-navy-300 text-[9px]">
                {t}
              </text>
            </g>
          ))}

          {series.map((d, i) => {
            const cx = i * groupW + groupW / 2;
            const clicksX = cx - barW - gap / 2;
            const convX = cx + gap / 2;
            const isHovered = hovered === i;
            return (
              <g key={d.date}>
                <rect
                  x={clicksX}
                  y={scaleY(d.clicks)}
                  width={barW}
                  height={Math.max(0, plotH - scaleY(d.clicks))}
                  rx={3}
                  fill={CLICKS_COLOR}
                  opacity={hovered === null || isHovered ? 1 : 0.5}
                />
                <rect
                  x={convX}
                  y={scaleY(d.conversions)}
                  width={barW}
                  height={Math.max(0, plotH - scaleY(d.conversions))}
                  rx={3}
                  fill={CONVERSIONS_COLOR}
                  opacity={hovered === null || isHovered ? 1 : 0.5}
                />
                <text
                  x={cx}
                  y={plotH + 16}
                  textAnchor="middle"
                  className="fill-navy-300 text-[9px] font-medium"
                >
                  {formatDay(d.date, d.date === today)}
                </text>
                {/* Hit target spans the whole group + margin, bigger than the bars themselves. */}
                <rect
                  x={i * groupW}
                  y={0}
                  width={groupW}
                  height={plotH}
                  fill="transparent"
                  tabIndex={0}
                  onMouseEnter={() => setHovered(i)}
                  onFocus={() => setHovered(i)}
                  onBlur={() => setHovered(null)}
                  aria-label={`${d.date}: ${d.clicks} clicks, ${d.conversions} conversions`}
                />
              </g>
            );
          })}
        </g>
      </svg>

      {hovered !== null && (
        <div
          className="pointer-events-none absolute rounded-lg bg-navy-950 px-3 py-2 text-xs text-white shadow-card-lg"
          style={{
            left: `${((hovered + 0.5) / series.length) * 100}%`,
            top: 0,
            transform: "translate(-50%, -100%)",
          }}
        >
          <div className="font-semibold">{series[hovered].date}</div>
          <div className="mt-1 flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full" style={{ background: CLICKS_COLOR }} />
            Clicks: <span className="font-bold">{series[hovered].clicks}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full" style={{ background: CONVERSIONS_COLOR }} />
            Conversions: <span className="font-bold">{series[hovered].conversions}</span>
          </div>
        </div>
      )}

      <div className="mt-2 flex items-center gap-4 text-xs font-medium text-navy-400">
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full" style={{ background: CLICKS_COLOR }} />
          Clicks
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full" style={{ background: CONVERSIONS_COLOR }} />
          Conversions
        </span>
      </div>
    </div>
  );
}
