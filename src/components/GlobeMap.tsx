"use client";

import { useTheme } from "@/lib/ThemeContext";

export default function GlobeMap() {
  const { theme } = useTheme();

  return (
    <img
      src="/globe.svg"
      alt=""
      aria-hidden="true"
      className="pointer-events-none absolute left-1/2 top-1/2 z-0 h-[min(78vw,42rem)] w-[min(78vw,42rem)] -translate-x-1/2 -translate-y-1/2 opacity-[0.06] sm:opacity-[0.08]"
      style={{ filter: theme === "dark" ? "brightness(0) invert(1)" : "brightness(0)" }}
    />
  );
}
