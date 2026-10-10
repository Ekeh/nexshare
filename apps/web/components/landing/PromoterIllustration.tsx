"use client";

import { m, useReducedMotion } from "framer-motion";
import {
  CheckCircleIcon,
  ArrowUpRightIcon,
  PlayIcon,
  FacebookIcon,
  InstagramIcon,
  TikTokIcon,
  WhatsAppIcon,
  YoutubeIcon,
  XIcon,
} from "@/components/icons";

function SocialBubble({
  className,
  bg,
  children,
  duration,
  delay,
  reduceMotion,
}: {
  className?: string;
  bg: string;
  children: React.ReactNode;
  duration: number;
  delay: number;
  reduceMotion: boolean;
}) {
  return (
    <m.div
      className={`absolute flex h-10 w-10 items-center justify-center rounded-full text-white shadow-lg ring-4 ring-white/10 sm:h-11 sm:w-11 ${bg} ${className ?? ""}`}
      animate={reduceMotion ? undefined : { y: [0, -8, 0] }}
      transition={
        reduceMotion
          ? undefined
          : { duration, delay, repeat: Infinity, repeatType: "reverse", ease: "easeInOut" }
      }
    >
      {children}
    </m.div>
  );
}

// Fixed (not Math.random()) per-bubble timing so bubbles bob out of sync
// rather than in lockstep, without causing an SSR/hydration value mismatch.
const bubbleTiming = [
  { duration: 3.2, delay: 0 },
  { duration: 3.8, delay: 0.4 },
  { duration: 4.4, delay: 0.8 },
  { duration: 3.6, delay: 0.2 },
  { duration: 4.0, delay: 0.6 },
  { duration: 3.4, delay: 1.0 },
];

export function PromoterIllustration() {
  const reduceMotion = Boolean(useReducedMotion());

  return (
    <div className="relative mx-auto aspect-[4/5] w-full max-w-md sm:max-w-lg">
      {/* swirl ring under the figure */}
      <div className="absolute inset-x-2 bottom-6 h-16 rounded-[50%] bg-gradient-to-r from-[#2b57ff] via-[#5b7bff] to-gold-500 opacity-90 blur-[1px]" />
      <div className="absolute inset-x-10 bottom-10 h-10 rounded-[50%] bg-navy-900/60 blur-md" />

      {/* promoter photo (stock, Unsplash License — free for commercial use) */}
      <div
        className="absolute inset-x-0 bottom-0 mx-auto h-[90%] aspect-[1600/2160] overflow-hidden [mask-image:radial-gradient(ellipse_55%_65%_at_50%_40%,black_40%,transparent_100%)] [-webkit-mask-image:radial-gradient(ellipse_55%_65%_at_50%_40%,black_40%,transparent_100%)]"
      >
        {/* eslint-disable-next-line @next/next/no-img-element -- fixed local
            asset; a plain img avoids next/image's fill-layout sizing quirks */}
        <img
          src="/images/hero-promoter.jpg"
          alt="Promoter smiling while using NexShare"
          className="h-full w-full object-cover drop-shadow-2xl"
        />
      </div>

      {/* play button */}
      <m.div
        className="absolute left-1/2 top-[46%] flex h-14 w-14 -translate-x-1/2 items-center justify-center rounded-full bg-white shadow-card-lg sm:h-16 sm:w-16"
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.95 }}
      >
        <PlayIcon className="ml-1 h-6 w-6 text-navy-900" />
      </m.div>

      {/* floating stat card: new commission */}
      <m.div
        className="absolute -left-2 top-2 flex items-center gap-2.5 rounded-2xl bg-white px-3.5 py-2.5 shadow-card-lg sm:-left-6 sm:top-6"
        animate={reduceMotion ? undefined : { y: [0, -8, 0] }}
        transition={
          reduceMotion
            ? undefined
            : { duration: 3.6, repeat: Infinity, repeatType: "reverse", ease: "easeInOut" }
        }
        whileHover={{ scale: 1.04 }}
      >
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
          <CheckCircleIcon className="h-5 w-5" />
        </span>
        <div>
          <div className="text-[11px] font-medium text-navy-500">New Commission!</div>
          <div className="text-sm font-extrabold text-navy-900">$48.50</div>
        </div>
      </m.div>

      {/* floating stat card: total earnings */}
      <m.div
        className="absolute -right-2 top-[38%] rounded-2xl bg-white px-4 py-3 shadow-card-lg sm:-right-6"
        animate={reduceMotion ? undefined : { y: [0, -8, 0] }}
        transition={
          reduceMotion
            ? undefined
            : { duration: 4.2, delay: 0.3, repeat: Infinity, repeatType: "reverse", ease: "easeInOut" }
        }
        whileHover={{ scale: 1.04 }}
      >
        <div className="flex items-center justify-between gap-6">
          <div className="text-[11px] font-medium text-navy-500">Total Earnings</div>
          <ArrowUpRightIcon className="h-4 w-4 text-emerald-500" />
        </div>
        <div className="text-lg font-extrabold text-navy-900">$3,286.40</div>
        <div className="text-[11px] text-navy-400">This Month</div>
      </m.div>

      {/* social bubbles */}
      <SocialBubble
        bg="bg-black"
        className="right-2 top-2 sm:right-4 sm:top-4"
        reduceMotion={reduceMotion}
        {...bubbleTiming[0]}
      >
        <TikTokIcon className="h-4 w-4" />
      </SocialBubble>
      <SocialBubble
        bg="bg-gradient-to-br from-fuchsia-500 to-orange-400"
        className="right-[-6px] top-[22%]"
        reduceMotion={reduceMotion}
        {...bubbleTiming[1]}
      >
        <InstagramIcon className="h-5 w-5" />
      </SocialBubble>
      <SocialBubble
        bg="bg-[#1877F2]"
        className="left-[6%] top-[28%]"
        reduceMotion={reduceMotion}
        {...bubbleTiming[2]}
      >
        <FacebookIcon className="h-5 w-5" />
      </SocialBubble>
      <SocialBubble
        bg="bg-[#25D366]"
        className="right-[10%] bottom-[16%]"
        reduceMotion={reduceMotion}
        {...bubbleTiming[3]}
      >
        <WhatsAppIcon className="h-5 w-5" />
      </SocialBubble>
      <SocialBubble
        bg="bg-[#FF0000]"
        className="right-[-4px] bottom-[6%]"
        reduceMotion={reduceMotion}
        {...bubbleTiming[4]}
      >
        <YoutubeIcon className="h-5 w-5" />
      </SocialBubble>
      <SocialBubble
        bg="bg-black"
        className="right-[16%] bottom-[-2px]"
        reduceMotion={reduceMotion}
        {...bubbleTiming[5]}
      >
        <XIcon className="h-4 w-4" />
      </SocialBubble>
    </div>
  );
}
