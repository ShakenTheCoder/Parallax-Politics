"use client";

import Image from "next/image";
import { useSession } from "@/lib/SessionContext";
import { useTheme } from "@/lib/ThemeContext";

export default function Footer() {
  const { user } = useSession();
  const { theme } = useTheme();
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-[#c4c4c4] dark:border-[#3a3a3a] mt-auto">
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
              <span>Philippines Intelligence Operations</span>
            </div>
          </div>

          <div className="flex items-center gap-4 text-[10px] tracking-widest uppercase text-muted-foreground">
            <span>Classified · Authorized Use Only</span>
            {user && <span className="hidden sm:inline">·</span>}
            {user && (
              <span className="hidden sm:inline">
                {user.role}
              </span>
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
