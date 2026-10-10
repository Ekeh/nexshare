import type { SourceBreakdown } from "@/lib/api";

// Reuses the same per-platform brand colors as ShareChannels.tsx, so a
// channel reads as the same color everywhere it appears in the dashboard.
const CHANNEL_META: Record<string, { label: string; color: string }> = {
  whatsapp: { label: "WhatsApp", color: "#25D366" },
  facebook: { label: "Facebook", color: "#1877F2" },
  x: { label: "X", color: "#0d1642" },
  telegram: { label: "Telegram", color: "#229ED9" },
  sms: { label: "SMS", color: "#293878" },
  email: { label: "Email", color: "#293878" },
  instagram: { label: "Instagram", color: "#d6249f" },
  tiktok: { label: "TikTok", color: "#0d1642" },
  other: { label: "Other / Direct", color: "#94a3b8" },
};

export function TopSources({ sources }: { sources: SourceBreakdown[] }) {
  if (sources.length === 0) {
    return <p className="text-sm font-medium text-navy-300">No clicks yet this week.</p>;
  }

  return (
    <div className="flex flex-col gap-3">
      {sources.map((s) => {
        const meta = CHANNEL_META[s.channel] ?? { label: s.channel, color: "#94a3b8" };
        return (
          <div key={s.channel}>
            <div className="mb-1 flex items-center justify-between text-xs font-semibold text-navy-700">
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full" style={{ background: meta.color }} />
                {meta.label}
              </span>
              <span className="text-navy-400">{s.pct}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full"
                style={{ width: `${s.pct}%`, background: meta.color }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
