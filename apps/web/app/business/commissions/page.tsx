"use client";

import { useEffect, useMemo, useState } from "react";
import { COMMISSION_STATUS_META } from "@/components/dashboard/commissionStatus";
import { FRAUD_SEVERITY_META, fraudRuleLabel } from "@/components/business/fraudRules";
import { CheckIcon, CopyIcon } from "@/components/icons";
import { api, formatMoney, type BusinessCommission, type CommissionStatus, type FraudFlag } from "@/lib/api";

const FILTERS: { value: CommissionStatus | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "pending", label: "Pending" },
  { value: "approved", label: "Approved" },
  { value: "available", label: "Available" },
  { value: "paid", label: "Paid" },
  { value: "rejected", label: "Rejected" },
  { value: "reversed", label: "Reversed" },
];

// Once a commission has earned (approved/available/paid) a business can
// still reverse it for a refund/chargeback — see transition() in
// commission_lifecycle.py. pending is decided via approve/reject instead;
// rejected/reversed are terminal.
const REVERSIBLE_STATUSES: CommissionStatus[] = ["approved", "available", "paid"];

export default function BusinessCommissionsPage() {
  const [commissions, setCommissions] = useState<BusinessCommission[] | null>(null);
  const [flags, setFlags] = useState<FraudFlag[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<CommissionStatus | "all">("all");
  const [actingId, setActingId] = useState<string | null>(null);

  function load() {
    api
      .businessCommissions()
      .then(setCommissions)
      .catch(() => setError("Couldn't load commissions. Try refreshing."));
    api.fraudFlags().then(setFlags).catch(() => undefined);
  }

  useEffect(load, []);

  const visible = useMemo(
    () => (filter === "all" ? commissions ?? [] : (commissions ?? []).filter((c) => c.status === filter)),
    [commissions, filter]
  );

  const unresolvedFlagsByCommission = useMemo(() => {
    const map = new Map<string, FraudFlag[]>();
    for (const flag of flags) {
      if (flag.resolved) continue;
      const existing = map.get(flag.commission_id) ?? [];
      existing.push(flag);
      map.set(flag.commission_id, existing);
    }
    return map;
  }, [flags]);

  async function act(id: string, action: "approve" | "reject" | "reverse") {
    setActingId(id);
    setError(null);
    try {
      const updated =
        action === "approve"
          ? await api.approveCommission(id)
          : action === "reject"
            ? await api.rejectCommission(id)
            : await api.reverseCommission(id);
      setCommissions((prev) => (prev ?? []).map((c) => (c.id === id ? updated : c)));
    } catch {
      setError("That action couldn't be completed. Try again.");
    } finally {
      setActingId(null);
    }
  }

  async function clearFlags(commissionFlags: FraudFlag[]) {
    const ids = commissionFlags.map((f) => f.id);
    setActingId(commissionFlags[0].commission_id);
    setError(null);
    try {
      await Promise.all(ids.map((id) => api.resolveFraudFlag(id)));
      setFlags((prev) => prev.map((f) => (ids.includes(f.id) ? { ...f, resolved: true } : f)));
    } catch {
      setError("Couldn't clear that flag. Try again.");
    } finally {
      setActingId(null);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-extrabold text-navy-900">Commissions</h1>
      <p className="mt-1 text-sm text-navy-400">Review and act on commissions earned against your offers.</p>

      <WebhookSecretCard />

      <div className="mt-8 flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            type="button"
            onClick={() => setFilter(f.value)}
            className={`rounded-full px-4 py-1.5 text-xs font-bold transition ${
              filter === f.value ? "bg-navy-900 text-white" : "border border-navy-100 bg-white text-navy-400 hover:bg-slate-50"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && <p className="mt-6 text-sm font-medium text-red-500">{error}</p>}

      <div className="mt-6 flex flex-col gap-3">
        {commissions ? (
          visible.length > 0 ? (
            visible.map((c) => {
              const meta = COMMISSION_STATUS_META[c.status];
              const busy = actingId === c.id;
              const commissionFlags = unresolvedFlagsByCommission.get(c.id) ?? [];
              return (
                <div key={c.id} className="rounded-2xl bg-white p-4 shadow-card">
                  <div className="flex flex-wrap items-center gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-bold text-navy-900">{c.offer_title}</div>
                      <div className="mt-0.5 truncate text-xs font-medium text-navy-400">
                        {c.promoter_name} ·{" "}
                        {new Date(c.created_at).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                        })}
                      </div>
                    </div>
                    <div className="text-sm font-semibold text-navy-900">
                      {formatMoney({ amount_minor_units: c.amount_minor_units, currency: c.currency, change_pct: null })}
                    </div>
                    <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${meta.bg} ${meta.fg}`}>{meta.label}</span>

                    <div className="flex shrink-0 gap-2">
                      {c.status === "pending" && (
                        <>
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => act(c.id, "reject")}
                            className="rounded-full border border-navy-100 px-3.5 py-2 text-xs font-bold text-navy-600 transition hover:bg-slate-50 disabled:opacity-50"
                          >
                            Reject
                          </button>
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => act(c.id, "approve")}
                            className="rounded-full bg-cta-gradient px-3.5 py-2 text-xs font-bold text-navy-900 shadow-card transition hover:brightness-105 disabled:opacity-50"
                          >
                            Approve
                          </button>
                        </>
                      )}
                      {REVERSIBLE_STATUSES.includes(c.status) && (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => act(c.id, "reverse")}
                          className="rounded-full border border-red-100 px-3.5 py-2 text-xs font-bold text-red-500 transition hover:bg-red-50 disabled:opacity-50"
                        >
                          Reverse
                        </button>
                      )}
                    </div>
                  </div>

                  {commissionFlags.length > 0 && (
                    <div className="mt-3 flex flex-wrap items-center gap-2 rounded-xl bg-red-50/60 px-3 py-2">
                      <span className="text-xs font-bold text-red-600">⚠ Flagged:</span>
                      {commissionFlags.map((f) => {
                        const sevMeta = FRAUD_SEVERITY_META[f.severity];
                        return (
                          <span key={f.id} className={`rounded-full px-2 py-0.5 text-xs font-bold ${sevMeta.bg} ${sevMeta.fg}`}>
                            {fraudRuleLabel(f.rule_triggered)}
                          </span>
                        );
                      })}
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => clearFlags(commissionFlags)}
                        className="ml-auto rounded-full border border-navy-100 bg-white px-3 py-1 text-xs font-bold text-navy-600 transition hover:bg-slate-50 disabled:opacity-50"
                      >
                        Clear Flag{commissionFlags.length > 1 ? "s" : ""}
                      </button>
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <p className="text-sm font-medium text-navy-300">No commissions in this category yet.</p>
          )
        ) : (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-[68px] animate-pulse rounded-2xl bg-white shadow-card" />
          ))
        )}
      </div>
    </div>
  );
}

