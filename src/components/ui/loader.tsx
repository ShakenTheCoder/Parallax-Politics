"use client";

import { useReducedMotion } from "motion/react";
import { useCallback, useEffect, useRef, useState } from "react";

const GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<>/*#@";

type LoaderProps = {
  target?: string;
  speed?: number;
  label?: string;
  className?: string;
  loop?: boolean;
  animateOnHover?: boolean;
};

export function ScrambleLoader({
  target = "IDENTIFING",
  speed = 1,
  label = "Loading",
  className = "",
  loop = true,
  animateOnHover = false,
}: LoaderProps) {
  const reduce = useReducedMotion() ?? false;
  const [text, setText] = useState(target);
  const intervalRef = useRef<number | null>(null);

  const animate = useCallback(() => {
    if (intervalRef.current !== null) window.clearInterval(intervalRef.current);

    if (reduce) {
      setText(target);
      return;
    }

    let tick = 0;
    const total = target.length + 4;
    intervalRef.current = window.setInterval(() => {
      const reveal = tick % total;
      setText(
        target
          .split("")
          .map((character, index) =>
            index < reveal
              ? character
              : GLYPHS[Math.floor(Math.random() * GLYPHS.length)],
          )
          .join(""),
      );
      tick += 1;

      if (!loop && tick >= total && intervalRef.current !== null) {
        window.clearInterval(intervalRef.current);
        intervalRef.current = null;
        setText(target);
      }
    }, (speed / target.length) * 1000 * 0.55);
  }, [loop, reduce, speed, target]);

  useEffect(() => {
    const task = window.setTimeout(animate, 0);
    return () => {
      window.clearTimeout(task);
      if (intervalRef.current !== null) window.clearInterval(intervalRef.current);
    };
  }, [animate]);

  return (
    <span
      role="status"
      aria-label={label}
      onMouseEnter={animateOnHover ? animate : undefined}
      className={`font-mono tracking-[0.12em] ${className}`}
    >
      {text}
    </span>
  );
}
