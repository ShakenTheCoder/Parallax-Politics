"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import {
  AgentFleet,
  ApiError,
  api,
  CollectionSource,
  CollectionSubscription,
  IntelligenceOverview,
  IntelligenceScenario,
  isAdminRole,
  PrincipalSummary,
  StrategyVerdict,
} from "@/lib/api";
import { useSession } from "@/lib/SessionContext";
import PoliticalActivityMonitorView from "@/components/intelligence/PoliticalActivityMonitor";

type View = "overview" | "scenarios" | "sources" | "fleet";
type SourceAuthority = "official_api" | "licensed_feed" | "public_web" | "representative_poll" | "consented_panel";

function Metric({ label, value, note }: { label: string; value: string | number; note?: string }) {
  return (
    <div className="border-l border-border pl-4 py-1">
      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold tracking-tight">{value}</p>
      {note && <p className="mt-1 text-xs text-muted-foreground">{note}</p>}
    </div>
  );
}

function Status({ value }: { value: string }) {
  const tone = value === "approved"
    ? "text-emerald-600"
    : value === "rejected" || value === "negative" || value === "degraded"
      ? "text-red-600"
      : value === "draft" || value.includes("review")
        ? "text-amber-600"
        : "text-muted-foreground";
  return <span className={`text-[10px] font-semibold uppercase tracking-[0.16em] ${tone}`}>{value.replaceAll("_", " ")}</span>;
}

function ReviewControls({ verdict, onReviewed }: { verdict: StrategyVerdict; onReviewed: () => void }) {
  const [note, setNote] = useState("");
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");

  const decide = async (decision: "approved" | "rejected") => {
    if (note.trim().length < 3) {
      setError("Record an analyst review note before deciding.");
      return;
    }
    setWorking(true);
    setError("");
    try {
      await api.reviewVerdict(verdict.id, decision, note.trim());
      onReviewed();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Review could not be recorded.");
    } finally {
      setWorking(false);
    }
  };

  return (
    <div className="mt-5 border-t border-border pt-4">
      <label className="block text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground" htmlFor={`review-${verdict.id}`}>
        Analyst review record
      </label>
      <textarea
        id={`review-${verdict.id}`}
        value={note}
        onChange={(event) => setNote(event.target.value)}
        maxLength={1000}
        rows={2}
        className="mt-2 w-full resize-y border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-foreground"
        placeholder="Evidence checked, limitations considered, and reason for decision…"
      />
      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
      <div className="mt-3 flex gap-2">
        <button disabled={working} onClick={() => decide("approved")} className="bg-foreground px-4 py-2 text-xs font-semibold text-background disabled:opacity-50">Approve</button>
        <button disabled={working} onClick={() => decide("rejected")} className="border border-border px-4 py-2 text-xs font-semibold disabled:opacity-50">Reject</button>
      </div>
    </div>
  );
}

export default function IntelligencePage() {
  return <PoliticalActivityMonitorView />;
}

