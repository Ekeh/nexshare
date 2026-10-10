"use client";

import { useEffect, useState } from "react";
import { CheckCircleIcon } from "@/components/icons";
import { api, ApiError, type Account, type VerificationChannel } from "@/lib/api";

const RESEND_COOLDOWN_SECONDS = 60;

export function VerificationStep({
  pendingToken,
  email,
  phone,
  emailVerified = false,
  phoneVerified = false,
  onVerified,
}: {
  pendingToken: string;
  email: string;
  phone: string;
  /** Skip straight to the "verified" state for a channel that was already
   * done before this step started (e.g. a returning user who finished
   * email earlier) — no code was sent for it this time, so its input
   * would otherwise sit there accepting a code that doesn't exist. */
  emailVerified?: boolean;
  phoneVerified?: boolean;
  onVerified: (account: Account) => void;
}) {
  const bothPending = !emailVerified && !phoneVerified;
  return (
    <div className="flex flex-col gap-5">
      <p className="text-center text-sm text-navy-400">
        {bothPending
          ? "We sent a 6-digit code to your email and phone. Enter both to finish setting up your account."
          : "Enter the code we just sent to finish setting up your account."}
      </p>
      <ChannelVerifier
        channel="email"
        destination={email}
        pendingToken={pendingToken}
        initiallyVerified={emailVerified}
        onVerified={onVerified}
      />
      <ChannelVerifier
        channel="phone"
        destination={phone}
        pendingToken={pendingToken}
        initiallyVerified={phoneVerified}
        onVerified={onVerified}
      />
    </div>
  );
}

function ChannelVerifier({
  channel,
  destination,
  pendingToken,
  initiallyVerified,
  onVerified,
}: {
  channel: VerificationChannel;
  destination: string;
  pendingToken: string;
  initiallyVerified: boolean;
  onVerified: (account: Account) => void;
}) {
  const [code, setCode] = useState("");
  const [done, setDone] = useState(initiallyVerified);
  const [error, setError] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [resending, setResending] = useState(false);
  const [cooldown, setCooldown] = useState(RESEND_COOLDOWN_SECONDS);

  useEffect(() => {
    if (cooldown <= 0) return;
    const id = setInterval(() => setCooldown((c) => c - 1), 1000);
    return () => clearInterval(id);
  }, [cooldown]);

  async function handleVerify(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setVerifying(true);
    try {
      const result = await api.verifyCode(pendingToken, channel, code);
      setDone(true);
      if (result.account) onVerified(result.account);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
    } finally {
      setVerifying(false);
    }
  }

  async function handleResend() {
    setError(null);
    setResending(true);
    setCooldown(RESEND_COOLDOWN_SECONDS);
    try {
      await api.resendCode(pendingToken, channel);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't resend the code.");
    } finally {
      setResending(false);
    }
  }

  if (done) {
    return (
      <div className="flex items-center gap-2 rounded-xl bg-emerald-50 px-4 py-3 text-sm font-semibold text-emerald-600">
        <CheckCircleIcon className="h-5 w-5" />
        {channel === "email" ? "Email" : "Phone"} verified
      </div>
    );
  }

  return (
    <form onSubmit={handleVerify} className="rounded-xl border border-navy-100 p-4">
      <p className="text-xs font-semibold text-navy-600">
        {channel === "email" ? "Email code" : "Phone code"}
      </p>
      <p className="mt-0.5 text-xs text-navy-300">Sent to {destination}</p>
      <div className="mt-2 flex gap-2">
        <input
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
          inputMode="numeric"
          placeholder="123456"
          required
          className="min-w-0 flex-1 rounded-xl border border-navy-100 px-3.5 py-2.5 text-sm tracking-widest text-navy-900 focus:border-navy-400 focus:outline-none"
        />
        <button
          type="submit"
          disabled={verifying || code.length !== 6}
          className="shrink-0 rounded-xl bg-cta-gradient px-4 py-2.5 text-sm font-bold text-navy-900 shadow-card transition hover:brightness-105 disabled:opacity-60"
        >
          {verifying ? "Verifying…" : "Verify"}
        </button>
      </div>
      {error && <p className="mt-2 text-xs font-medium text-red-500">{error}</p>}
      <button
        type="button"
        onClick={handleResend}
        disabled={resending || cooldown > 0}
        className="mt-2 text-xs font-semibold text-navy-400 hover:text-navy-700 disabled:cursor-not-allowed disabled:text-navy-300"
      >
        {cooldown > 0 ? `Resend code (${cooldown}s)` : "Resend code"}
      </button>
    </form>
  );
}
