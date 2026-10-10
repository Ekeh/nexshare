"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, type Account } from "@/lib/api";

const AccountContext = createContext<Account | null>(null);

export function useAccount(): Account {
  const account = useContext(AccountContext);
  if (!account) {
    throw new Error("useAccount must be used within AccountProvider, after auth has resolved");
  }
  return account;
}

export function AccountProvider({
  children,
  role,
}: {
  children: React.ReactNode;
  /** Only an account with this role may view what's inside — anyone else is bounced to /login. */
  role: "promoter" | "business";
}) {
  const router = useRouter();
  const [account, setAccount] = useState<Account | null>(null);
  const [status, setStatus] = useState<"loading" | "ready">("loading");

  useEffect(() => {
    let cancelled = false;
    api
      .me()
      .then((acc) => {
        if (cancelled) return;
        if (acc.role !== role) {
          router.replace("/login");
          return;
        }
        setAccount(acc);
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) router.replace("/login");
      });
    return () => {
      cancelled = true;
    };
  }, [router, role]);

  if (status === "loading" || !account) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-navy-200 border-t-navy-900" />
      </div>
    );
  }

  return <AccountContext.Provider value={account}>{children}</AccountContext.Provider>;
}
