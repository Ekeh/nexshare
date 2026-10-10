"use client";

import { useEffect, useState } from "react";
import {
  api,
  ApiError,
  formatMoney,
  type Bank,
  type Commission,
  type Payout,
  type PayoutAccount,
  type PayoutMethod,
} from "@/lib/api";

const PAYOUT_METHODS: { value: PayoutMethod; label: string }[] = [
  { value: "bank_transfer", label: "Bank Transfer" },
  { value: "mobile_money", label: "Mobile Money" },
];

const PAYOUT_STATUS_META: Record<string, { label: string; bg: string; fg: string }> = {
  requested: { label: "Requested", bg: "bg-slate-100", fg: "text-slate-500" },
  processing: { label: "Processing", bg: "bg-blue-50", fg: "text-blue-600" },
  completed: { label: "Completed", bg: "bg-emerald-50", fg: "text-emerald-600" },
  failed: { label: "Failed", bg: "bg-red-50", fg: "text-red-600" },
};

export default function WithdrawPage() {
  const [commissions, setCommissions] = useState<Commission[] | null>(null);
  const [payouts, setPayouts] = useState<Payout[] | null>(null);
  const [method, setMethod] = useState<PayoutMethod>("bank_transfer");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [justRequested, setJustRequested] = useState(false);

  // null = Paystack isn't configured in this environment (banks endpoint
  // 503s) — fall back to the plain method-toggle flow with no real payout
  // destination, exactly how withdrawing worked before this was wired up.
  const [banksAvailable, setBanksAvailable] = useState<boolean | null>(null);
  const [payoutAccount, setPayoutAccount] = useState<PayoutAccount | null | undefined>(undefined);

  function load() {
    api.commissions().then(setCommissions).catch(() => setError("Couldn't load your balance. Try refreshing."));
    api.payouts().then(setPayouts).catch(() => undefined);
  }

  useEffect(load, []);

  useEffect(() => {
    api
      .payoutBanks()
      .then(() => setBanksAvailable(true))
      .catch(() => setBanksAvailable(false));
    api
      .payoutAccount()
      .then(setPayoutAccount)
      .catch(() => setPayoutAccount(null));
  }, []);

  const currency = commissions?.find((c) => c.status === "available")?.currency ?? "USD";
  const available = (commissions ?? [])
    .filter((c) => c.status === "available")
    .reduce((sum, c) => sum + c.amount_minor_units, 0);

  const requiresPayoutAccount = banksAvailable === true;
  const readyToWithdraw = !requiresPayoutAccount || !!payoutAccount;

  async function handleWithdraw() {
    setSubmitting(true);
    setError(null);
    setJustRequested(false);
    try {
      await api.requestWithdrawal(requiresPayoutAccount ? "bank_transfer" : method);
      setJustRequested(true);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't submit that withdrawal. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-extrabold text-navy-900">Withdraw</h1>
      <p className="mt-1 text-sm text-navy-400">Move your available balance to your bank or mobile money account.</p>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr,1.3fr]">
        <div className="flex flex-col gap-6">
          <section className="rounded-2xl bg-white p-6 shadow-card">
            <p className="text-xs font-semibold uppercase tracking-wide text-navy-300">Available Balance</p>
            {commissions ? (
              <div className="mt-2 text-4xl font-extrabold text-navy-900">
                {formatMoney({ amount_minor_units: available, currency, change_pct: null })}
              </div>
            ) : (
              <div className="mt-2 h-10 w-40 animate-pulse rounded-lg bg-slate-100" />
            )}

            {!requiresPayoutAccount && (
              <>
                <p className="mt-4 text-xs font-semibold text-navy-600">Payout Method</p>
                <div className="mt-2 flex gap-2">
                  {PAYOUT_METHODS.map((m) => (
                    <button
                      key={m.value}
                      type="button"
                      onClick={() => setMethod(m.value)}
                      className={`rounded-full px-4 py-1.5 text-xs font-bold transition ${
                        method === m.value
                          ? "bg-navy-900 text-white"
                          : "border border-navy-100 bg-white text-navy-400 hover:bg-slate-50"
                      }`}
                    >
                      {m.label}
                    </button>
                  ))}
                </div>
              </>
            )}

            {error && <p className="mt-3 text-xs font-medium text-red-500">{error}</p>}
            {justRequested && (
              <p className="mt-3 text-xs font-medium text-emerald-600">
                Withdrawal requested — it&rsquo;ll show below once it&rsquo;s processed.
              </p>
            )}

            <button
              type="button"
              onClick={handleWithdraw}
              disabled={!commissions || available <= 0 || submitting || !readyToWithdraw}
              className="mt-5 w-full rounded-full bg-cta-gradient py-3 text-sm font-bold text-navy-900 shadow-card transition hover:brightness-105 disabled:opacity-50"
            >
              {submitting ? "Submitting…" : "Withdraw Available Balance"}
            </button>
            {commissions && available <= 0 && (
              <p className="mt-2 text-center text-xs text-navy-300">Nothing available to withdraw yet.</p>
            )}
            {requiresPayoutAccount && !payoutAccount && (
              <p className="mt-2 text-center text-xs text-navy-300">Add a payout account below first.</p>
            )}
          </section>

          {banksAvailable && (
            <PayoutAccountCard
              account={payoutAccount ?? null}
              onSaved={(pa) => setPayoutAccount(pa)}
            />
          )}
        </div>

        <section>
          <h2 className="text-sm font-bold text-navy-900">Payout History</h2>
          <div className="mt-3 flex flex-col gap-3">
            {payouts ? (
              payouts.length > 0 ? (
                payouts.map((p) => {
                  const meta = PAYOUT_STATUS_META[p.status] ?? {
                    label: p.status,
                    bg: "bg-blue-50",
                    fg: "text-blue-600",
                  };
                  return (
                    <div key={p.id} className="rounded-2xl bg-white p-4 shadow-card">
                      <div className="flex items-center gap-4">
                        <div className="min-w-0 flex-1">
                          <div className="text-sm font-bold text-navy-900">
                            {p.payout_method === "bank_transfer" ? "Bank Transfer" : "Mobile Money"}
                          </div>
                          <div className="mt-0.5 text-xs font-medium text-navy-400">
                            {new Date(p.requested_at).toLocaleDateString("en-US", {
                              month: "short",
                              day: "numeric",
                              year: "numeric",
                            })}
                          </div>
                        </div>
                        <div className="text-sm font-semibold text-navy-900">
                          {formatMoney({ amount_minor_units: p.amount_minor_units, currency: p.currency, change_pct: null })}
                        </div>
                        <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${meta.bg} ${meta.fg}`}>
                          {meta.label}
                        </span>
                      </div>
                      {p.status === "failed" && p.failure_reason && (
                        <p className="mt-2 text-xs font-medium text-red-500">{p.failure_reason}</p>
                      )}
                    </div>
                  );
                })
              ) : (
                <p className="text-sm font-medium text-navy-300">No withdrawals yet.</p>
              )
            ) : (
              <div className="h-16 animate-pulse rounded-2xl bg-white shadow-card" />
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

function PayoutAccountCard({
  account,
  onSaved,
}: {
  account: PayoutAccount | null;
  onSaved: (account: PayoutAccount) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [banks, setBanks] = useState<Bank[] | null>(null);
  const [bankCode, setBankCode] = useState("");
  const [accountNumber, setAccountNumber] = useState("");
  const [resolvedName, setResolvedName] = useState<string | null>(null);
  const [resolving, setResolving] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (editing && banks === null) {
      api.payoutBanks().then(setBanks).catch(() => setError("Couldn't load the bank list. Try again."));
    }
  }, [editing, banks]);

  async function handleVerify() {
    setError(null);
    setResolvedName(null);
    if (!bankCode || accountNumber.trim().length < 10) {
      setError("Choose a bank and enter a valid account number.");
      return;
    }
    setResolving(true);
    try {
      const { account_name } = await api.resolvePayoutAccount(bankCode, accountNumber.trim());
      setResolvedName(account_name);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't verify that account.");
    } finally {
      setResolving(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const saved = await api.savePayoutAccount({
        payout_method: "bank_transfer",
        bank_code: bankCode,
        account_number: accountNumber.trim(),
      });
      onSaved(saved);
      setEditing(false);
      setResolvedName(null);
      setAccountNumber("");
      setBankCode("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't save that payout account.");
    } finally {
      setSaving(false);
    }
  }

  if (!editing) {
    return (
      <section className="rounded-2xl bg-white p-6 shadow-card">
        <p className="text-xs font-semibold uppercase tracking-wide text-navy-300">Payout Account</p>
        {account ? (
          <div className="mt-3 flex items-center justify-between gap-4">
            <div className="min-w-0">
              <div className="truncate text-sm font-bold text-navy-900">{account.account_name}</div>
              <div className="mt-0.5 text-xs font-medium text-navy-400">
                {account.bank_name} · {account.account_number_masked}
              </div>
            </div>
            <button
              type="button"
              onClick={() => setEditing(true)}
              className="shrink-0 rounded-full border border-navy-100 px-3.5 py-2 text-xs font-bold text-navy-600 transition hover:bg-slate-50"
            >
              Change
            </button>
          </div>
        ) : (
          <div className="mt-3 flex items-center justify-between gap-4">
            <p className="text-sm font-medium text-navy-400">No payout account saved yet.</p>
            <button
              type="button"
              onClick={() => setEditing(true)}
              className="shrink-0 rounded-full bg-cta-gradient px-4 py-2 text-xs font-bold text-navy-900 shadow-card transition hover:brightness-105"
            >
              Add Account
            </button>
          </div>
        )}
      </section>
    );
  }

  return (
    <section className="rounded-2xl bg-white p-6 shadow-card">
      <p className="text-xs font-semibold uppercase tracking-wide text-navy-300">
        {account ? "Change Payout Account" : "Add Payout Account"}
      </p>

      <div className="mt-3 flex flex-col gap-3">
        <div>
          <label htmlFor="bank" className="block text-xs font-semibold text-navy-600">
            Bank
          </label>
          <select
            id="bank"
            value={bankCode}
            onChange={(e) => {
              setBankCode(e.target.value);
              setResolvedName(null);
            }}
            className="mt-1.5 w-full rounded-xl border border-navy-100 bg-white px-3.5 py-2.5 text-sm text-navy-900 focus:border-navy-400 focus:outline-none"
          >
            <option value="">{banks ? "Select a bank" : "Loading banks…"}</option>
            {banks?.map((b) => (
              <option key={b.code} value={b.code}>
                {b.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="account-number" className="block text-xs font-semibold text-navy-600">
            Account Number
          </label>
          <input
            id="account-number"
            value={accountNumber}
            onChange={(e) => {
              setAccountNumber(e.target.value);
              setResolvedName(null);
            }}
            placeholder="0000000000"
            className="mt-1.5 w-full rounded-xl border border-navy-100 px-3.5 py-2.5 text-sm text-navy-900 focus:border-navy-400 focus:outline-none"
          />
        </div>

        {resolvedName && (
          <p className="text-xs font-semibold text-emerald-600">Verified: {resolvedName}</p>
        )}
        {error && <p className="text-xs font-medium text-red-500">{error}</p>}

        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => {
              setEditing(false);
              setError(null);
              setResolvedName(null);
            }}
            className="flex-1 rounded-full border border-navy-100 py-2.5 text-xs font-bold text-navy-600 transition hover:bg-slate-50"
          >
            Cancel
          </button>
          {resolvedName ? (
            <button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className="flex-1 rounded-full bg-cta-gradient py-2.5 text-xs font-bold text-navy-900 shadow-card transition hover:brightness-105 disabled:opacity-50"
            >
              {saving ? "Saving…" : "Save"}
            </button>
          ) : (
            <button
              type="button"
              onClick={handleVerify}
              disabled={resolving}
              className="flex-1 rounded-full bg-cta-gradient py-2.5 text-xs font-bold text-navy-900 shadow-card transition hover:brightness-105 disabled:opacity-50"
            >
              {resolving ? "Verifying…" : "Verify"}
            </button>
          )}
        </div>
      </div>
    </section>
  );
}
