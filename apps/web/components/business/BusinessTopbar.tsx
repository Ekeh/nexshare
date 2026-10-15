"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Logo, LogoMark } from "@/components/Logo";
import { BanknoteIcon, LogOutIcon, MenuIcon, TagIcon } from "@/components/icons";
import { api, type Account } from "@/lib/api";

export const businessNavLinks = [
  { href: "/business", label: "Offers", icon: TagIcon },
  { href: "/business/commissions", label: "Commissions", icon: BanknoteIcon },
];

export function BusinessTopbar({ account, onMenuClick }: { account: Account; onMenuClick: () => void }) {
  const router = useRouter();
  const pathname = usePathname();

  async function handleLogout() {
    await api.logout().catch(() => undefined);
    router.push("/login");
  }

  return (
    <header className="flex items-center justify-between border-b border-navy-900/5 bg-white px-6 py-4">
      <div className="flex items-center gap-4 md:gap-8">
        <button
          type="button"
          onClick={onMenuClick}
          aria-label="Open menu"
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-navy-700 transition hover:bg-slate-50 md:hidden"
        >
          <MenuIcon className="h-5 w-5" />
        </button>
        <LogoMark className="h-8 w-8 shrink-0 md:hidden" />
        <div className="hidden md:block">
          <Logo dark tagline={false} />
        </div>
        <nav className="hidden items-center gap-1 md:flex">
          {businessNavLinks.map((link) => (
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
        <div className="hidden text-right leading-tight sm:block">
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
