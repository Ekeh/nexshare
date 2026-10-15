"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Logo } from "@/components/Logo";
import { VerificationStep } from "@/components/VerificationStep";
import { api, ApiError, type PendingVerification } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [pending, setPending] = useState<PendingVerification | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const account = await api.login(email, password);
      router.push(account.role === "business" ? "/business" : "/dashboard");
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        // Right credentials, but email/phone verification was never
        // finished — recover a fresh pending token so they can pick up
        // where they left off instead of dead-ending on the error.
        try {
          setPending(await api.verifyStart(email, password));
        } catch (startErr) {
          setError(startErr instanceof ApiError ? startErr.message : "Something went wrong. Please try again.");
        }
      } else {
        setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  if (pending) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-hero-gradient px-6 py-12">
        <div className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-card-lg">
          <div className="flex justify-center">
            <Logo dark tagline={false} />
          </div>
          <h1 className="mt-6 text-center text-xl font-extrabold text-navy-900">Verify your account</h1>
          <p className="mt-1 text-center text-sm text-navy-400">Almost there — finish verifying to log in.</p>
          <div className="mt-6">
            <VerificationStep
              pendingToken={pending.pending_verification_token}
              email={pending.email}
              phone={pending.phone}
              emailVerified={pending.email_verified}
              phoneVerified={pending.phone_verified}
              emailTestCode={pending.email_test_code}
              phoneTestCode={pending.phone_test_code}
              onVerified={(account) => router.push(account.role === "business" ? "/business" : "/dashboard")}
            />
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-hero-gradient px-6 py-12">
      <div className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-card-lg">
        <div className="flex justify-center">
          <Logo dark tagline={false} />
        </div>
        <h1 className="mt-6 text-center text-xl font-extrabold text-navy-900">
          Welcome back, Promoter
        </h1>
        <p className="mt-1 text-center text-sm text-navy-400">
          Log in to keep sharing and earning.
        </p>

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="email" className="block text-xs font-semibold text-navy-600">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="mt-1.5 w-full rounded-xl border border-navy-100 px-3.5 py-2.5 text-sm text-navy-900 focus:border-navy-400 focus:outline-none"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-xs font-semibold text-navy-600">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              className="mt-1.5 w-full rounded-xl border border-navy-100 px-3.5 py-2.5 text-sm text-navy-900 focus:border-navy-400 focus:outline-none"
            />
          </div>

          {error && <p className="text-sm font-medium text-red-500">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-full bg-cta-gradient py-3 text-sm font-bold text-navy-900 shadow-card transition hover:brightness-105 disabled:opacity-60"
          >
            {loading ? "Logging in..." : "Log In"}
          </button>
        </form>

        <p className="mt-5 text-center text-xs text-navy-400">
          Don&rsquo;t have an account?{" "}
          <Link href="/register" className="font-semibold text-navy-600 hover:text-navy-900">
            Sign up
          </Link>
        </p>
        <p className="mt-2 text-center text-xs text-navy-400">
          <Link href="/" className="font-semibold text-navy-600 hover:text-navy-900">
            ← Back to home
          </Link>
        </p>
      </div>
    </main>
  );
}
