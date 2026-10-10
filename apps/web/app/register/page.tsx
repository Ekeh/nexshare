"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Logo } from "@/components/Logo";
import { VerificationStep } from "@/components/VerificationStep";
import { api, ApiError, type PendingVerification } from "@/lib/api";

type Role = "promoter" | "business";

function RegisterForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialRole: Role = searchParams.get("role") === "business" ? "business" : "promoter";

  const [role, setRole] = useState<Role>(initialRole);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [pending, setPending] = useState<PendingVerification | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await api.register({ email, phone, password, full_name: fullName, role });
      setPending(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
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
          <div className="mt-6">
            <VerificationStep
              pendingToken={pending.pending_verification_token}
              email={pending.email}
              phone={pending.phone}
              onVerified={(account) => router.push(account.role === "promoter" ? "/dashboard" : "/business")}
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
        <h1 className="mt-6 text-center text-xl font-extrabold text-navy-900">Create your account</h1>
        <p className="mt-1 text-center text-sm text-navy-400">Join the movement, earn from results.</p>

        <div className="mt-5 grid grid-cols-2 gap-2 rounded-full bg-slate-100 p-1">
          <button
            type="button"
            onClick={() => setRole("promoter")}
            className={`rounded-full py-2 text-sm font-bold transition ${
              role === "promoter" ? "bg-white text-navy-900 shadow-card" : "text-navy-400"
            }`}
          >
            I&rsquo;m a Promoter
          </button>
          <button
            type="button"
            onClick={() => setRole("business")}
            className={`rounded-full py-2 text-sm font-bold transition ${
              role === "business" ? "bg-white text-navy-900 shadow-card" : "text-navy-400"
            }`}
          >
            I&rsquo;m a Business
          </button>
        </div>

        <form className="mt-5 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="full_name" className="block text-xs font-semibold text-navy-600">
              {role === "business" ? "Business name" : "Full name"}
            </label>
            <input
              id="full_name"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder={role === "business" ? "Your business name" : "Your full name"}
              className="mt-1.5 w-full rounded-xl border border-navy-100 px-3.5 py-2.5 text-sm text-navy-900 focus:border-navy-400 focus:outline-none"
            />
          </div>
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
            <label htmlFor="phone" className="block text-xs font-semibold text-navy-600">
              Phone number
            </label>
            <input
              id="phone"
              type="tel"
              required
              minLength={7}
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+234 801 234 5678"
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
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Create a password"
              className="mt-1.5 w-full rounded-xl border border-navy-100 px-3.5 py-2.5 text-sm text-navy-900 focus:border-navy-400 focus:outline-none"
            />
            <p className="mt-1 text-[11px] text-navy-300">At least 8 characters.</p>
          </div>

          {error && <p className="text-sm font-medium text-red-500">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-full bg-cta-gradient py-3 text-sm font-bold text-navy-900 shadow-card transition hover:brightness-105 disabled:opacity-60"
          >
            {loading ? "Creating account..." : "Create Account"}
          </button>
        </form>

        <p className="mt-5 text-center text-xs text-navy-400">
          Already have an account?{" "}
          <Link href="/login" className="font-semibold text-navy-600 hover:text-navy-900">
            Log in
          </Link>
        </p>
      </div>
    </main>
  );
}

export default function RegisterPage() {
  return (
    <Suspense>
      <RegisterForm />
    </Suspense>
  );
}
