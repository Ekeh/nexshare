import Link from "next/link";
import {
  CheckCircleIcon,
  PlayIcon,
  UserPlusIcon,
  UsersIcon,
} from "@/components/icons";
import { LogoMark } from "@/components/Logo";
import { Reveal } from "@/components/motion/Reveal";
import { HoverCard } from "@/components/motion/HoverCard";

const promoterPerks = [
  "Access thousands of offers",
  "Get unique tracking links",
  "Share on social media",
  "Track your performance",
  "Withdraw real money",
];

const businessPerks = [
  "List products or services",
  "Set commission rates",
  "Choose conversion type",
  "Track results in real-time",
  "Pay for actual results",
];

function AppBadge({ label, sub }: { label: string; sub: string }) {
  return (
    <div className="flex items-center gap-2 rounded-lg bg-navy-950 px-3 py-2 text-white">
      <div className="h-5 w-5 rounded-sm bg-white/10" />
      <div className="leading-none">
        <div className="text-[9px] text-white/60">{sub}</div>
        <div className="text-xs font-semibold">{label}</div>
      </div>
    </div>
  );
}

export function TwoPaths() {
  return (
    <section id="two-paths" className="bg-navy-950 py-20">
      <div className="mx-auto max-w-7xl px-6 lg:px-10">
        <Reveal>
          <h2 className="text-center text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            Two Paths. One Platform.
          </h2>
        </Reveal>

        <div className="mt-12 grid grid-cols-1 items-center gap-8 lg:grid-cols-[1fr_1fr_auto_1.1fr]">
          {/* Promoter card */}
          <Reveal delay={0} y={20}>
            <HoverCard className="rounded-2xl bg-gradient-to-b from-navy-800 to-navy-900 p-6 shadow-card-lg ring-1 ring-white/10">
              <span className="flex h-11 w-11 items-center justify-center rounded-full bg-gold-500/90 text-navy-900">
                <UserPlusIcon className="h-6 w-6" />
              </span>
              <h3 className="mt-4 text-base font-bold text-white">
                For Promoters
              </h3>
              <p className="text-sm font-bold text-gold-500">Earn Money</p>
              <ul className="mt-4 space-y-2.5">
                {promoterPerks.map((p) => (
                  <li key={p} className="flex items-center gap-2.5 text-sm text-white/70">
                    <CheckCircleIcon className="h-4 w-4 shrink-0 text-white/40" />
                    {p}
                  </li>
                ))}
              </ul>
              <Link
                href="/register?role=promoter"
                className="mt-6 block rounded-full bg-cta-gradient py-3 text-center text-sm font-bold text-navy-900 shadow-card transition hover:brightness-105"
              >
                Join as Promoter
              </Link>
            </HoverCard>
          </Reveal>

          {/* Business card */}
          <Reveal delay={0.1} y={20}>
            <HoverCard className="rounded-2xl bg-gradient-to-b from-navy-800 to-navy-900 p-6 shadow-card-lg ring-1 ring-white/10">
              <span className="flex h-11 w-11 items-center justify-center rounded-full bg-sky-400/90 text-navy-900">
                <UsersIcon className="h-6 w-6" />
              </span>
              <h3 className="mt-4 text-base font-bold text-white">
                For Businesses
              </h3>
              <p className="text-sm font-bold text-sky-400">Get Customers</p>
              <ul className="mt-4 space-y-2.5">
                {businessPerks.map((p) => (
                  <li key={p} className="flex items-center gap-2.5 text-sm text-white/70">
                    <CheckCircleIcon className="h-4 w-4 shrink-0 text-white/40" />
                    {p}
                  </li>
                ))}
              </ul>
              <Link
                href="/register?role=business"
                className="mt-6 block rounded-full bg-gradient-to-r from-sky-500 to-blue-600 py-3 text-center text-sm font-bold text-white shadow-card transition hover:brightness-110"
              >
                Add Your Business
              </Link>
            </HoverCard>
          </Reveal>

          {/* phone splash mock */}
          <Reveal delay={0.2} className="hidden lg:block">
            <div className="relative mx-auto flex h-[300px] w-[150px] flex-col items-center justify-center rounded-[1.75rem] border-4 border-navy-800 bg-hero-gradient p-1 shadow-card-lg">
              <div className="absolute left-1/2 top-0 h-4 w-16 -translate-x-1/2 rounded-b-lg bg-navy-950" />
              <LogoMark className="h-10 w-10" />
              <div className="mt-2 text-sm font-extrabold text-white">
                Nex<span className="text-gold-500">Share</span>
              </div>
              <div className="mt-1 text-center text-[9px] leading-snug text-white/60">
                Promote Anything.
                <br />
                Earn from Results.
              </div>
            </div>
          </Reveal>

          {/* mission copy */}
          <Reveal delay={0.15}>
            <h3 className="text-2xl font-extrabold leading-tight text-white">
              Your Success
              <br />
              Is Our Mission
            </h3>
            <p className="mt-3 max-w-sm text-sm leading-relaxed text-white/60">
              NexShare is more than a platform — it&rsquo;s a movement to
              create opportunities, power businesses and transform lives.
            </p>
            <div className="mt-5 flex flex-wrap items-center gap-5">
              <Link
                href="/register"
                className="rounded-full bg-cta-gradient px-6 py-3 text-sm font-bold text-navy-900 shadow-card transition hover:brightness-105"
              >
                Join the Movement
              </Link>
              <button className="flex items-center gap-2 text-sm font-semibold text-white">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-navy-900 transition hover:scale-110 active:scale-95">
                  <PlayIcon className="ml-0.5 h-3.5 w-3.5" />
                </span>
                Watch Video
              </button>
            </div>
            <div className="mt-6 flex gap-3">
              <AppBadge sub="Download on the" label="App Store" />
              <AppBadge sub="GET IT ON" label="Google Play" />
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
