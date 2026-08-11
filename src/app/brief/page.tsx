"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  api,
  BriefOut,
  BriefSummary,
  BriefTopic,
  MyIdentityOut,
  streamRunEvents,
  TopicStance,
} from "@/lib/api";

// --- generation step types --------------------------------------------------

type StepKey = "sga" | "dcaa" | "demcaa" | "brief";
type StepStatus = "pending" | "running" | "completed" | "failed";
type GenStatus = "idle" | "generating" | "completed" | "failed" | "budget_exhausted";

const STEP_DEFS: { key: StepKey; label: string }[] = [
  { key: "sga",    label: "Pulling sources" },
  { key: "dcaa",   label: "Domain analysis" },
  { key: "demcaa", label: "Audience analysis" },
  { key: "brief",  label: "Synthesising brief" },
];

type StepState = { key: StepKey; label: string; status: StepStatus };

function makeSteps(): StepState[] {
  return STEP_DEFS.map((d) => ({ ...d, status: "pending" }));
}

function progressPct(steps: StepState[]): number {
  const done = steps.filter((s) => s.status === "completed").length;
  const running = steps.some((s) => s.status === "running") ? 1 : 0;
  return Math.round(((done + running * 0.5) / steps.length) * 100);
}

const POLL_MS = 5000;

// --- helpers -----------------------------------------------------------------

function fmtDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    year: "numeric", month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function SectionTitle({ title }: { title: string }) {
  return <h2 className="text-xs font-semibold tracking-widest uppercase text-muted-foreground">{title}</h2>;
}

// --- subcomponents -----------------------------------------------------------

function TopRiskCard({ brief }: { brief: BriefOut }) {
  const r = brief.top_risk;
  const sev = Math.round(r.severity * 100);
  return (
    <div className="border border-red-500/60 bg-red-500/5 p-5 space-y-2">
      <div className="flex items-baseline justify-between gap-3">
        <p className="text-[10px] font-bold tracking-widest uppercase text-red-500">Top Risk · {r.time_horizon}</p>
        <span className="text-xs text-red-500 font-mono">severity {sev}/100</span>
      </div>
      <p className="text-lg font-semibold">{r.label}</p>
      <p className="text-sm text-muted-foreground">{r.summary}</p>
    </div>
  );
}

function TopOpportunityCard({ brief }: { brief: BriefOut }) {
  const o = brief.top_opportunity;
  const mag = Math.round(o.magnitude * 100);
  return (
    <div className="border border-green-500/60 bg-green-500/5 p-5 space-y-2">
      <div className="flex items-baseline justify-between gap-3">
        <p className="text-[10px] font-bold tracking-widest uppercase text-green-500">Top Opportunity · {o.time_horizon}</p>
        <span className="text-xs text-green-500 font-mono">magnitude {mag}/100</span>
      </div>
      <p className="text-lg font-semibold">{o.label}</p>
      <p className="text-sm text-muted-foreground">{o.summary}</p>
    </div>
  );
}

function TopicRow({ topic, idx }: { topic: BriefTopic; idx: number }) {
  return (
    <div className="border border-border p-4 space-y-2">
      <div className="flex items-start gap-3 min-w-0">
        <span className="text-xs text-muted-foreground font-mono shrink-0">#{idx + 1}</span>
        <p className="font-medium">{topic.topic}</p>
      </div>
      <p className="text-sm text-muted-foreground">{topic.rationale}</p>
      {topic.angle && topic.stance !== "avoid" && (
        <p className="text-sm border-l-2 border-foreground pl-3 italic">
          <span className="text-xs text-muted-foreground uppercase tracking-wide mr-2">Angle</span>
          {topic.angle}
        </p>
      )}
    </div>
  );
}

