"use client";

import { m } from "framer-motion";

export function HoverCard({
  children,
  className,
  lift = 6,
  scale = 1.02,
  tapScale = 0.98,
}: {
  children: React.ReactNode;
  className?: string;
  lift?: number;
  scale?: number;
  tapScale?: number;
}) {
  return (
    <m.div
      className={className}
      whileHover={{
        y: -lift,
        scale,
        transition: { type: "spring", stiffness: 300, damping: 20 },
      }}
      whileTap={{ scale: tapScale }}
    >
      {children}
    </m.div>
  );
}
