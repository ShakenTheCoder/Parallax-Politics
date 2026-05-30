"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";

export default function Home() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-5xl font-bold tracking-tight">Parallax</h1>
          <p className="text-sm text-muted-foreground">Philippine Political Intelligence · Closed Program</p>
        </div>

        <button
          onClick={() => router.push("/login")}
          className="w-full px-4 py-3 bg-foreground text-background font-medium hover:opacity-90 transition-opacity"
        >
          Sign In
        </button>

        <p className="text-center">
          <Link href="/superadmin/enter" className="text-xs text-muted-foreground hover:text-foreground transition-colors">
            Superadmin →
          </Link>
        </p>
      </div>
    </div>
  );
}