function WebhookSecretCard() {
  const [secret, setSecret] = useState<string | null>(null);
  const [revealed, setRevealed] = useState(false);
  const [copied, setCopied] = useState(false);
  const [confirmingRotate, setConfirmingRotate] = useState(false);
  const [rotating, setRotating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.webhookSecret().then((s) => setSecret(s.webhook_secret)).catch(() => setError("Couldn't load your webhook secret."));
  }, []);

  async function handleRotate() {
    if (!confirmingRotate) {
      setConfirmingRotate(true);
      setTimeout(() => setConfirmingRotate(false), 4000);
      return;
    }
    setRotating(true);
    setError(null);
    try {
      const s = await api.rotateWebhookSecret();
      setSecret(s.webhook_secret);
      setRevealed(true);
    } catch {
      setError("Couldn't rotate the secret. Try again.");
    } finally {
      setRotating(false);
      setConfirmingRotate(false);
    }
  }

  const masked = secret ? `${secret.slice(0, 9)}${"•".repeat(24)}` : "";

  return (
    <div className="mt-6 rounded-2xl bg-white p-4 shadow-card">
      <p className="text-xs font-semibold uppercase tracking-wide text-navy-300">Webhook Secret</p>
      <p className="mt-1 text-xs font-medium text-navy-400">
        Used to authenticate <code className="rounded bg-slate-50 px-1 py-0.5 text-navy-600">POST /api/webhooks/conversions</code> calls from your checkout.
      </p>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <div className="min-w-0 flex-1 truncate rounded-xl border border-navy-100 px-3.5 py-2.5 text-sm font-medium text-navy-600">
          {secret ? (revealed ? secret : masked) : "Loading…"}
        </div>
        <button
          type="button"
          disabled={!secret}
          onClick={() => setRevealed((r) => !r)}
          className="rounded-full border border-navy-100 px-3.5 py-2 text-xs font-bold text-navy-600 transition hover:bg-slate-50 disabled:opacity-50"
        >
          {revealed ? "Hide" : "Show"}
        </button>
        <button
          type="button"
          disabled={!secret}
          onClick={() => {
            if (!secret) return;
            navigator.clipboard.writeText(secret);
            setCopied(true);
            setTimeout(() => setCopied(false), 1800);
          }}
          className="flex items-center gap-1.5 rounded-full border border-navy-100 px-3.5 py-2 text-xs font-bold text-navy-600 transition hover:bg-slate-50 disabled:opacity-50"
        >
          {copied ? <CheckIcon className="h-3.5 w-3.5" /> : <CopyIcon className="h-3.5 w-3.5" />}
          {copied ? "Copied" : "Copy"}
        </button>
        <button
          type="button"
          disabled={!secret || rotating}
          onClick={handleRotate}
          className={`rounded-full px-3.5 py-2 text-xs font-bold transition disabled:opacity-50 ${
            confirmingRotate ? "bg-red-500 text-white hover:bg-red-600" : "border border-red-100 text-red-500 hover:bg-red-50"
          }`}
        >
          {rotating ? "Rotating…" : confirmingRotate ? "Confirm Rotate" : "Rotate"}
        </button>
      </div>
      {confirmingRotate && (
        <p className="mt-2 text-xs font-medium text-red-500">
          Rotating invalidates the current secret immediately — your checkout integration must be updated too.
        </p>
      )}
      {error && <p className="mt-2 text-xs font-medium text-red-500">{error}</p>}
    </div>
  );
}
