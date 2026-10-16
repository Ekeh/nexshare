"use client";

import { useState } from "react";
import Link from "next/link";
import { Logo, LogoMark } from "@/components/Logo";
import { MenuIcon } from "@/components/icons";
import { MobileNavDrawer } from "@/components/MobileNavDrawer";

const links = [
  { label: "Home", href: "#" },
  { label: "How It Works", href: "#how-it-works" },
  { label: "For Businesses", href: "#two-paths" },
  { label: "For Promoters", href: "#two-paths" },
  { label: "Offers", href: "#" },
  { label: "Resources", href: "#" },
];

export function Nav() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="relative z-20">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6 lg:px-10">
        <LogoMark className="h-9 w-9 shrink-0 sm:hidden" />
        <div className="hidden sm:block">
          <Logo />
        </div>
        <nav className="hidden items-center gap-8 lg:flex">
          {links.map((l) => (
            <Link
              key={l.label}
              href={l.href}
              className="text-sm font-medium text-white/80 transition hover:text-white"
            >
              {l.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-2 sm:gap-3">
          <Link
            href="/login"
            className="rounded-full border border-white/30 px-3.5 py-1.5 text-xs font-semibold text-white transition hover:scale-[1.02] hover:bg-white/10 active:scale-95 sm:px-5 sm:py-2 sm:text-sm"
          >
            Login
          </Link>
          <Link
            href="/register"
            className="rounded-full bg-cta-gradient px-3.5 py-1.5 text-xs font-bold text-navy-900 shadow-card transition hover:scale-[1.02] hover:brightness-105 active:scale-95 sm:px-5 sm:py-2 sm:text-sm"
          >
            Get Started
          </Link>
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            aria-label="Open menu"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-white transition hover:bg-white/10 sm:h-10 sm:w-10 lg:hidden"
          >
            <MenuIcon className="h-5 w-5" />
          </button>
        </div>
      </div>
      <MobileNavDrawer open={mobileOpen} onClose={() => setMobileOpen(false)} links={links} hideFrom="lg" />
    </header>
  );
}
