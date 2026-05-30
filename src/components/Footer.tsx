"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useSession } from "@/lib/SessionContext";
import { useTheme } from "@/lib/ThemeContext";

export default function Footer() {
  const { user } = useSession();
  const { theme, toggleTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const currentYear = new Date().getFullYear();

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <footer className="border-t border-border mt-auto">
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Image
              src={theme === "dark" ? "/Parallax-assets/Parallax politics/4.png" : "/Parallax-assets/Parallax politics/3.png"}
              alt="Parallax Politics"
              width={24}
              height={24}
              className="object-contain"
            />
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span className="font-medium text-foreground">Parallax Politics</span>
              <span>·</span>
              <span>Philippines POC</span>
            </div>
          </div>

          <div className="flex items-center gap-4 text-[10px] tracking-widest uppercase text-muted-foreground">
            <span>Authorized Use Only</span>
            {user && <span className="hidden sm:inline">·</span>}
            {user && (
              <span className="hidden sm:inline">
                {user.role}
              </span>
            )}
            <span>·</span>
            {mounted && (
              <button
                onClick={toggleTheme}
                className="hover:text-foreground transition-colors border border-border px-2 py-1"
              >
                {theme === "light" ? "Dark" : "Light"}
              </button>
            )}
          </div>

          <div className="text-[10px] text-muted-foreground">
            {currentYear}
          </div>
        </div>
      </div>
    </footer>
  );
}
