import Link from "next/link";
import { Nav } from "@/components/landing/Nav";
import { PromoterIllustration } from "@/components/landing/PromoterIllustration";
import { AnimatedStat } from "@/components/motion/AnimatedStat";

const stats = [
  { value: "50,000+", label: "Active Promoters" },
  { value: "3,500+", label: "Partner Companies" },
  { value: "200,000+", label: "Active Offers" },
  { value: "$12M+", label: "Commissions Paid" },
];

export function Hero() {
  return (
    <section className="relative overflow-hidden bg-hero-gradient pb-16 pt-2 sm:pb-24">
      <div className="pointer-events-none absolute -top-40 right-0 h-96 w-96 rounded-full bg-[#3B62F5]/30 blur-3xl" />
      <Nav />
      <div className="relative mx-auto grid max-w-7xl grid-cols-1 items-center gap-12 px-6 pt-8 lg:grid-cols-2 lg:gap-8 lg:px-10 lg:pt-14">
        <div>
          <h1 className="text-4xl font-extrabold leading-[1.1] tracking-tight text-white sm:text-5xl lg:text-[3.4rem]">
            Turn Your Audience
            <br />
            into <span className="text-gold-500">Income</span>
          </h1>
          <p className="mt-5 max-w-md text-base leading-relaxed text-white/70">
            Promote products, services, bookings, leads, and more. Share
            through your social media and earn real money when people take
            action.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-4">
            <Link
              href="/register"
              className="rounded-full bg-cta-gradient px-7 py-3.5 text-sm font-bold text-navy-900 shadow-card-lg transition hover:scale-[1.03] hover:brightness-105 active:scale-[0.97]"
            >
              Start Earning Today
            </Link>
            <Link
              href="#how-it-works"
              className="rounded-full border border-white/30 px-7 py-3.5 text-sm font-bold text-white transition hover:scale-[1.03] hover:bg-white/10 active:scale-[0.97]"
            >
              How It Works
            </Link>
          </div>
          <dl className="mt-14 grid grid-cols-2 gap-x-6 gap-y-8 sm:grid-cols-4 sm:gap-x-4">
            {stats.map((s) => (
              <div key={s.label}>
                <dt className="sr-only">{s.label}</dt>
                <AnimatedStat
                  value={s.value}
                  className="text-2xl font-extrabold text-white sm:text-[1.75rem]"
                />
                <div className="mt-1 text-xs font-medium text-white/50">
                  {s.label}
                </div>
              </div>
            ))}
          </dl>
        </div>
        <PromoterIllustration />
      </div>
    </section>
  );
}
