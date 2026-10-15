"use client";

import { useState } from "react";
import { BusinessTopbar, businessNavLinks } from "@/components/business/BusinessTopbar";
import { useAccount } from "@/components/dashboard/AccountContext";
import { MobileNavDrawer } from "@/components/MobileNavDrawer";

export function BusinessChrome({ children }: { children: React.ReactNode }) {
  const account = useAccount();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50">
      <BusinessTopbar account={account} onMenuClick={() => setMobileNavOpen(true)} />
      <MobileNavDrawer
        open={mobileNavOpen}
        onClose={() => setMobileNavOpen(false)}
        links={businessNavLinks}
        hideFrom="md"
      />
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </div>
  );
}
