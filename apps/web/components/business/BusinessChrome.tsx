"use client";

import { BusinessTopbar } from "@/components/business/BusinessTopbar";
import { useAccount } from "@/components/dashboard/AccountContext";

export function BusinessChrome({ children }: { children: React.ReactNode }) {
  const account = useAccount();

  return (
    <div className="min-h-screen bg-slate-50">
      <BusinessTopbar account={account} />
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </div>
  );
}
