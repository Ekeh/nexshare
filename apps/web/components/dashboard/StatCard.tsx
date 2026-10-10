import { ArrowUpRightIcon } from "@/components/icons";

export function StatCard({
  value,
  label,
  deltaPct,
}: {
  value: string;
  label: string;
  deltaPct?: number | null;
}) {
  const isNegative = typeof deltaPct === "number" && deltaPct < 0;

  return (
    <div className="rounded-2xl bg-white p-5 shadow-card">
      <div className="text-2xl font-extrabold text-navy-900">{value}</div>
      <div className="mt-1 text-xs font-medium text-navy-400">{label}</div>
      {typeof deltaPct === "number" ? (
        <div
          className={`mt-3 flex items-center gap-1 text-xs font-bold ${
            isNegative ? "text-red-500" : "text-emerald-500"
          }`}
        >
          <ArrowUpRightIcon className={`h-3.5 w-3.5 ${isNegative ? "rotate-90" : ""}`} />
          {isNegative ? deltaPct : `+${deltaPct}`}%
        </div>
      ) : (
        <div className="mt-3 text-xs font-bold text-navy-300">—</div>
      )}
    </div>
  );
}
