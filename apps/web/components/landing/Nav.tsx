import Link from "next/link";
import { Logo } from "@/components/Logo";

const links = [
  { label: "Home", href: "#" },
  { label: "How It Works", href: "#how-it-works" },
  { label: "For Businesses", href: "#two-paths" },
  { label: "For Promoters", href: "#two-paths" },
  { label: "Offers", href: "#" },
  { label: "Resources", href: "#" },
];

export function Nav() {
  return (
    <header className="relative z-20">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6 lg:px-10">
        <Logo />
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
        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="hidden rounded-full border border-white/30 px-5 py-2 text-sm font-semibold text-white transition hover:scale-[1.02] hover:bg-white/10 active:scale-95 sm:block"
          >
            Login
          </Link>
          <Link
            href="/register"
            className="rounded-full bg-cta-gradient px-5 py-2 text-sm font-bold text-navy-900 shadow-card transition hover:scale-[1.02] hover:brightness-105 active:scale-95"
          >
            Get Started
          </Link>
        </div>
      </div>
    </header>
  );
}
