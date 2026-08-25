"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "motion/react";
import { useSession } from "@/lib/SessionContext";
import { useTheme } from "@/lib/ThemeContext";
import { isAdminRole } from "@/lib/api";

export default function Navbar() {
  const { user, logoutSession } = useSession();
  const { theme } = useTheme();
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const task = window.setTimeout(() => setMounted(true), 0);
    return () => window.clearTimeout(task);
  }, []);

  const navItems = user
    ? isAdminRole(user.role)
          ? [
              { label: "Identities", href: "/admin" },
              { label: "Political Glossary", href: "/admin/glossary" },
              { label: "Intelligence", href: "/intelligence" },
        ]
      : [
              { label: "Brief", href: "/brief" },
              { label: "Analysis", href: "/analysis" },
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
          </Link>
          {navItems.length > 0 && (
            <nav className="hidden items-center gap-3 sm:flex sm:gap-4">
              {navItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`text-sm font-medium ${
                      isActive ? "tab-active pb-1" : "text-muted-foreground hover:text-foreground"
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
          {navItems.length > 0 && (
            <button
              type="button"
              onClick={() => setMobileMenuOpen((open) => !open)}
              className="inline-flex h-9 w-9 flex-col items-center justify-center gap-1.5 sm:hidden focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-foreground"
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-navigation"
              aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
            >
              <motion.span
                className="block h-px w-4 bg-foreground"
                animate={{ rotate: mobileMenuOpen ? 45 : 0, y: mobileMenuOpen ? 5 : 0 }}
                transition={{ duration: 0.2 }}
              />
              <motion.span
                className="block h-px w-4 bg-foreground"
                animate={{ opacity: mobileMenuOpen ? 0 : 1 }}
                transition={{ duration: 0.15 }}
              />
              <motion.span
                className="block h-px w-4 bg-foreground"
                animate={{ rotate: mobileMenuOpen ? -45 : 0, y: mobileMenuOpen ? -5 : 0 }}
                transition={{ duration: 0.2 }}
              />
            </button>
          )}
          {user ? (
            <>
              <span className="text-xs text-muted-foreground hidden sm:inline-block">
                {user.display_name || user.username}
              </span>
              <button
                onClick={logoutSession}
                className="hidden bg-foreground text-background px-2.5 py-1 text-xs font-medium hover:bg-muted hover:text-foreground transition-colors sm:inline-flex"
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
      <AnimatePresence initial={false}>
        {mobileMenuOpen && navItems.length > 0 && (
          <motion.div
            id="mobile-navigation"
            className="border-t border-border sm:hidden overflow-hidden"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
          >
            <nav className="mx-auto max-w-6xl px-4 py-2" aria-label="Mobile navigation">
              {navItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`block py-3 text-sm font-medium ${
                      isActive ? "tab-active" : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
              {user && (
                <button
                  type="button"
                  onClick={logoutSession}
                  className="mt-2 w-full border-t border-border py-3 text-left text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
                >
                  Logout
                </button>
              )}
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
