"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession } from "@/lib/SessionContext";
import { useTheme } from "@/lib/ThemeContext";
import { isAdminRole } from "@/lib/api";

export default function Navbar() {
  const { user, logoutSession } = useSession();
  const { theme } = useTheme();
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const task = window.setTimeout(() => setMounted(true), 0);
    return () => window.clearTimeout(task);
  }, []);

  const navItems = user
    ? isAdminRole(user.role)
      ? [
          { label: "Identities", href: "/admin" },
          { label: "Intelligence", href: "/intelligence" },
        ]
      : [
          { label: "Brief", href: "/brief" },
          { label: "Audience", href: "/audience" },
          { label: "Intelligence", href: "/intelligence" },
        ]
    : [];

  return (
    <header className="border-b border-border bg-background/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 py-3 min-h-16 flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <div className="flex min-w-0 items-center gap-3 sm:gap-6">
          <Link href={user ? (isAdminRole(user.role) ? "/admin" : "/brief") : "/"} className="flex min-w-0 items-center gap-2">
            {mounted && (
              <Image
                src={theme === "dark" ? "/Parallax-assets/Parallax politics/4.png" : "/Parallax-assets/Parallax politics/3.png"}
                alt="Parallax Politics"
                width={28}
                height={28}
                className="object-contain"
              />
            )}
            <span className="truncate text-lg sm:text-xl font-bold tracking-tight">Parallax Politics</span>
          </Link>
          {navItems.length > 0 && (
            <nav className="flex items-center gap-3 sm:gap-4">
              {navItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`text-sm font-medium transition-colors hover:text-foreground ${
                      isActive ? "text-foreground font-semibold" : "text-muted-foreground"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          )}
        </div>

        <div className="ml-auto flex shrink-0 items-center gap-2 sm:gap-4">
          {user ? (
            <>
              <span className="text-xs text-muted-foreground hidden sm:inline-block">
                {user.display_name || user.username}
              </span>
              <button
                onClick={logoutSession}
                className="bg-foreground text-background px-2.5 py-1 text-xs font-medium hover:bg-muted hover:text-foreground transition-colors"
              >
                Logout
              </button>
            </>
          ) : (
            <Link
              href="/login"
              className="text-sm font-medium bg-foreground text-background px-3 py-1.5 hover:opacity-90 transition-opacity"
            >
              Access Insights
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
