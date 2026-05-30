"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession } from "@/lib/SessionContext";
import { useTheme } from "@/lib/ThemeContext";

export default function Navbar() {
  const { user, logoutSession } = useSession();
  const { theme } = useTheme();
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const navItems = user
    ? [
        { label: "Brief", href: "/brief" },
      ]
    : [];

  return (
    <header className="border-b border-border bg-background/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href={user ? "/brief" : "/"} className="flex items-center gap-2">
            {mounted && (
              <Image
                src={theme === "dark" ? "/Parallax-assets/Parallax politics/4.png" : "/Parallax-assets/Parallax politics/3.png"}
                alt="Parallax Politics"
                width={28}
                height={28}
                className="object-contain"
              />
            )}
            <span className="text-xl font-bold tracking-tight">Parallax Politics</span>
          </Link>
          {navItems.length > 0 && (
            <nav className="flex items-center gap-4">
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

        <div className="flex items-center gap-4">
          {user ? (
            <>
              <span className="text-xs text-muted-foreground hidden sm:inline-block">
                {user.display_name || user.username}
              </span>
              <button
                onClick={logoutSession}
                className="text-sm font-medium text-muted-foreground hover:text-foreground border border-border px-3 py-1.5 hover:bg-muted transition-colors"
              >
                Logout
              </button>
            </>
          ) : (
            <Link
              href="/login"
              className="text-sm font-medium bg-foreground text-background px-3 py-1.5 hover:opacity-90 transition-opacity"
            >
              Sign In
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
