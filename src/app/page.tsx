"use client";

import { useRouter } from "next/navigation";
import RotatingEarth from "@/components/ui/wireframe-dotted-globe";

export default function Home() {
  const router = useRouter();

  return (
    <div className="relative min-h-screen overflow-hidden bg-background text-foreground flex flex-col items-center justify-center px-4">
      <div className="pointer-events-none absolute inset-0 flex -translate-y-10 items-center justify-center opacity-35">
        <RotatingEarth width={760} height={600} className="w-full max-w-3xl" />
      </div>
      <div className="relative z-10 -translate-y-10 w-full max-w-sm space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-5xl font-bold tracking-tight">Parallax</h1>
          <p className="text-sm text-muted-foreground">Philippine Political Intelligence · Restricted Access</p>
        </div>

        <button
          onClick={() => router.push("/login")}
          className="mx-auto block w-full max-w-[220px] px-4 py-3 bg-foreground text-background font-medium hover:opacity-90 transition-opacity"
        >
          Access Insights
        </button>
      </div>
    </div>
  );
}
