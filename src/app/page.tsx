"use client";

import { useRouter } from "next/navigation";
import RotatingEarth from "@/components/ui/wireframe-dotted-globe";
import { ScrambleLoader } from "@/components/ui/loader";

export default function Home() {
  const router = useRouter();

  return (
    <div className="relative flex min-h-0 flex-1 w-full flex-col items-center justify-center overflow-hidden bg-background px-4">
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center opacity-35 sm:-translate-y-10">
        <RotatingEarth width={760} height={600} className="w-[84vw] max-w-3xl sm:w-[760px] sm:max-w-none" />
      </div>
      <div className="relative z-10 w-full max-w-sm space-y-8 sm:-translate-y-10">
        <div className="text-center space-y-2">
          <h1 className="text-5xl font-bold tracking-tight">
            <ScrambleLoader
              target="PARALLAX"
              label="Loading Parallax"
              speed={1.8}
              loop={false}
              animateOnHover
              className="text-5xl font-bold tracking-tight"
            />
          </h1>
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
