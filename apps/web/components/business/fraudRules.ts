import type { FraudSeverity } from "@/lib/api";

// Mirrors the rules in apps/api/app/services/fraud.py — keep in sync if a
// new rule is added there.
export const FRAUD_RULE_LABELS: Record<string, string> = {
  instant_conversion: "Instant Conversion",
  velocity_abuse: "High Velocity",
};

export function fraudRuleLabel(rule: string): string {
  return FRAUD_RULE_LABELS[rule] ?? rule.replace(/_/g, " ");
}

export const FRAUD_SEVERITY_META: Record<FraudSeverity, { bg: string; fg: string }> = {
  high: { bg: "bg-red-50", fg: "text-red-600" },
  medium: { bg: "bg-orange-50", fg: "text-orange-600" },
  low: { bg: "bg-amber-50", fg: "text-amber-600" },
};
