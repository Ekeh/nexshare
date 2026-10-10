"use client";

import { Sidebar } from "@/components/dashboard/Sidebar";
import { Topbar } from "@/components/dashboard/Topbar";
import { useAccount } from "@/components/dashboard/AccountContext";

export function DashboardChrome({ children }: { children: React.ReactNode }) {
  const account = useAccount();

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar account={account} />
        <main className="flex-1 px-6 py-6">{children}</main>
      </div>
    </div>
  );
}
