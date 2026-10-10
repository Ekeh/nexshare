"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Logo } from "@/components/Logo";
import { LogOutIcon } from "@/components/icons";
import { api, type Account } from "@/lib/api";

const NAV_LINKS = [
  { href: "/business", label: "Offers" },
  { href: "/business/commissions", label: "Commissions" },
];

export function BusinessTopbar({ account }: { account: Account }) {
  const router = useRouter();
  const pathname = usePathname();

  async function handleLogout() {
    await api.logout().catch(() => undefined);
    router.push("/login");
  }

  return (
    <header className="flex items-center justify-between border-b border-navy-900/5 bg-white px-6 py-4">
      <div className="flex items-center gap-8">
        <Logo dark tagline={false} />
        <nav className="flex items-center gap-1">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`rounded-full px-4 py-1.5 text-sm font-bold transition ${
                pathname === link.href ? "bg-navy-900 text-white" : "text-navy-400 hover:bg-slate-50 hover:text-navy-700"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
      <div className="flex items-center gap-3">
        <div className="text-right leading-tight">
          <div className="text-sm font-bold text-navy-900">{account.full_name || account.email}</div>
          <div className="text-xs text-navy-400">Business</div>
        </div>
        <button
          type="button"
          onClick={handleLogout}
          aria-label="Log out"
          className="flex h-9 w-9 items-center justify-center rounded-full text-navy-300 transition hover:bg-slate-50 hover:text-navy-700"
        >
          <LogOutIcon className="h-[18px] w-[18px]" />
        </button>
      </div>
    </header>
  );
}
