"use client";

import { useEffect, useState } from "react";
import AnalysisCenter from "@/components/intelligence/AnalysisCenter";
import { AnalysisCenter as AnalysisCenterData, ApiError, api } from "@/lib/api";

export default function AnalysisPage() {
  const [data, setData] = useState<AnalysisCenterData | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { let active = true; api.getAnalysisCenter().then((value) => active && setData(value)).catch((reason) => active && setError(reason instanceof ApiError ? reason.message : "Analysis Center unavailable.")); return () => { active = false; }; }, []);
  return <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6" aria-label="Analysis Center">{error ? <div className="border border-red-500/50 p-6 text-sm">{error}</div> : data ? <AnalysisCenter data={data} /> : <div className="py-20 text-sm text-muted-foreground">Loading live analysis…</div>}</main>;
}
