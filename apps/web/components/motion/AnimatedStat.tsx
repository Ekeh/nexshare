"use client";

import { useCountUp } from "@/components/motion/useCountUp";

export function AnimatedStat({
  value,
  className,
}: {
  value: string;
  className?: string;
}) {
  const { ref, display } = useCountUp(value);
  return (
    <dd ref={ref as React.Ref<HTMLElement>} className={className}>
      {display}
    </dd>
  );
}
