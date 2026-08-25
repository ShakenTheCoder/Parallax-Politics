"use client";

import Image from "next/image";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import {
  ActivityWindow,
  api,
  PoliticalActivityCollection,
  PoliticalActivityMonitor,
  PoliticalActivitySource,
} from "@/lib/api";
import { useSession } from "@/lib/SessionContext";

type Section = "people" | "activity" | "analytics" | "sources";

const WINDOW_LABELS: Record<ActivityWindow, string> = {
  "6h": "Last 6 hours",
  "24h": "Last 24 hours",
  "7d": "Last week",
};

function relativeTime(value: string | null): string {
  if (!value) return "No verified appearance";
  const seconds = Math.max(0, Math.round((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 3600) return `${Math.max(1, Math.round(seconds / 60))}m ago`;
  if (seconds < 86400) return `${Math.round(seconds / 3600)}h ago`;
  return `${Math.round(seconds / 86400)}d ago`;
}

function Portrait({ url, name }: { url: string | null; name: string }) {
  return (
    <div className="relative h-11 w-11 shrink-0 overflow-hidden rounded-xl bg-muted ring-1 ring-border">
      {url ? <Image src={url} alt={`${name} profile`} fill sizes="44px" className="object-cover object-top" /> : (
        <span className="flex h-full items-center justify-center text-sm font-semibold text-muted-foreground">{name.charAt(0)}</span>
      )}
    </div>
  );
}

function StateBadge({ state }: { state: "active" | "quiet" | "emerging" }) {
  const tone = state === "emerging"
    ? "border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-300"
    : state === "active"
      ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
      : "border-border bg-muted/40 text-muted-foreground";
  return <span className={`inline-flex rounded-full border px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] ${tone}`}>{state}</span>;
}

function SourceStatus({ status }: { status: string }) {
  const tone = status === "active"
    ? "text-emerald-700 dark:text-emerald-300"
    : status.includes("required") || status === "blocked"
      ? "text-red-600 dark:text-red-400"
      : "text-amber-700 dark:text-amber-300";
  return <span className={`text-[10px] font-semibold uppercase tracking-[0.12em] ${tone}`}>{status.replaceAll("_", " ")}</span>;
}

export default function PoliticalActivityMonitorView() {
  const router = useRouter();
  const { user, loading: sessionLoading } = useSession();
  const [period, setPeriod] = useState<ActivityWindow>("24h");
  const [section, setSection] = useState<Section>("people");
  const [monitor, setMonitor] = useState<PoliticalActivityMonitor | null>(null);
  const [sources, setSources] = useState<PoliticalActivitySource[]>([]);
  const [result, setResult] = useState<PoliticalActivityCollection | null>(null);
  const [loading, setLoading] = useState(true);
  const [collecting, setCollecting] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (user?.role !== "superadmin") return;
    setLoading(true);
    try {
      let sourceResult = await api.listPoliticalActivitySources();
      if (!sourceResult.length) sourceResult = await api.bootstrapPoliticalActivitySources();
      const monitorResult = await api.getPoliticalActivityMonitor(period);
      setMonitor(monitorResult);
      setSources(sourceResult);
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Activity monitor could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [period, user?.role]);

  useEffect(() => {
    if (sessionLoading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    if (user.role !== "superadmin") {
      router.replace("/brief");
      return;
    }
    const task = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(task);
  }, [load, router, sessionLoading, user]);

  const collect = async () => {
    setCollecting(true);
    setError("");
    try {
      const collection = await api.collectPoliticalActivity();
      setResult(collection);
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Collection run failed.");
    } finally {
      setCollecting(false);
    }
  };

  const sourceStats = useMemo(() => ({
    active: sources.filter((source) => source.status === "active").length,
    review: sources.filter((source) => source.status.includes("review") || source.status.includes("channel")).length,
    blocked: sources.filter((source) => source.status === "blocked" || source.status.includes("required")).length,
  }), [sources]);
  const analytics = useMemo(() => {
    const topics = new Map<string, number>();
    const publishers = new Map<string, number>();
    const layers = new Map<string, number>();
    for (const activity of monitor?.recent_activity || []) {
      topics.set(activity.topic, (topics.get(activity.topic) || 0) + 1);
      publishers.set(activity.publisher, (publishers.get(activity.publisher) || 0) + 1);
      layers.set(activity.evidence_layer, (layers.get(activity.evidence_layer) || 0) + 1);
    }
    const ranked = (values: Map<string, number>) => [...values.entries()].sort((a, b) => b[1] - a[1]);
    return { topics: ranked(topics), publishers: ranked(publishers), layers: ranked(layers) };
  }, [monitor]);
  const meaningfulChanges = useMemo(
    () => (monitor?.people || []).filter((person) => person.monitoring_state === "emerging" || person.activity_change !== "steady").slice(0, 4),
    [monitor],
  );

  if (sessionLoading) return <main className="mx-auto w-full max-w-7xl flex-1 px-5 py-16 text-sm text-muted-foreground">Opening public activity monitor…</main>;
  if (!user || user.role !== "superadmin") return null;
  if (loading) return <main className="mx-auto w-full max-w-7xl flex-1 px-5 py-16 text-sm text-muted-foreground">Opening public activity monitor…</main>;

  return (
    <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-8 sm:py-12">
      <header className="grid gap-6 border-b border-border pb-8 lg:grid-cols-[1fr_auto] lg:items-end">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--signal-blue)]">Intelligence Center · Public activity</p>
          <h1 className="mt-3 text-4xl font-semibold tracking-[-0.04em] sm:text-5xl">Thirty people. One evidence feed.</h1>
          <p className="mt-4 max-w-3xl text-sm leading-6 text-muted-foreground">Verified appearances and statements are counted separately from indirect coverage and public reaction. Every record keeps its direct source, publisher overlap, and confidence basis.</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <select value={period} onChange={(event) => setPeriod(event.target.value as ActivityWindow)} className="rounded-md border border-border bg-background px-3 py-2.5 text-sm font-medium" aria-label="Activity comparison period">
            {Object.entries(WINDOW_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          <button onClick={collect} disabled={collecting || monitor?.llm_status !== "ready"} className="rounded-md bg-foreground px-4 py-2.5 text-sm font-semibold text-background disabled:opacity-50">{collecting ? "Analyzing…" : "Run monitor now"}</button>
        </div>
      </header>

      {error && <p className="mt-6 border-l-2 border-red-600 pl-3 text-sm text-red-600">{error}</p>}
      {result && <p className="mt-6 border-l-2 border-emerald-600 bg-emerald-500/5 px-4 py-3 text-xs leading-5">Last run: {result.activities_created} created, {result.activities_merged} matched to existing events, {result.sources_checked} sources checked. {result.errors.length ? `${result.errors.length} connector or extraction errors remain visible.` : "No connector errors."}</p>}

      {monitor && (
        <>
          <section className="grid grid-cols-2 gap-4 border-b border-border py-7 sm:grid-cols-4">
            <div><p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">People</p><p className="mt-1 text-2xl font-semibold">{monitor.people_monitored}</p></div>
            <div><p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">Verified records</p><p className="mt-1 text-2xl font-semibold">{monitor.recent_activity.filter((item) => item.evidence_layer === "direct_appearance" || item.evidence_layer === "public_statement").length}</p></div>
            <div><p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">Active sources</p><p className="mt-1 text-2xl font-semibold">{monitor.active_sources}</p></div>
            <div><p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">Ollama ingestion</p><p className="mt-1 text-lg font-semibold capitalize">{monitor.llm_status.replaceAll("_", " ")}</p></div>
          </section>

          <section className="border-b border-border py-7">
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">Meaningful changes · {WINDOW_LABELS[monitor.window]}</p>
            {meaningfulChanges.length ? <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{meaningfulChanges.map((person) => <article key={person.figure_id} className="border-l-2 border-[var(--signal-blue)] pl-3"><div className="flex items-center gap-2"><StateBadge state={person.monitoring_state} /><span className="text-xs text-muted-foreground">{person.activity_change === "up" ? "↑" : "↓"} vs prior period</span></div><p className="mt-2 font-semibold">{person.person}</p><p className="mt-1 text-xs leading-5 text-muted-foreground">{person.current_count} verified · {person.main_topic || "topic unavailable"}</p></article>)}</div> : <p className="mt-3 text-sm text-muted-foreground">No verified change clears the meaningful-change rule. Coverage gaps remain visible in the source registry.</p>}
          </section>

          <nav className="flex gap-6 border-b border-border" aria-label="Activity monitor sections">
            {(["people", "activity", "analytics", "sources"] as Section[]).map((item) => <button key={item} onClick={() => setSection(item)} className={`py-4 text-xs font-semibold uppercase tracking-[0.14em] ${section === item ? "border-b-2 border-foreground" : "text-muted-foreground"}`}>{item === "people" ? "People" : item === "activity" ? "Evidence feed" : item === "analytics" ? "Analytics" : "Source registry"}</button>)}
          </nav>

          {section === "people" && (
            <section className="mt-7">
              <div className="hidden grid-cols-[minmax(240px,1.5fr)_150px_minmax(160px,1fr)_130px_130px] gap-5 border-b border-border pb-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground md:grid">
                <span>Person</span><span>Last appearance</span><span>Main topic</span><span>Activity</span><span>Sources</span>
              </div>
              <div className="divide-y divide-border">
                {monitor.people.map((person) => (
                  <article key={person.figure_id} className="grid gap-4 py-5 md:grid-cols-[minmax(240px,1.5fr)_150px_minmax(160px,1fr)_130px_130px] md:items-center md:gap-5">
                    <div className="flex min-w-0 items-center gap-3"><Portrait url={person.portrait_url} name={person.person} /><div className="min-w-0"><p className="truncate font-semibold">{person.person}</p><p className="mt-1 truncate text-xs text-muted-foreground">{person.position || "Role not verified"}</p></div></div>
                    <p className="text-sm"><span className="mr-2 text-[10px] uppercase text-muted-foreground md:hidden">Last</span>{relativeTime(person.last_appearance_at)}</p>
                    <p className="text-sm"><span className="mr-2 text-[10px] uppercase text-muted-foreground md:hidden">Topic</span>{person.main_topic || "No recent verified topic"}</p>
                    <div className="flex items-center gap-2"><StateBadge state={person.monitoring_state} /><span className="text-xs tabular-nums text-muted-foreground">{person.activity_change === "up" ? "↑" : person.activity_change === "down" ? "↓" : "→"} {person.current_count}</span></div>
                    <div className="text-sm"><p>{person.source_count ? `${person.source_count} source${person.source_count === 1 ? "" : "s"}` : "—"}</p><p className="mt-1 text-[10px] uppercase tracking-[0.1em] text-muted-foreground">{person.confidence_label} confidence</p></div>
                  </article>
                ))}
              </div>
            </section>
          )}

          {section === "activity" && (
            <section className="mt-7 divide-y divide-border border-y border-border">
              {monitor.recent_activity.map((activity) => (
                <article key={activity.id} className="grid gap-4 py-6 md:grid-cols-[190px_1fr_180px]">
                  <div className="flex gap-3"><Portrait url={activity.portrait_url} name={activity.person} /><div><p className="font-semibold">{activity.person}</p><p className="mt-1 text-xs capitalize text-muted-foreground">{activity.evidence_layer.replaceAll("_", " ")}</p></div></div>
                  <div><div className="flex flex-wrap gap-2 text-[10px] font-semibold uppercase tracking-[0.11em] text-muted-foreground"><span>{activity.appearance_type.replaceAll("_", " ")}</span><span>·</span><span>{activity.initiation.replaceAll("_", " ")}</span></div><h2 className="mt-2 text-lg font-semibold">{activity.topic}</h2><p className="mt-2 text-sm leading-6 text-muted-foreground">{activity.summary}</p>{activity.venue_program && <p className="mt-2 text-xs">Venue/program: {activity.venue_program}</p>}</div>
                  <div className="text-sm"><p>{new Date(activity.occurred_at).toLocaleString()}</p><a href={activity.direct_source_url} target="_blank" rel="noopener noreferrer" className="mt-3 inline-block font-semibold text-[var(--signal-blue)] hover:underline">{activity.publisher} ↗</a><p className="mt-2 text-xs text-muted-foreground">{Math.round(activity.evidence_confidence * 100)}% evidence confidence · {activity.source_links.length} linked source{activity.source_links.length === 1 ? "" : "s"}</p></div>
                </article>
              ))}
              {!monitor.recent_activity.length && <p className="py-12 text-sm text-muted-foreground">No normalized activity has been published for this period. Check source health before interpreting this as silence.</p>}
            </section>
          )}

          {section === "analytics" && (
            <section className="mt-7 grid gap-10 lg:grid-cols-3">
              <div><h2 className="text-lg font-semibold">Topic frequency</h2><div className="mt-4 divide-y divide-border border-y border-border">{analytics.topics.slice(0, 10).map(([label, count]) => <p key={label} className="flex justify-between gap-4 py-3 text-sm"><span>{label}</span><strong>{count}</strong></p>)}{!analytics.topics.length && <p className="py-6 text-sm text-muted-foreground">No topic records in this period.</p>}</div></div>
              <div><h2 className="text-lg font-semibold">Publisher distribution</h2><div className="mt-4 divide-y divide-border border-y border-border">{analytics.publishers.slice(0, 10).map(([label, count]) => <p key={label} className="flex justify-between gap-4 py-3 text-sm"><span>{label}</span><strong>{count}</strong></p>)}{!analytics.publishers.length && <p className="py-6 text-sm text-muted-foreground">No publisher records in this period.</p>}</div></div>
              <div><h2 className="text-lg font-semibold">Evidence layers</h2><div className="mt-4 divide-y divide-border border-y border-border">{analytics.layers.map(([label, count]) => <p key={label} className="flex justify-between gap-4 py-3 text-sm"><span className="capitalize">{label.replaceAll("_", " ")}</span><strong>{count}</strong></p>)}{!analytics.layers.length && <p className="py-6 text-sm text-muted-foreground">No evidence records in this period.</p>}</div><div className="mt-7 border border-border p-4"><p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Confidence method</p><p className="mt-2 text-xs leading-5 text-muted-foreground">Evidence confidence combines registry source tier (40%), deterministic identity attribution (35%), and Ollama classification confidence (25%). Corroborating links raise confidence but never convert indirect coverage into an appearance. Geography and source overlap remain attached to each evidence record.</p></div></div>
            </section>
          )}

          {section === "sources" && (
            <section className="mt-7">
              <div className="grid gap-3 sm:grid-cols-3"><p className="border border-border p-4 text-sm"><strong>{sourceStats.active}</strong> active</p><p className="border border-border p-4 text-sm"><strong>{sourceStats.review}</strong> awaiting review</p><p className="border border-border p-4 text-sm"><strong>{sourceStats.blocked}</strong> blocked/credentialed</p></div>
              <p className="mt-5 text-xs leading-5 text-muted-foreground">Blocked sources remain mandatory coverage gaps. The monitor never responds to a 403 or platform authorization gate with stealth scraping.</p>
              <div className="mt-5 divide-y divide-border border-y border-border">
                {sources.map((source) => <article key={source.id} className="grid gap-3 py-4 md:grid-cols-[minmax(220px,1fr)_150px_180px_130px]"><div><a href={source.url} target="_blank" rel="noopener noreferrer" className="font-semibold hover:underline">{source.name}</a><p className="mt-1 text-xs text-muted-foreground">{source.figure_name || source.publisher}</p></div><p className="text-xs capitalize">{source.source_class.replaceAll("_", " ")} · {source.platform}</p><p className="text-xs">{source.access_method.replaceAll("_", " ")}<br/><span className="text-muted-foreground">{source.rights.replaceAll("_", " ")}</span></p><div><SourceStatus status={source.status} />{source.last_error && <p className="mt-2 text-[10px] text-red-600">{source.last_error}</p>}</div></article>)}
              </div>
            </section>
          )}
        </>
      )}
    </main>
  );
}
