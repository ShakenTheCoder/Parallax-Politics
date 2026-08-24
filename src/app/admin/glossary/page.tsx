"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import SocialPlatformIcon from "@/components/SocialPlatformIcon";
import { api, ApiError, PoliticalFigureSummary } from "@/lib/api";
import { useSession } from "@/lib/SessionContext";

export default function PoliticalGlossaryPage() {
  const { user } = useSession();
  const [figures, setFigures] = useState<PoliticalFigureSummary[]>([]);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  const load = async () => {
    try { setFigures(await api.listGlossaryFigures({ q: query || undefined, category: category === "all" ? undefined : category })); }
    catch (error) { setMessage(error instanceof ApiError ? error.message : "Glossary unavailable"); }
  };
  useEffect(() => {
    let active = true;
    void api.listGlossaryFigures().then((items) => { if (active) setFigures(items); }).catch((error) => { if (active) setMessage(error instanceof ApiError ? error.message : "Glossary unavailable"); });
    return () => { active = false; };
  }, []);
  const categories = useMemo(() => ["all", ...Array.from(new Set(figures.map((figure) => figure.category)))], [figures]);

  if (!user || user.role !== "superadmin") return <main className="mx-auto max-w-4xl px-4 py-12 sm:px-6 sm:py-20"><h1 className="text-2xl font-semibold">Superadmin access required</h1></main>;

  const seed = async () => {
    setBusy(true); setMessage("Seeding official roster and resolving portraits…");
    try { await api.seedGlossary(); setMessage("Glossary seed queued. Refresh this view in a moment."); } catch (error) { setMessage(error instanceof ApiError ? error.message : "Seed failed"); } finally { setBusy(false); }
  };

  return <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-10">
    <div className="flex flex-col items-start gap-5 border-b border-border pb-6 sm:flex-row sm:items-end sm:justify-between sm:pb-7">
      <div><p className="text-xs uppercase tracking-[0.2em] text-muted-foreground sm:tracking-[0.25em]">Superadmin / Intelligence registry</p><h1 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">Political figures glossary</h1><p className="mt-3 max-w-2xl text-sm text-muted-foreground">A source-backed national power map. Profiles stay explicit about freshness, evidence, and unknowns.</p></div>
      <button disabled={busy} onClick={seed} className="w-full bg-foreground px-4 py-3 text-sm text-background disabled:opacity-50 sm:w-auto sm:py-2">{busy ? "Working…" : "Seed / refresh roster"}</button>
    </div>
    <div className="mt-6 grid gap-3 sm:mt-7 sm:flex sm:flex-wrap"><input value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => event.key === "Enter" && void load()} placeholder="Search a figure" className="w-full border border-border bg-transparent px-3 py-3 text-sm sm:min-w-64 sm:flex-1 sm:py-2" aria-label="Search political figures" /><select value={category} onChange={(event) => setCategory(event.target.value)} className="w-full border border-border bg-background px-3 py-3 text-sm sm:w-auto sm:py-2">{categories.map((item) => <option key={item} value={item}>{item === "all" ? "All categories" : item}</option>)}</select><button onClick={() => void load()} className="w-full border border-border px-4 py-3 text-sm sm:w-auto sm:py-2">Search</button></div>
    {message && <p className="mt-4 text-sm text-muted-foreground">{message}</p>}
    <div className="mt-8 grid gap-px border border-border bg-border sm:grid-cols-2 lg:grid-cols-3">{figures.map((figure) => <Link href={`/admin/glossary/${figure.slug}`} key={figure.id} className="group bg-background p-5 transition-colors hover:bg-muted/30"><div className="flex gap-4"><div className="h-16 w-16 shrink-0 overflow-hidden bg-muted">{figure.portrait_url ? <img src={figure.portrait_url} alt="" className="h-full w-full object-cover" /> : <div className="flex h-full items-center justify-center text-xl text-muted-foreground">{figure.canonical_name.slice(0, 1)}</div>}</div><div className="min-w-0"><p className="text-xs uppercase tracking-widest text-muted-foreground">{figure.category}</p><h2 className="mt-1 truncate text-lg font-medium group-hover:underline">{figure.canonical_name}</h2><p className="mt-1 text-sm text-muted-foreground">{figure.current_role || "Role requires refresh"}</p></div></div><div className="mt-4 flex min-h-5 items-center gap-2 text-muted-foreground">{figure.social_platforms.slice(0, 6).map((platform) => <SocialPlatformIcon key={platform} platform={platform} className="h-4 w-4" />)}</div><div className="mt-3 flex justify-between gap-3 text-xs text-muted-foreground"><span className="truncate">{figure.party || "Party not verified"}</span><span className="shrink-0">{figure.last_verified_at ? new Date(figure.last_verified_at).toLocaleDateString() : "Not verified"}</span></div></Link>)}</div>
  </main>;
}
