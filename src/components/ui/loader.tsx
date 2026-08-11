"use client";

import { useReducedMotion } from "motion/react";
import { useEffect, useState } from "react";

const GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<>/*#@";

type LoaderProps = {
  target?: string;
  speed?: number;
  label?: string;
  className?: string;
};

export function ScrambleLoader({
  target = "IDENTIFING",
  speed = 1,
  label = "Loading",
  className = "",
}: LoaderProps) {
  const reduce = useReducedMotion() ?? false;
  const [text, setText] = useState(target);

  useEffect(() => {
    if (reduce) {
      setText(target);
      return;
    }

    let tick = 0;
    const total = target.length + 4;
    const id = window.setInterval(() => {
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
    }, (speed / target.length) * 1000 * 0.55);

    return () => window.clearInterval(id);
  }, [reduce, speed, target]);

  return (
    <span role="status" aria-label={label} className={`font-mono tracking-[0.12em] ${className}`}>
      {text}
    </span>
  );
}
