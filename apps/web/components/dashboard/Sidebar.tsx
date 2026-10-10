"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "@/components/Logo";
import {
  DashboardIcon,
  TagIcon,
  LinkIcon,
  StoreIcon,
  ChartIcon,
  WalletIcon,
  BanknoteIcon,
  GraduationCapIcon,
  LifeBuoyIcon,
} from "@/components/icons";

const links = [
  { label: "Dashboard", href: "/dashboard", icon: DashboardIcon },
  { label: "My Offers", href: "/dashboard/offers", icon: TagIcon },
  { label: "My Links", href: "/dashboard/links", icon: LinkIcon },
  { label: "Storefront", href: "/dashboard/storefront", icon: StoreIcon },
  { label: "Analytics", href: "/dashboard/analytics", icon: ChartIcon },
  { label: "Earnings", href: "/dashboard/earnings", icon: WalletIcon },
  { label: "Withdraw", href: "/dashboard/withdraw", icon: BanknoteIcon },
  { label: "Training", href: "/dashboard/training", icon: GraduationCapIcon },
  { label: "Support", href: "/dashboard/support", icon: LifeBuoyIcon },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 shrink-0 flex-col bg-navy-950 px-4 py-6 lg:flex">
      <div className="px-2">
        <Logo tagline={false} />
      </div>
      <nav className="mt-8 flex flex-1 flex-col gap-1">
        {links.map((link) => {
          const active = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                active
                  ? "bg-gradient-to-r from-[#3B62F5] to-[#2947d1] text-white shadow-card"
                  : "text-white/60 hover:bg-white/5 hover:text-white"
              }`}
            >
              <link.icon className="h-[18px] w-[18px]" />
              {link.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
