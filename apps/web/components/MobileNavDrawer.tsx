"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "@/components/Logo";
import { XMarkIcon } from "@/components/icons";
import type { ComponentType, SVGProps } from "react";

export type MobileNavLink = {
  label: string;
  href: string;
  icon?: ComponentType<SVGProps<SVGSVGElement>>;
};

export function MobileNavDrawer({
  open,
  onClose,
  links,
  /** The breakpoint at which the desktop nav takes over and this drawer
   * should never render, even if `open` is stale true from before a
   * resize (e.g. the drawer was left open on mobile, then the viewport
   * was widened past the point where the desktop nav is shown instead). */
  hideFrom = "lg",
}: {
  open: boolean;
  onClose: () => void;
  links: MobileNavLink[];
  hideFrom?: "md" | "lg";
}) {
  const pathname = usePathname();

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  if (!open) return null;

  return (
    <div
      className={`fixed inset-0 z-50 ${hideFrom === "md" ? "md:hidden" : "lg:hidden"}`}
      role="dialog"
      aria-modal="true"
    >
      <div className="absolute inset-0 bg-navy-950/60" onClick={onClose} />
      <div className="absolute inset-y-0 left-0 flex w-72 max-w-[85vw] flex-col bg-navy-950 px-4 py-6 shadow-card-lg">
        <div className="flex items-center justify-between px-2">
          <Logo tagline={false} />
          <button
            type="button"
            onClick={onClose}
            aria-label="Close menu"
            className="flex h-9 w-9 items-center justify-center rounded-full text-white/60 transition hover:bg-white/5 hover:text-white"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
        <nav className="mt-8 flex flex-1 flex-col gap-1 overflow-y-auto">
          {links.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={onClose}
                className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                  active
                    ? "bg-gradient-to-r from-[#3B62F5] to-[#2947d1] text-white shadow-card"
                    : "text-white/60 hover:bg-white/5 hover:text-white"
                }`}
              >
                {link.icon && <link.icon className="h-[18px] w-[18px]" />}
                {link.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
