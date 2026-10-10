"use client";

import { useEffect, useRef, useState } from "react";
import { animate, useInView, useReducedMotion } from "framer-motion";

const PARSE = /^([^\d]*)([\d,]+)(.*)$/;

function parse(raw: string) {
  const match = raw.match(PARSE);
  if (!match) return { prefix: "", target: 0, suffix: raw };
  const [, prefix, digits, suffix] = match;
  return { prefix, target: Number(digits.replace(/,/g, "")), suffix };
}

export function useCountUp(rawValue: string, duration = 1.6) {
  const ref = useRef<HTMLElement>(null);
  const isInView = useInView(ref, { once: true, amount: 0.5 });
  const shouldReduceMotion = useReducedMotion();
  // Initial state is the real final string, never "0" — SSR/no-JS/pre-hydration
  // paints must always show the correct trust-critical number. Count-up is a
  // progressive-enhancement flourish only, once hydrated and in view.
  const [display, setDisplay] = useState(rawValue);

  useEffect(() => {
    if (!isInView) return;
    if (shouldReduceMotion) {
      setDisplay(rawValue);
      return;
    }
    const { prefix, target, suffix } = parse(rawValue);
    const controls = animate(0, target, {
      duration,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (v) => {
        setDisplay(`${prefix}${Math.round(v).toLocaleString("en-US")}${suffix}`);
      },
      onComplete: () => setDisplay(rawValue),
    });
    return () => controls.stop();
  }, [isInView, rawValue, duration, shouldReduceMotion]);

  return { ref, display };
}
