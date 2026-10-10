import type { CommissionStatus } from "@/lib/api";

export interface CommissionStatusMeta {
  label: string;
  bg: string;
  fg: string;
}

// Mirrors the lifecycle in app/services/commission_lifecycle.py:
// pending -> approved -> available -> paid, with rejected (from pending)
// and reversed (from approved/available/paid) as the two exit branches.
export const COMMISSION_STATUS_META: Record<CommissionStatus, CommissionStatusMeta> = {
  pending: { label: "Pending", bg: "bg-slate-100", fg: "text-slate-500" },
  approved: { label: "Approved", bg: "bg-blue-50", fg: "text-blue-600" },
  available: { label: "Available", bg: "bg-emerald-50", fg: "text-emerald-600" },
  paid: { label: "Paid", bg: "bg-teal-50", fg: "text-teal-600" },
  rejected: { label: "Rejected", bg: "bg-red-50", fg: "text-red-600" },
  reversed: { label: "Reversed", bg: "bg-orange-50", fg: "text-orange-600" },
};