function NextMoveView({ brief }: { brief: BriefOut }) {
  const ac = brief.action_card;

  const sections = [
    { key: "Who", value: ac.who },
    { key: "Where", value: ac.where },
    { key: "When", value: ac.when },
    { key: "How", value: ac.how },
    { key: "Proof needed", value: ac.proof },
    { key: "Avoid", value: ac.avoid },
  ];

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-baseline justify-between gap-3 border-b border-border pb-3">
        <p className="text-[10px] font-bold tracking-widest uppercase text-muted-foreground">Your Next Move · 24–72h</p>
        <span className="text-xs px-2 py-1 border border-border">{Math.round(ac.confidence * 100)}% confidence</span>
      </div>

      {/* Main action */}
      <p className="text-lg font-semibold leading-snug">{ac.what}</p>

      {/* Action sections - single column for readability */}
      <div className="space-y-3">
        {sections.map(({ key, value }) => (
          <div key={key} className="border border-border border-l-4 border-l-foreground p-4 bg-muted/30">
            <p className="text-[10px] font-bold tracking-widest uppercase text-muted-foreground mb-2">{key}</p>
            <p className="text-sm leading-relaxed">{value}</p>
          </div>
        ))}
      </div>

      {/* Success KPIs */}
      {ac.success_kpis.length > 0 && (
        <div className="border border-border border-l-4 border-l-foreground p-4 bg-muted/30">
          <p className="text-[10px] font-bold tracking-widest uppercase text-muted-foreground mb-3">Success KPIs</p>
          <ul className="space-y-3">
            {ac.success_kpis.map((kpi, i) => (
              <li key={i} className="flex gap-3 text-sm">
                <span className="shrink-0 w-5 h-5 rounded-full border border-foreground text-foreground flex items-center justify-center text-xs font-medium">
                  {i + 1}
                </span>
                <span className="leading-relaxed">{kpi}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function SourcesView({ brief }: { brief: BriefOut }) {
  if (brief.sources.length === 0) return (
    <div className="border border-dashed border-border p-10 text-center">
      <p className="text-muted-foreground">No sources available for this brief.</p>
    </div>
  );
  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between border-b border-border pb-2">
        <SectionTitle title={`Sources (${brief.sources.length})`} />
      </div>
      <div className="space-y-3">
        {brief.sources.map((s, i) => (
          <div key={i} className="border border-border p-4 space-y-3">
            <div className="flex items-start justify-between gap-3">
              <a
                href={s.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-medium hover:underline break-all leading-snug"
              >
                {s.title || s.url}
              </a>
              <span className="text-xs px-2 py-1 border border-border shrink-0">
                {Math.round(s.credibility_score * 100)}%
              </span>
            </div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <p className="text-xs text-muted-foreground">
                {s.domain}{s.published_at ? ` · ${s.published_at}` : ""}
              </p>
              <div className="flex flex-wrap gap-1">
                {s.used_for.slice(0, 3).map((tag, j) => (
                  <span key={j} className="text-[10px] border border-border px-1.5 py-0.5 text-muted-foreground">
                    {tag}
                  </span>
                ))}
                {s.used_for.length > 3 && (
                  <span className="text-[10px] text-muted-foreground">+{s.used_for.length - 3}</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function BriefDetail({ brief, onSeeNextMove }: { brief: BriefOut; onSeeNextMove: () => void }) {
  const [topicTab, setTopicTab] = useState<TopicStance | "all">("lead");

  const leadTopics = brief.topics.filter((t) => t.stance === "lead");
  const engageTopics = brief.topics.filter((t) => t.stance === "engage");
  const avoidTopics = brief.topics.filter((t) => t.stance === "avoid");

  const displayedTopics = topicTab === "all" ? brief.topics :
    topicTab === "lead" ? leadTopics :
    topicTab === "engage" ? engageTopics :
    avoidTopics;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <TopRiskCard brief={brief} />
        <TopOpportunityCard brief={brief} />
      </div>

      {brief.topics.length > 0 && (
        <section className="space-y-3">
          {/* Topic Stance Tabs */}
          <div className="flex items-center gap-1 border-b border-border">
            <button
              onClick={() => setTopicTab("lead")}
              className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 whitespace-nowrap ${
                topicTab === "lead"
                  ? "border-green-500 text-green-500"
                  : "border-transparent text-muted-foreground hover:text-green-500"
              }`}
            >
              Lead <span className="ml-1 text-xs">({leadTopics.length})</span>
            </button>
            <button
              onClick={() => setTopicTab("engage")}
              className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 whitespace-nowrap ${
                topicTab === "engage"
                  ? "border-yellow-500 text-yellow-500"
                  : "border-transparent text-muted-foreground hover:text-yellow-500"
              }`}
            >
              Engage <span className="ml-1 text-xs">({engageTopics.length})</span>
            </button>
            <button
              onClick={() => setTopicTab("avoid")}
              className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 whitespace-nowrap ${
                topicTab === "avoid"
                  ? "border-red-500 text-red-500"
                  : "border-transparent text-muted-foreground hover:text-red-500"
              }`}
            >
              Avoid <span className="ml-1 text-xs">({avoidTopics.length})</span>
            </button>
          </div>

          {/* Topic List */}
          <div className="space-y-2">
            {displayedTopics.length > 0 ? (
              displayedTopics.map((t, i) => <TopicRow key={i} topic={t} idx={i} />)
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">
                No {topicTab} recommendations for this brief.
              </p>
            )}
          </div>
        </section>
      )}

      {/* Action Card teaser with button */}
      <div className="border border-border p-4 sm:p-5 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex-1 min-w-0">
            <p className="text-[10px] font-bold tracking-widest uppercase text-muted-foreground">Next Move · 24–72h</p>
            <p className="text-sm font-medium mt-1 line-clamp-2">{brief.action_card.what}</p>
          </div>
          <button
            onClick={onSeeNextMove}
            className="px-4 py-2 bg-foreground text-background text-sm font-medium hover:opacity-90 transition-opacity shrink-0 w-full sm:w-auto"
          >
            See next move →
          </button>
        </div>
      </div>
    </div>
  );
}

// --- identity panel ----------------------------------------------------------

function IdentityPanel({ data }: { data: MyIdentityOut }) {
  const [open, setOpen] = useState(false);
  const id = data.identity;

  return (
    <section className="border border-border">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-4 hover:bg-border/30 transition-colors"
      >
        <div className="flex items-baseline gap-3 min-w-0">
          <p className="text-xs font-semibold tracking-widest uppercase text-muted-foreground shrink-0">Identity</p>
          <p className="font-medium truncate">{data.full_name}</p>
          {data.role_title && <span className="text-xs text-muted-foreground hidden sm:inline">· {data.role_title}</span>}
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <span className={`text-[10px] tracking-widest border px-2 py-0.5 ${
            data.pidaa_status === "ready" ? "border-green-500 text-green-500" :
            data.pidaa_status === "building" ? "border-yellow-500 text-yellow-500" :
            "border-border text-muted-foreground"
          }`}>{data.pidaa_status}</span>
          <span className="text-muted-foreground text-lg leading-none">{open ? "−" : "+"}</span>
        </div>
      </button>

      {open && id && (() => {
        const basics = id.basics;
        const hasBasics = typeof basics.birth_date === "string" || typeof basics.birthplace === "string" || typeof basics.citizenship === "string" || typeof basics.gender === "string";
        const hasPosition = typeof id.current_position.role === "string";
        const hasParty = Array.isArray(id.party_history) && id.party_history.length > 0;
        const validStances = Object.entries(id.policy_stances).filter(([, v]) => {
          const val = typeof v === "object" && v && "value" in v ? String((v as { value?: string }).value) : typeof v === "string" ? v : "";
          return val && val !== "null" && val !== "";
        });
        const hasStances = validStances.length > 0;
        const controversies = typeof id.controversies === "object" && id.controversies && "items" in id.controversies ? (id.controversies as { items?: unknown }).items : undefined;
        const hasControversies = Array.isArray(controversies) && controversies.length > 0;
        const hasGaps = Array.isArray(id.coverage_gaps) && id.coverage_gaps.length > 0;

        return (
          <div className="border-t border-border p-5 space-y-4 text-sm">
            {/* Basics - only show known fields */}
            {hasBasics && (
              <div className="grid grid-cols-2 gap-3">
                {typeof basics.birth_date === "string" && (
                  <div>
                    <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-0.5">Born</p>
                    <p className="text-sm">{basics.birth_date}</p>
                  </div>
                )}
                {typeof basics.birthplace === "string" && (
                  <div>
                    <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-0.5">Birthplace</p>
                    <p className="text-sm">{basics.birthplace}</p>
                  </div>
                )}
                {typeof basics.citizenship === "string" && (
                  <div>
                    <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-0.5">Citizenship</p>
                    <p className="text-sm">{basics.citizenship}</p>
                  </div>
                )}
                {typeof basics.gender === "string" && (
                  <div>
                    <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-0.5">Gender</p>
                    <p className="text-sm capitalize">{basics.gender}</p>
                  </div>
                )}
              </div>
            )}

            {/* Current Position */}
            {hasPosition && (
              <div>
                <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-1">Current Position</p>
                <p className="text-sm font-medium">{String(id.current_position.role)}</p>
                {(typeof id.current_position.term_start === "string" || typeof id.current_position.term_end === "string") && (
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {typeof id.current_position.term_start === "string" ? id.current_position.term_start : ""} — {typeof id.current_position.term_end === "string" ? id.current_position.term_end : "present"}
                  </p>
                )}
              </div>
            )}

            {/* Party History */}
            {hasParty && (
              <div>
                <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-1">Party Affiliation</p>
                <div className="space-y-1">
                  {(id.party_history as unknown as unknown[]).slice(0, 2).map((p: unknown, i: number) => {
                    const party = typeof p === "object" && p && "party" in p ? String((p as { party: string }).party) : "";
                    const period = typeof p === "object" && p && "period" in p ? String((p as { period?: string }).period) : "";
                    if (!party) return null;
                    return (
                      <div key={i} className="flex items-center gap-2">
                        <span className="text-sm">{party}</span>
                        {period && <span className="text-xs text-muted-foreground">({period})</span>}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Policy Stances - only show those with values */}
            {hasStances && (
              <div>
                <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-2">Key Positions</p>
                <div className="space-y-2">
                  {validStances.slice(0, 4).map(([topic, stance]) => {
                    const val = typeof stance === "object" && stance && "value" in stance ? String((stance as { value?: string }).value) : typeof stance === "string" ? stance : "";
                    return (
                      <div key={topic} className="flex gap-3 items-start">
                        <span className="text-muted-foreground shrink-0 capitalize text-xs w-24">{topic.replace(/_/g, " ")}</span>
                        <span className="text-sm flex-1">{val}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Controversies */}
            {hasControversies && (
              <div>
                <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-2">Controversies</p>
                <div className="space-y-2">
                  {(controversies as { label: string; severity: number; summary: string }[]).slice(0, 3).map((c, i) => (
                    <div key={i} className="border-l-2 border-border pl-3 py-1">
                      <div className="flex justify-between items-center">
                        <span className="font-medium text-sm">{c.label}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 border ${
                          c.severity >= 0.7 ? "border-red-500 text-red-500" :
                          c.severity >= 0.4 ? "border-yellow-500 text-yellow-500" :
                          "border-muted-foreground text-muted-foreground"
                        }`}>
                          {Math.round(c.severity * 10)}/10
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-0.5">{c.summary}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Coverage Gaps */}
            {hasGaps && (
              <div className="pt-2 border-t border-border">
                <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-2">Data Gaps</p>
                <div className="flex flex-wrap gap-1.5">
                  {id.coverage_gaps.slice(0, 5).map((g, i) => (
                    <span key={i} className="text-xs border border-yellow-600/50 text-yellow-600 px-2 py-0.5">{String(g)}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })()}
    </section>
  );
}

// --- history view ------------------------------------------------------------

function HistoryView({
  briefs,
  selectedId,
  onSelect,
}: {
  briefs: BriefSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  if (briefs.length === 0) return (
    <div className="border border-dashed border-border p-10 text-center">
      <p className="text-muted-foreground">No brief history available.</p>
    </div>
  );

  return (
    <section className="space-y-3">
      <div className="border-b border-border pb-2">
        <SectionTitle title={`Brief History (${briefs.length})`} />
      </div>
      <div className="border border-border divide-y divide-border">
        {briefs.map((b) => {
          const isActive = b.id === selectedId;
          return (
            <button
              key={b.id}
              onClick={() => onSelect(b.id)}
              className={`w-full text-left p-4 hover:bg-border/30 transition-colors ${isActive ? "bg-border/20" : ""}`}
            >
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2 mb-2">
                <p className="text-xs text-muted-foreground">{fmtDate(b.created_at)}</p>
                <span className={`text-[10px] px-2 py-0.5 border ${isActive ? "border-foreground" : "border-border"}`}>
                  {Math.round(b.confidence * 100)}% conf
                </span>
              </div>
              <p className="text-sm font-medium leading-snug line-clamp-2">{b.action_what}</p>
              <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2 text-xs text-muted-foreground">
                <span>Risk: <span className="text-foreground">{b.top_risk_label || "—"}</span></span>
                <span>·</span>
                <span>Opp: <span className="text-foreground">{b.top_opportunity_label || "—"}</span></span>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}

// --- progress bar component -------------------------------------------------

function GeneratorProgress({
  genStatus,
  steps,
  error,
}: {
  genStatus: GenStatus;
  steps: StepState[];
  error: string | null;
}) {
  const pct = progressPct(steps);
  const finished = genStatus === "completed";
  const failed = genStatus === "failed" || genStatus === "budget_exhausted";
  const currentStep = steps.find((s) => s.status === "running");

  return (
    <section className="border border-border p-4 space-y-3">
      {/* Progress bar */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-xs text-muted-foreground">
          <span className="font-medium">
            {finished ? "Complete" :
             failed   ? (genStatus === "budget_exhausted" ? "Budget cap reached" : "Failed") :
             currentStep ? currentStep.label : "Starting…"}
          </span>
          <span className={finished ? "text-green-500" : failed ? "text-red-500" : ""}>
            {pct}%
          </span>
        </div>
        <div className="h-1.5 bg-border rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-700 rounded-full ${
              finished ? "bg-green-500" :
              failed   ? "bg-red-500" :
              "bg-foreground"
            }`}
            style={{ width: `${finished ? 100 : pct}%` }}
          />
        </div>
      </div>

      {/* Step list */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {steps.map((s) => (
          <div
            key={s.key}
            className={`border p-2.5 space-y-1 ${
              s.status === "completed" ? "border-green-500/60 bg-green-500/5" :
              s.status === "running"   ? "border-yellow-500/60 bg-yellow-500/5" :
              s.status === "failed"    ? "border-red-500/60 bg-red-500/5" :
              "border-border"
            }`}
          >
            <div className="flex items-center gap-1.5">
              {s.status === "completed" && <span className="text-green-500 text-sm">✓</span>}
              {s.status === "running"   && <span className="inline-block w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />}
              {s.status === "pending"   && <span className="inline-block w-2 h-2 rounded-full bg-border" />}
              {s.status === "failed"    && <span className="text-red-500 text-sm">✗</span>}
              <span className={`text-[10px] font-semibold tracking-widest uppercase ${
                s.status === "completed" ? "text-green-500" :
                s.status === "running"   ? "text-yellow-500" :
                s.status === "failed"    ? "text-red-500" :
                "text-muted-foreground"
              }`}>
                {s.key}
              </span>
            </div>
            <p className="text-xs text-muted-foreground leading-tight">{s.label}</p>
          </div>
        ))}
      </div>

      {error && (
        <div className="text-sm text-red-500 pt-1">{error}</div>
      )}
    </section>
  );
}

// --- main page ---------------------------------------------------------------

export default function BriefPage() {
  const [identity, setIdentity] = useState<MyIdentityOut | null>(null);
  const [briefs, setBriefs] = useState<BriefSummary[]>([]);
  const [active, setActive] = useState<BriefOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [genStatus, setGenStatus] = useState<GenStatus>("idle");
  const [steps, setSteps] = useState<StepState[]>(makeSteps());
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"brief" | "sources" | "nextmove" | "history">("brief");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const eventsAbortRef = useRef<AbortController | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  }, []);

  const closeSSE = useCallback(() => {
    eventsAbortRef.current?.abort();
    eventsAbortRef.current = null;
  }, []);

  // Run exactly once on mount. No dependency on `active` => no refetch loop.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const id = await api.getMyIdentity();
        if (!cancelled) setIdentity(id);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
      try {
        const list = await api.listBriefs();
        if (cancelled) return;
        setBriefs(list);
        if (list.length > 0) {
          try {
            const latest = await api.getLatestBrief();
            if (!cancelled) setActive(latest);
          } catch { /* no latest yet */ }
        }
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        if (!cancelled && !msg.includes("404")) setError(msg);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; stopPolling(); closeSSE(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleGenerate = async () => {
    setGenStatus("generating");
    setSteps(makeSteps());
    setError(null);
    closeSSE();
    stopPolling();
    try {
      const { run_id } = await api.generateBrief();

      // Fetch streaming keeps bearer credentials out of the URL.
      const eventAbort = new AbortController();
      eventsAbortRef.current = eventAbort;
      void (async () => {
        try {
          for await (const event of streamRunEvents(run_id, eventAbort.signal)) {
            const type = String(event.type ?? "");
            if (type === "step.started") {
              const step = event.step as StepKey;
              setSteps((prev) => prev.map((item) => item.key === step ? { ...item, status: "running", label: typeof event.label === "string" ? event.label : item.label } : item));
            } else if (type === "step.completed") {
              const step = event.step as StepKey;
              setSteps((prev) => prev.map((item) => item.key === step ? { ...item, status: "completed" } : item));
            } else if (type === "run.failed" || type === "run.budget_exhausted") {
              setGenStatus(type === "run.failed" ? "failed" : "budget_exhausted");
              setError(typeof event.error === "string" ? event.error : type === "run.failed" ? "Run failed" : "Budget cap reached");
              stopPolling();
            } else if (type === "run.completed") {
              setGenStatus("completed");
              setSteps((prev) => prev.map((item) => ({ ...item, status: "completed" })));
            }
          }
        } catch (error) {
          if (!eventAbort.signal.aborted) setError(error instanceof Error ? error.message : "Run event stream failed");
        }
      })();

      // Poll for the brief row (persisted after run.completed)
      const baseline = briefs.length;
      let attempts = 0;
      pollRef.current = setInterval(async () => {
        attempts += 1;
        try {
          const list = await api.listBriefs();
          if (list.length > baseline) {
            setBriefs(list);
            try { setActive(await api.getLatestBrief()); } catch {}
            stopPolling();
            return;
          }
        } catch {
          stopPolling(); return;
        }
        if (attempts >= 45) {
          stopPolling();
          setError("Brief generation timed out. Check backend logs.");
        }
      }, POLL_MS);

    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setGenStatus("failed");
    }
  };

  const handleSelect = async (id: string) => {
    try {
      const detail = await api.getBrief(id);
      setActive(detail);
      setActiveTab("brief");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const pidaaReady = identity?.pidaa_status === "ready";

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="max-w-4xl mx-auto px-4 py-10 space-y-8">

        {/* Identity panel (collapsible) */}
        {identity && <IdentityPanel data={identity} />}

        {/* Active brief or empty state */}
        {loading ? (
          <p className="text-sm text-muted-foreground text-center py-8">Loading…</p>
        ) : active ? (
          <div className="space-y-6">
            {/* Tabs */}
            <div className="flex items-center justify-between border-b border-border">
              <div className="flex items-center gap-1 overflow-x-auto">
                <button
                  onClick={() => setActiveTab("brief")}
                  className={`px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap ${
                    activeTab === "brief"
                      ? "text-foreground border-b-2 border-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Brief
                </button>
                <button
                  onClick={() => setActiveTab("nextmove")}
                  className={`px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap ${
                    activeTab === "nextmove"
                      ? "text-foreground border-b-2 border-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Next Move
                </button>
                <button
                  onClick={() => setActiveTab("sources")}
                  className={`px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap ${
                    activeTab === "sources"
                      ? "text-foreground border-b-2 border-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Sources ({active.sources.length})
                </button>
                <button
                  onClick={() => setActiveTab("history")}
                  className={`px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap ${
                    activeTab === "history"
                      ? "text-foreground border-b-2 border-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  History ({briefs.length})
                </button>
              </div>
              <button
                onClick={handleGenerate}
                disabled={genStatus === "generating" || !pidaaReady}
                className="px-4 py-2 bg-foreground text-background text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed shrink-0 ml-4"
              >
                {genStatus === "generating" ? "Generating…" : "Generate New Brief"}
              </button>
            </div>

            {/* Generation progress */}
            {(genStatus === "generating" || genStatus === "completed" || genStatus === "failed" || genStatus === "budget_exhausted") && (
              <GeneratorProgress genStatus={genStatus} steps={steps} error={error} />
            )}

            {/* Tab content */}
            {activeTab === "brief" && <BriefDetail brief={active} onSeeNextMove={() => setActiveTab("nextmove")} />}
            {activeTab === "sources" && <SourcesView brief={active} />}
            {activeTab === "nextmove" && <NextMoveView brief={active} />}
            {activeTab === "history" && <HistoryView briefs={briefs} selectedId={active?.id ?? null} onSelect={handleSelect} />}
          </div>
        ) : (
          <div className="border border-dashed border-border p-10 text-center space-y-4">
            <p className="text-muted-foreground">No briefs yet.</p>
            {pidaaReady && (
              <button
                onClick={handleGenerate}
                disabled={genStatus === "generating"}
                className="px-6 py-3 bg-foreground text-background font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {genStatus === "generating" ? "Generating…" : "Generate New Brief"}
              </button>
            )}
            {!pidaaReady && (
              <p className="text-xs text-muted-foreground">
                PIDAA must finish before briefs are available.
              </p>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
