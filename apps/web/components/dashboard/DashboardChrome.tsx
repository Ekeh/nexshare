"use client";

import { useState } from "react";
import { Sidebar, promoterNavLinks } from "@/components/dashboard/Sidebar";
import { Topbar } from "@/components/dashboard/Topbar";
import { useAccount } from "@/components/dashboard/AccountContext";
import { MobileNavDrawer } from "@/components/MobileNavDrawer";

export function DashboardChrome({ children }: { children: React.ReactNode }) {
  const account = useAccount();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <MobileNavDrawer
        open={mobileNavOpen}
        onClose={() => setMobileNavOpen(false)}
        links={promoterNavLinks}
        hideFrom="lg"
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar account={account} onMenuClick={() => setMobileNavOpen(true)} />
        <main className="flex-1 px-6 py-6">{children}</main>
      </div>
    </div>
  );
}