export function LegacyIntelligencePage() {
  const router = useRouter();
  const { user, loading: sessionLoading } = useSession();
  const [view, setView] = useState<View>("overview");
  const [overview, setOverview] = useState<IntelligenceOverview | null>(null);
  const [scenarios, setScenarios] = useState<IntelligenceScenario[]>([]);
  const [verdicts, setVerdicts] = useState<StrategyVerdict[]>([]);
  const [fleet, setFleet] = useState<AgentFleet | null>(null);
  const [sources, setSources] = useState<CollectionSource[]>([]);
  const [subscriptions, setSubscriptions] = useState<CollectionSubscription[]>([]);
  const [principals, setPrincipals] = useState<PrincipalSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [sourceWorking, setSourceWorking] = useState(false);
  const [sourceForm, setSourceForm] = useState<{ name: string; baseUrl: string; authority: SourceAuthority; allowedPath: string }>({ name: "", baseUrl: "", authority: "public_web", allowedPath: "/" });
  const [collectionForm, setCollectionForm] = useState({ sourceId: "", subjectId: "", path: "/", language: "en" as "und" | "en" | "fil", monitor: true });
  const [form, setForm] = useState({
    title: "",
    narrative: "",
    proposedAction: "",
    cohortLabel: "National electorate",
    sampleSize: "100",
    evidenceBasis: "Representative polling and consented panel",
  });

  const isAdmin = isAdminRole(user?.role);
  const verdictByScenario = useMemo(
    () => new Map(verdicts.map((verdict) => [verdict.scenario_id, verdict])),
    [verdicts],
  );

  const load = useCallback(async () => {
    try {
      const [overviewResult, scenarioResult, verdictResult, fleetResult] = await Promise.all([
        api.getIntelligenceOverview(),
        api.listScenarios(),
        api.listVerdicts(),
        api.getAgentFleet(),
      ]);
      setOverview(overviewResult);
      setScenarios(scenarioResult);
      setVerdicts(verdictResult);
      setFleet(fleetResult);
      if (isAdmin) {
        const [sourceResult, subscriptionResult, principalResult] = await Promise.all([
          api.listCollectionSources(),
          api.listCollectionSubscriptions(),
          api.listPrincipals(),
        ]);
        setSources(sourceResult);
        setSubscriptions(subscriptionResult);
        setPrincipals(principalResult);
        setCollectionForm((current) => ({
          ...current,
          sourceId: current.sourceId || sourceResult.find((source) => source.connector_kind === "scrapling")?.id || "",
          subjectId: current.subjectId || principalResult[0]?.profile_id || "",
        }));
      }
      setError("");
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 401) {
        router.replace("/login");
        return;
      }
      setError("The intelligence control plane is temporarily unavailable.");
    } finally {
      setLoading(false);
    }
  }, [isAdmin, router]);

  useEffect(() => {
    if (sessionLoading) return;
    const task = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(task);
  }, [load, sessionLoading]);

  const submitScenario = async (event: FormEvent) => {
    event.preventDefault();
    const sampleSize = Number(form.sampleSize);
    if (!Number.isInteger(sampleSize) || sampleSize < 100) {
      setError("Cohorts must contain at least 100 observations.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      await api.createScenario({
        title: form.title.trim(),
        narrative: form.narrative.trim(),
        proposed_action: form.proposedAction.trim(),
        cohort: {
          label: form.cohortLabel.trim(),
          sample_size: sampleSize,
          regions: ["Philippines"],
          evidence_basis: form.evidenceBasis.trim(),
        },
      });
      setForm((current) => ({ ...current, title: "", narrative: "", proposedAction: "" }));
      setView("scenarios");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Scenario could not be created.");
    } finally {
      setSubmitting(false);
    }
  };

  const registerSource = async (event: FormEvent) => {
    event.preventDefault();
    setSourceWorking(true);
    setError("");
    try {
      const connectorKind = sourceForm.authority === "public_web"
        ? "scrapling"
        : sourceForm.authority === "official_api"
          ? "official_api"
          : "licensed_feed";
      await api.createCollectionSource({
        name: sourceForm.name.trim(),
        base_url: sourceForm.baseUrl.trim(),
        authority: sourceForm.authority,
        connector_kind: connectorKind,
        schedule_minutes: 15,
        robots_observed: true,
        allowed_paths: [sourceForm.allowedPath.trim()],
      });
      setSourceForm({ name: "", baseUrl: "", authority: "public_web", allowedPath: "/" });
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Source could not be registered.");
    } finally {
      setSourceWorking(false);
    }
  };

  const runCollection = async (event: FormEvent) => {
    event.preventDefault();
    if (!collectionForm.sourceId || !collectionForm.subjectId) {
      setError("Select both a registered source and an observed candidate.");
      return;
    }
    setSourceWorking(true);
    setError("");
    try {
      await api.collectSource(collectionForm.sourceId, {
        subject_id: collectionForm.subjectId,
        path: collectionForm.path.trim(),
        language: collectionForm.language,
        event_type: "public_document",
      });
      if (collectionForm.monitor) {
        await api.createCollectionSubscription(collectionForm.sourceId, {
          subject_id: collectionForm.subjectId,
          path: collectionForm.path.trim(),
          language: collectionForm.language,
          event_type: "public_document",
        });
      }
      setView("overview");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Collection could not be completed.");
    } finally {
      setSourceWorking(false);
    }
  };

  if (loading || sessionLoading) {
    return <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-16 text-sm text-muted-foreground">Opening intelligence record…</main>;
  }

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-10 sm:px-8 sm:py-14">
      <header className="max-w-3xl">
        <h1 className="font-serif text-4xl tracking-tight sm:text-5xl">Operational picture</h1>
        <p className="mt-4 max-w-2xl text-sm leading-6 text-muted-foreground">
          Time-bounded public evidence, competitive presence, and calibrated campaign-planning scenarios. Estimates remain provisional until analyst approval.
        </p>
      </header>

      <nav className="mt-10 flex gap-6 border-b border-border" aria-label="Intelligence sections">
        {(["overview", "scenarios", ...(isAdmin ? ["sources" as const] : []), "fleet"] as View[]).map((item) => (
          <button key={item} onClick={() => setView(item)} className={`pb-3 text-xs font-semibold uppercase tracking-[0.15em] ${view === item ? "border-b-2 border-foreground text-foreground" : "text-muted-foreground"}`}>
            {item}
          </button>
        ))}
      </nav>

      {error && <p className="mt-6 border-l-2 border-red-600 pl-3 text-sm text-red-600">{error}</p>}

      {view === "overview" && overview && (
        <div className="mt-10 space-y-12">
          <section className="grid gap-7 sm:grid-cols-2 lg:grid-cols-5">
            <Metric label="Signals · 24h" value={overview.signals_24h} />
            <Metric label="Candidates observed" value={overview.monitored_candidates} />
            <Metric label="Active sources" value={overview.sources_active} />
            <Metric label="Pending review" value={overview.scenarios_pending_review} />
            <Metric label="Freshness" value={overview.freshness_minutes === null ? "No data" : `${overview.freshness_minutes}m`} note="Target ≤ 15 minutes" />
          </section>

          <p className="border-l-2 border-amber-500 bg-amber-500/5 px-4 py-3 text-xs leading-5 text-muted-foreground">{overview.data_notice}</p>

          <section>
            <h2 className="font-serif text-2xl">Competitive presence</h2>
            <div className="mt-5 overflow-x-auto">
              <table className="w-full min-w-[620px] text-left text-sm">
                <thead className="border-b border-border text-[10px] uppercase tracking-[0.15em] text-muted-foreground">
                  <tr><th className="pb-3 font-semibold">Candidate</th><th className="pb-3 font-semibold">Share of voice</th><th className="pb-3 font-semibold">Signals</th><th className="pb-3 font-semibold">Engagement</th><th className="pb-3 font-semibold">Latest evidence</th></tr>
                </thead>
                <tbody>
                  {overview.presence.map((row) => (
                    <tr key={row.subject_id} className="border-b border-border/60">
                      <td className="py-4 font-medium">{row.full_name}</td>
                      <td className="py-4">{row.share_of_voice_pct.toFixed(1)}%</td>
                      <td className="py-4">{row.signal_count}</td>
                      <td className="py-4">{row.engagement_total.toLocaleString()}</td>
                      <td className="py-4 text-muted-foreground">{row.latest_signal_at ? new Date(row.latest_signal_at).toLocaleString() : "—"}</td>
                    </tr>
                  ))}
                  {!overview.presence.length && <tr><td colSpan={5} className="py-8 text-muted-foreground">No normalized candidate signals have entered the current 24-hour window.</td></tr>}
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <h2 className="font-serif text-2xl">Recent evidence</h2>
            <div className="mt-5 divide-y divide-border border-y border-border">
              {overview.recent_signals.map((signal) => (
                <article key={signal.id} className="grid gap-2 py-5 sm:grid-cols-[150px_1fr] sm:gap-6">
                  <div className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                    <p>{signal.platform}</p><p className="mt-1">{new Date(signal.observed_at).toLocaleString()}</p>
                  </div>
                  <div>
                    <a href={signal.url} target="_blank" rel="noopener noreferrer" className="font-medium hover:opacity-70">{signal.title || "Public source record"}</a>
                    <p className="mt-2 line-clamp-3 text-sm leading-6 text-muted-foreground">{signal.content_excerpt}</p>
                  </div>
                </article>
              ))}
              {!overview.recent_signals.length && <p className="py-8 text-sm text-muted-foreground">No evidence records are available yet. An administrator must register and run authorized collection sources.</p>}
            </div>
          </section>
        </div>
      )}

      {view === "scenarios" && (
        <div className="mt-10 grid gap-12 lg:grid-cols-[minmax(0,1fr)_340px]">
          <section className="space-y-8">
            {scenarios.map((scenario) => {
              const verdict = verdictByScenario.get(scenario.id);
              return (
                <article key={scenario.id} className="border-b border-border pb-8">
                  <div className="flex flex-wrap items-center justify-between gap-3"><Status value={scenario.status} /><span className="text-xs text-muted-foreground">{new Date(scenario.created_at).toLocaleString()}</span></div>
                  <h2 className="mt-3 font-serif text-2xl">{scenario.title}</h2>
                  <p className="mt-3 text-sm leading-6 text-muted-foreground">{scenario.narrative}</p>
                  <dl className="mt-5 grid gap-4 bg-muted/30 p-4 text-sm sm:grid-cols-4">
                    <div><dt className="text-[10px] uppercase tracking-wider text-muted-foreground">Direction</dt><dd className="mt-1 capitalize">{scenario.forecast.direction?.replaceAll("_", " ") || "—"}</dd></div>
                    <div><dt className="text-[10px] uppercase tracking-wider text-muted-foreground">Estimated range</dt><dd className="mt-1">{scenario.forecast.lower_pct ?? "—"}% to {scenario.forecast.upper_pct ?? "—"}%</dd></div>
                    <div><dt className="text-[10px] uppercase tracking-wider text-muted-foreground">Confidence</dt><dd className="mt-1">{Math.round((scenario.forecast.confidence ?? 0) * 100)}%</dd></div>
                    <div><dt className="text-[10px] uppercase tracking-wider text-muted-foreground">Evidence</dt><dd className="mt-1">{scenario.forecast.signal_count ?? 0} signals</dd></div>
                  </dl>
                  {verdict && (
                    <div className="mt-5 border-l-2 border-foreground pl-4">
                      <div className="flex items-center gap-3"><Status value={verdict.status} /><span className="text-[10px] uppercase tracking-wider text-muted-foreground">{verdict.risk_level} risk</span></div>
                      <p className="mt-2 text-sm font-medium leading-6">{verdict.recommendation}</p>
                      <p className="mt-2 text-xs leading-5 text-muted-foreground">{verdict.rationale}</p>
                      {isAdmin && verdict.status === "draft" && <ReviewControls verdict={verdict} onReviewed={load} />}
                    </div>
                  )}
                </article>
              );
            })}
            {!scenarios.length && <p className="text-sm text-muted-foreground">No scenario records have been created.</p>}
          </section>

          {!isAdmin && (
            <aside>
              <form onSubmit={submitScenario} className="sticky top-24 space-y-4 border border-border p-5">
                <div><p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">Controlled scenario</p><h2 className="mt-2 font-serif text-xl">Request an estimate</h2></div>
                <input required minLength={3} maxLength={200} value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} placeholder="Scenario title" className="w-full border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-foreground" />
                <textarea required minLength={20} maxLength={4000} rows={4} value={form.narrative} onChange={(event) => setForm({ ...form, narrative: event.target.value })} placeholder="Narrative or public issue to evaluate" className="w-full resize-y border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-foreground" />
                <textarea required minLength={20} maxLength={4000} rows={4} value={form.proposedAction} onChange={(event) => setForm({ ...form, proposedAction: event.target.value })} placeholder="Proposed public communication or action" className="w-full resize-y border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-foreground" />
                <input required minLength={2} maxLength={160} value={form.cohortLabel} onChange={(event) => setForm({ ...form, cohortLabel: event.target.value })} placeholder="Aggregate cohort" className="w-full border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-foreground" />
                <input required type="number" min={100} max={10000000} value={form.sampleSize} onChange={(event) => setForm({ ...form, sampleSize: event.target.value })} aria-label="Cohort sample size" className="w-full border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-foreground" />
                <input required minLength={3} maxLength={240} value={form.evidenceBasis} onChange={(event) => setForm({ ...form, evidenceBasis: event.target.value })} placeholder="Evidence basis" className="w-full border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-foreground" />
                <p className="text-xs leading-5 text-muted-foreground">Only aggregate cohorts of 100 or more are accepted. The result is an estimate and requires analyst review.</p>
                <button disabled={submitting} className="w-full bg-foreground px-4 py-2.5 text-sm font-medium text-background disabled:opacity-50">{submitting ? "Constructing estimate…" : "Create scenario"}</button>
              </form>
            </aside>
          )}
        </div>
      )}

      {view === "fleet" && fleet && (
        <section className="mt-10">
          <p className="max-w-3xl border-l-2 border-foreground pl-4 text-sm leading-6 text-muted-foreground">{fleet.invariant}</p>
          <div className="mt-8 grid gap-x-10 gap-y-7 sm:grid-cols-2 lg:grid-cols-3">
            {fleet.agents.map((agent, index) => (
              <article key={agent.id}>
                <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">{String(index + 1).padStart(2, "0")} · {agent.stage}</p>
                <h2 className="mt-2 font-serif text-xl">{agent.name}</h2>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{agent.role}</p>
              </article>
            ))}
          </div>
        </section>
      )}

      {view === "sources" && isAdmin && (
        <div className="mt-10 grid gap-12 lg:grid-cols-2">
          <section>
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">Source policy registry</p>
            <h2 className="mt-2 font-serif text-2xl">Authorized collection</h2>
            <p className="mt-3 text-sm leading-6 text-muted-foreground">Public collection is same-origin, robots-aware, size-bounded, and protected against private-network access. Authentication and anti-bot bypass are not available.</p>
            <form onSubmit={registerSource} className="mt-6 space-y-3">
              <input required minLength={2} maxLength={160} value={sourceForm.name} onChange={(event) => setSourceForm({ ...sourceForm, name: event.target.value })} placeholder="Source name" className="w-full border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-foreground" />
              <input required type="url" value={sourceForm.baseUrl} onChange={(event) => setSourceForm({ ...sourceForm, baseUrl: event.target.value })} placeholder="https://official-source.ph" className="w-full border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-foreground" />
              <div className="grid grid-cols-2 gap-3">
                <select value={sourceForm.authority} onChange={(event) => setSourceForm({ ...sourceForm, authority: event.target.value as SourceAuthority })} className="border border-border bg-background px-3 py-2 text-sm">
                  <option value="public_web">Public web</option><option value="official_api">Official source</option><option value="licensed_feed">Licensed feed</option><option value="representative_poll">Representative poll</option><option value="consented_panel">Consented panel</option>
                </select>
                <input required value={sourceForm.allowedPath} onChange={(event) => setSourceForm({ ...sourceForm, allowedPath: event.target.value })} placeholder="/news/" className="border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-foreground" />
              </div>
              <button disabled={sourceWorking} className="bg-foreground px-4 py-2.5 text-sm font-medium text-background disabled:opacity-50">Register policy</button>
            </form>

            <div className="mt-8 divide-y divide-border border-y border-border">
              {sources.map((source) => (
                <div key={source.id} className="py-4">
                  <div className="flex items-center justify-between gap-4"><p className="font-medium">{source.name}</p><Status value={source.status} /></div>
                  <p className="mt-1 break-all text-xs text-muted-foreground">{source.base_url}{source.allowed_paths.join(", ")}</p>
                  <p className="mt-2 text-[10px] uppercase tracking-wider text-muted-foreground">{source.authority.replaceAll("_", " ")} · every {source.schedule_minutes} minutes · robots enforced</p>
                </div>
              ))}
              {!sources.length && <p className="py-6 text-sm text-muted-foreground">No collection policies are registered.</p>}
            </div>

            <div className="mt-8">
              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">Active monitoring assignments</p>
              <div className="mt-3 divide-y divide-border border-y border-border">
                {subscriptions.map((subscription) => {
                  const source = sources.find((item) => item.id === subscription.collection_source_id);
                  const principal = principals.find((item) => item.profile_id === subscription.subject_id);
                  return (
                    <div key={subscription.id} className="py-4 text-sm">
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-medium">{principal?.full_name ?? "Unknown identity"}</p>
                        <Status value={subscription.last_error ? "degraded" : subscription.status} />
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">{source?.name ?? "Unknown source"} · {subscription.path}</p>
                      <p className="mt-1 text-[10px] uppercase tracking-wider text-muted-foreground">Next acquisition {new Date(subscription.next_due_at).toLocaleString()} · failures {subscription.consecutive_failures}</p>
                      {subscription.last_error && <p className="mt-2 text-xs text-red-600">{subscription.last_error}</p>}
                    </div>
                  );
                })}
                {!subscriptions.length && <p className="py-6 text-sm text-muted-foreground">No continuous monitoring assignments are active.</p>}
              </div>
            </div>
          </section>

          <section>
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">Manual evidence acquisition</p>
            <h2 className="mt-2 font-serif text-2xl">Collect a public record</h2>
            <form onSubmit={runCollection} className="mt-6 space-y-3 border border-border p-5">
              <label className="block text-xs text-muted-foreground">Registered public-web source<select required value={collectionForm.sourceId} onChange={(event) => setCollectionForm({ ...collectionForm, sourceId: event.target.value })} className="mt-1 block w-full border border-border bg-background px-3 py-2 text-sm text-foreground"><option value="">Select source</option>{sources.filter((source) => source.connector_kind === "scrapling").map((source) => <option key={source.id} value={source.id}>{source.name}</option>)}</select></label>
              <label className="block text-xs text-muted-foreground">Observed candidate<select required value={collectionForm.subjectId} onChange={(event) => setCollectionForm({ ...collectionForm, subjectId: event.target.value })} className="mt-1 block w-full border border-border bg-background px-3 py-2 text-sm text-foreground"><option value="">Select candidate</option>{principals.map((principal) => <option key={principal.profile_id} value={principal.profile_id}>{principal.full_name}</option>)}</select></label>
              <label className="block text-xs text-muted-foreground">Same-origin path<input required value={collectionForm.path} onChange={(event) => setCollectionForm({ ...collectionForm, path: event.target.value })} className="mt-1 block w-full border border-border bg-background px-3 py-2 text-sm text-foreground" /></label>
              <label className="block text-xs text-muted-foreground">Document language<select value={collectionForm.language} onChange={(event) => setCollectionForm({ ...collectionForm, language: event.target.value as "und" | "en" | "fil" })} className="mt-1 block w-full border border-border bg-background px-3 py-2 text-sm text-foreground"><option value="en">English</option><option value="fil">Filipino</option><option value="und">Undetermined</option></select></label>
              <label className="flex items-start gap-2 text-xs leading-5 text-muted-foreground"><input type="checkbox" checked={collectionForm.monitor} onChange={(event) => setCollectionForm({ ...collectionForm, monitor: event.target.checked })} className="mt-1" />Continue authorized monitoring on the registered interval.</label>
              <button disabled={sourceWorking || !sources.some((source) => source.connector_kind === "scrapling") || !principals.length} className="w-full bg-foreground px-4 py-2.5 text-sm font-medium text-background disabled:opacity-50">Collect and normalize</button>
            </form>
          </section>
        </div>
      )}
    </main>
  );
}
