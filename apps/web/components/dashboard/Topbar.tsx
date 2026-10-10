"use client";

import { useRouter } from "next/navigation";
import { api, type Account } from "@/lib/api";
import { BellIcon, LogOutIcon, SearchIcon } from "@/components/icons";

export function Topbar({ account }: { account: Account }) {
  const router = useRouter();

  async function handleLogout() {
    await api.logout().catch(() => undefined);
    router.push("/login");
  }

  const initial = account.full_name?.charAt(0) || account.email.charAt(0);

  return (
    <header className="flex items-center gap-4 border-b border-navy-900/5 bg-white px-6 py-4">
      <div className="relative flex-1 max-w-md">
        <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-navy-300" />
        <input
          type="search"
          placeholder="Search offers, links..."
          className="w-full rounded-full border border-navy-100 bg-slate-50 py-2.5 pl-9 pr-4 text-sm text-navy-800 placeholder:text-navy-300 focus:border-navy-300 focus:outline-none"
        />
      </div>

      <button
        type="button"
        aria-label="Notifications"
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-navy-400 transition hover:bg-slate-50 hover:text-navy-700"
      >
        <BellIcon className="h-5 w-5" />
      </button>

      <div className="flex shrink-0 items-center gap-2.5 border-l border-navy-100 pl-4">
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-navy-900 text-sm font-bold uppercase text-white">
          {initial}
        </span>
        <div className="hidden leading-tight sm:block">
          <div className="text-sm font-bold text-navy-900">{account.full_name || account.email}</div>
          <div className="text-xs capitalize text-navy-400">{account.role}</div>
        </div>
        <button
          type="button"
          onClick={handleLogout}
          aria-label="Log out"
          className="ml-1 flex h-9 w-9 items-center justify-center rounded-full text-navy-300 transition hover:bg-slate-50 hover:text-navy-700"
        >
          <LogOutIcon className="h-[18px] w-[18px]" />
        </button>
      </div>
    </header>
  );
}
