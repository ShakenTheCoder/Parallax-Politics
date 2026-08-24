"use client";

import { FormEvent, useState } from "react";

import { AnalysisCenter as AnalysisCenterData, ScenarioComparison, api } from "@/lib/api";

type Section = "performance" | "narratives" | "appearances" | "competitors" | "audience" | "polling" | "evidence" | "coverage" | "methodology";

const SECTIONS: { id: Section; label: string }[] = [
  { id: "performance", label: "Performance" },
  { id: "narratives", label: "Narratives" },
  { id: "appearances", label: "Appearances" },
  { id: "competitors", label: "Watchlist" },
  { id: "audience", label: "Audience Lab" },
  { id: "polling", label: "Polling" },
  { id: "evidence", label: "Evidence" },
  { id: "coverage", label: "Coverage" },
  { id: "methodology", label: "Method" },
];

function SectionHeader({ eyebrow, title, copy }: { eyebrow: string; title: string; copy: string }) {
  return (
    <header className="max-w-3xl">
      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--signal-blue)]">{eyebrow}</p>
      <h2 className="mt-2 text-3xl font-semibold tracking-[-0.035em]">{title}</h2>
      <p className="mt-3 text-sm leading-6 text-muted-foreground">{copy}</p>
    </header>
  );
}

function Bars({ rows }: { rows: { label: string; value: number; suffix?: string }[] }) {
  return (
    <div className="space-y-4">
      {rows.map((row) => (
        <div key={row.label}>
          <div className="mb-1.5 flex items-center justify-between gap-3 text-xs"><span>{row.label}</span><strong>{row.value}{row.suffix ?? ""}</strong></div>
          <div className="h-1.5 bg-muted"><div className="h-full bg-[var(--signal-blue)]" style={{ width: `${Math.min(100, row.value)}%` }} /></div>
        </div>
      ))}
    </div>
  );
}

function Timeline({ data }: { data: AnalysisCenterData }) {
  const series = data.watchlist.slice(0, 3);
  const colors = ["var(--signal-blue)", "var(--signal-red)", "var(--foreground)"];
  const points = (slug: string) => data.timeline.map((row, index) => {
    const x = 12 + index * (676 / Math.max(1, data.timeline.length - 1));
    const y = 212 - ((row.values[slug] ?? 0) / 100) * 190;
    return `${x},${y}`;
  }).join(" ");
  return (
    <div className="mt-8 border-y border-border py-6">
      <div className="flex flex-wrap gap-5 text-xs">
        {series.map((figure, index) => <span key={figure.slug} className="flex items-center gap-2"><i className="h-0.5 w-5" style={{ background: colors[index] }} />{figure.name}</span>)}
      </div>
      <svg className="mt-5 h-auto w-full" viewBox="0 0 700 230" role="img" aria-label="Fourteen-day provisional momentum overlay for the first three watchlist figures">
        {[25, 50, 75].map((tick) => <g key={tick}><line x1="12" x2="688" y1={212 - tick * 1.9} y2={212 - tick * 1.9} stroke="var(--border)" opacity="0.15" /><text x="0" y={216 - tick * 1.9} fontSize="8" fill="currentColor">{tick}</text></g>)}
        {series.map((figure, index) => <polyline key={figure.slug} points={points(figure.slug)} fill="none" stroke={colors[index]} strokeWidth={index === 0 ? 3 : 2} vectorEffect="non-scaling-stroke" />)}
      </svg>
      <div className="mt-2 flex justify-between text-[10px] text-muted-foreground"><span>{data.timeline[0]?.date}</span><span>{data.timeline.at(-1)?.date}</span></div>
    </div>
  );
}

export default function AnalysisCenter({ data }: { data: AnalysisCenterData }) {
  const [section, setSection] = useState<Section>(() => {
    if (typeof window === "undefined") return "performance";
    const requested = window.location.hash.slice(1);
    if (requested === "audience-lab") return "audience";
    return SECTIONS.some((item) => item.id === requested) ? requested as Section : "performance";
  });
  const [comparison, setComparison] = useState<ScenarioComparison | null>(null);
  const [scenarioError, setScenarioError] = useState("");
  const [scenarioBusy, setScenarioBusy] = useState(false);
  const [variants, setVariants] = useState([
    { id: "a", title: "Service proof", message: "Lead with one completed public-service outcome, name the delivery date, and link the supporting public record." },
    { id: "b", title: "National frame", message: "Frame the same outcome as evidence of national executive readiness while preserving the specific source and date." },
  ]);

  const runComparison = async (event: FormEvent) => {
    event.preventDefault();
    setScenarioBusy(true);
    setScenarioError("");
    try {
      setComparison(await api.compareScenarioVariants(variants));
    } catch (reason) {
      setScenarioError(reason instanceof Error ? reason.message : "Scenario provider unavailable.");
    } finally {
      setScenarioBusy(false);
    }
  };

  const choose = (next: Section) => {
    setSection(next);
    window.history.replaceState(null, "", `#${next}`);
  };

  return (
    <div>
      <nav className="analysis-rail" aria-label="Analysis Center sections">
        {SECTIONS.map((item) => <button key={item.id} type="button" onClick={() => choose(item.id)} className={section === item.id ? "active" : ""}>{item.label}</button>)}
      </nav>

      <div className="mt-10">
        {section === "performance" && (
          <section id="performance">
            <SectionHeader eyebrow="Observed layer · provisional" title="Performance and momentum" copy="Current seven complete days against the immediately preceding seven. Normalization stays inside platform and content format; rank remains withheld while coverage is below 60%." />
            <Timeline data={data} />
            <div className="mt-10 grid gap-10 lg:grid-cols-2">
              <div>
                <h3 className="text-sm font-semibold">Campaign Momentum components</h3>
                <div className="mt-6"><Bars rows={data.momentum_components.map((item) => ({ label: `${item.label} · ${Math.round(item.weight * 100)}%`, value: item.score }))} /></div>
              </div>
              <div>
                <h3 className="text-sm font-semibold">Channel-native comparisons</h3>
                <div className="mt-4 divide-y divide-border border-y border-border">
                  {data.channels.map((channel) => <div key={channel.name} className="grid grid-cols-[1fr_auto] gap-4 py-4"><div><p className="text-sm font-semibold">{channel.name}</p><p className="mt-1 text-xs text-muted-foreground">{channel.comparison}</p></div><div className="text-right"><p className="font-semibold">{channel.score ?? "—"}</p><p className="text-[10px] text-muted-foreground">{Math.round(channel.coverage * 100)}% covered</p></div></div>)}
                </div>
              </div>
            </div>
          </section>
        )}

        {section === "narratives" && (
          <section id="narratives">
            <SectionHeader eyebrow="Clustered public evidence" title="Narrative lifecycle" copy="Velocity and ownership stay provisional until every narrative has source-diverse Signals. Classifier uncertainty remains part of the record." />
            <div className="mt-8 grid gap-px bg-border lg:grid-cols-3">
              {data.narratives.map((item) => <article key={item.name} className="bg-background p-6"><p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--signal-blue)]">{item.stage}</p><h3 className="mt-3 text-xl font-semibold">{item.name}</h3><dl className="mt-6 grid grid-cols-2 gap-4 text-xs"><div><dt className="text-muted-foreground">Velocity</dt><dd className="mt-1 text-lg font-semibold">+{item.velocity}%</dd></div><div><dt className="text-muted-foreground">Source diversity</dt><dd className="mt-1 text-lg font-semibold">{item.source_diversity}</dd></div></dl><p className="mt-5 text-xs">Ownership: <strong>{item.owner}</strong></p></article>)}
            </div>
          </section>
        )}

        {section === "appearances" && (
          <section id="appearances">
            <SectionHeader eyebrow="Appearance workspace" title="From transcript to 72-hour lift" copy="Topic allocation, message consistency, quote pickup, clip response, and lift all point back to a recording, transcript, or visible missing-source state." />
            {data.appearances.map((appearance) => <article key={appearance.id} className="mt-8 grid gap-8 border-y border-border py-7 lg:grid-cols-[minmax(0,1fr)_19rem]"><div><div className="flex flex-wrap items-center gap-3"><h3 className="text-xl font-semibold">{appearance.title}</h3><span className="bg-[var(--signal-wash)] px-2 py-1 text-[10px] font-semibold uppercase">{appearance.source_status.replaceAll("_", " ")}</span></div><p className="mt-2 text-sm text-muted-foreground">{appearance.figure} · {new Date(appearance.occurred_at).toLocaleString()}</p><div className="mt-6"><Bars rows={appearance.topics.map((topic) => ({ label: topic.label, value: Math.round(topic.share * 100), suffix: "%" }))} /></div></div><dl className="grid grid-cols-2 gap-px bg-border"><div className="bg-background p-5"><dt className="text-[10px] uppercase text-muted-foreground">Consistency</dt><dd className="mt-2 text-2xl font-semibold">{Math.round(appearance.message_consistency * 100)}%</dd></div><div className="bg-background p-5"><dt className="text-[10px] uppercase text-muted-foreground">Quote pickup</dt><dd className="mt-2 text-2xl font-semibold">{appearance.quote_pickup}</dd></div>{Object.entries(appearance.lift).map(([window, value]) => <div key={window} className="bg-background p-5"><dt className="text-[10px] uppercase text-muted-foreground">{window} lift</dt><dd className="mt-2 text-2xl font-semibold">+{value}%</dd></div>)}</dl></article>)}
          </section>
        )}

        {section === "competitors" && (
          <section id="competitors">
            <SectionHeader eyebrow="Mechanical same-race relation" title="Six-person research watchlist" copy="Each figure appeared in the same Pulse Asia hypothetical long list. That is the only competitor rule here; none is labeled a filed candidate." />
            <div className="mt-8 overflow-x-auto"><table className="w-full min-w-[880px] text-left text-sm"><thead className="border-b border-border text-[10px] uppercase tracking-[0.14em] text-muted-foreground"><tr><th className="pb-3">Watchlist figure</th><th className="pb-3">Status</th><th className="pb-3">Momentum</th><th className="pb-3">7d</th><th className="pb-3">Strongest channel</th><th className="pb-3">Issue ownership</th><th className="pb-3">Cadence</th></tr></thead><tbody>{data.watchlist.map((figure) => <tr key={figure.slug} className="border-b border-border/50"><td className="py-4"><strong>{figure.name}</strong><p className="mt-1 text-xs text-muted-foreground">{figure.office}</p></td><td className="py-4 text-xs">{figure.watch_status}</td><td className="py-4 font-semibold">{figure.momentum}</td><td className="py-4">{figure.movement > 0 ? "+" : ""}{figure.movement}</td><td className="py-4">{figure.strongest_channel}</td><td className="py-4">{figure.issue}</td><td className="py-4">{figure.cadence}</td></tr>)}</tbody></table></div>
          </section>
        )}

        {section === "audience" && (
          <section id="audience-lab">
            <SectionHeader eyebrow="Explicitly synthetic" title="Audience Lab" copy="Friendly aggregate archetypes evaluate clarity, relevance, credibility, objection risk, recall, and sharing inclination. Three samples per cohort show consensus and variance—never vote share or a best target segment." />
            <div className="mt-8 grid gap-px bg-border sm:grid-cols-2 lg:grid-cols-4">{data.audience_lab.map((cohort) => <article key={cohort.name} className="bg-background p-5"><p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--signal-blue)]">Synthetic · 3 runs</p><h3 className="mt-3 font-semibold">{cohort.name}</h3><p className="mt-2 min-h-10 text-xs leading-5 text-muted-foreground">{cohort.basis}</p><div className="mt-5 flex items-end justify-between"><span className="text-3xl font-semibold">{cohort.consensus}<small className="text-sm">/5</small></span><span className="text-xs">±{cohort.variance}</span></div><p className="mt-4 text-[11px] leading-4 text-muted-foreground">{cohort.note}</p></article>)}</div>

            <form onSubmit={runComparison} className="mt-12 border-t border-border pt-8">
              <h3 className="text-xl font-semibold">Compare message variants</h3>
              <p className="mt-2 text-xs text-muted-foreground">Up to three variants use the frozen Aug 24 Context Pack. This fallback is qualitative and visibly labeled.</p>
              <div className="mt-6 grid gap-5 lg:grid-cols-2">{variants.map((variant, index) => <label key={variant.id} className="block"><span className="text-xs font-semibold">Variant {index + 1} · {variant.title}</span><textarea value={variant.message} onChange={(event) => setVariants((current) => current.map((item) => item.id === variant.id ? { ...item, message: event.target.value } : item))} minLength={20} maxLength={2000} rows={4} className="mt-2 w-full border border-border bg-background p-3 text-sm outline-none focus:ring-2 focus:ring-[var(--signal-blue)]" /></label>)}</div>
              <button disabled={scenarioBusy} className="mt-5 bg-[var(--signal-blue)] px-5 py-3 text-sm font-semibold text-white disabled:opacity-50">{scenarioBusy ? "Running comparison…" : "Compare variants"}</button>
              {scenarioError && <p className="mt-4 border-l-4 border-[var(--signal-red)] pl-4 text-sm">{scenarioError}</p>}
            </form>
            {comparison && <div className="mt-8 grid gap-px bg-border lg:grid-cols-2">{comparison.results.map((result) => <article key={result.id} className="bg-background p-6"><p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--signal-blue)]">{comparison.provider_status.replaceAll("_", " ")}</p><h4 className="mt-3 text-lg font-semibold">{result.title}</h4><p className="mt-4 text-4xl font-semibold">{result.consensus}<small className="text-sm">/5</small></p><p className="mt-1 text-xs">Variance ±{result.variance} · {result.sample_runs_per_cohort} runs/cohort</p><p className="mt-4 text-xs text-muted-foreground">{result.label}</p></article>)}</div>}
          </section>
        )}

        {section === "polling" && (
          <section id="polling">
            <SectionHeader eyebrow="Representative polling layer" title="Polling Center" copy="Polling stays outside Campaign Momentum and synthetic simulation. Question, population, field dates, mode, sample, and uncertainty travel together." />
            <article className="mt-8 grid gap-8 border-y border-border py-7 lg:grid-cols-[20rem_minmax(0,1fr)]"><div><h3 className="text-xl font-semibold">{data.latest_poll.pollster}</h3><p className="mt-2 text-sm">{data.latest_poll.field_dates}</p><dl className="mt-5 space-y-2 text-xs"><div><dt className="text-muted-foreground">Sample</dt><dd>{data.latest_poll.sample.toLocaleString()} · {data.latest_poll.population}</dd></div><div><dt className="text-muted-foreground">Method</dt><dd>{data.latest_poll.mode}</dd></div><div><dt className="text-muted-foreground">Uncertainty</dt><dd>{data.latest_poll.margin_of_error}</dd></div></dl></div><div><p className="text-sm leading-6 text-muted-foreground">{data.latest_poll.question}</p><div className="mt-6"><Bars rows={(data.latest_poll.results ?? []).map((item) => ({ label: item.name, value: item.value, suffix: "%" }))} /></div>{data.latest_poll.source_url && <a href={data.latest_poll.source_url} target="_blank" rel="noreferrer" className="mt-6 inline-block text-xs font-semibold text-[var(--signal-blue)]">Open pollster release ↗</a>}</div></article>
          </section>
        )}

        {section === "evidence" && (
          <section id="evidence">
            <SectionHeader eyebrow="Provenance first" title="Evidence Explorer" copy="Every material claim must retain its source, publication/capture time, geography, rights classification, confidence, and observed-versus-inferred label." />
            <div className="mt-8 divide-y divide-border border-y border-border">{data.evidence.map((item) => <article key={item.id} className="grid gap-3 py-5 lg:grid-cols-[minmax(0,1fr)_17rem]"><div><a href={item.url} target="_blank" rel="noreferrer" className="font-semibold text-[var(--signal-blue)]">{item.title} ↗</a><p className="mt-2 text-xs text-muted-foreground">{item.source} · {item.geography}</p></div><dl className="grid grid-cols-2 gap-3 text-[10px] uppercase tracking-[0.08em]"><div><dt className="text-muted-foreground">Layer</dt><dd className="mt-1">{item.layer}</dd></div><div><dt className="text-muted-foreground">Rights</dt><dd className="mt-1">{item.rights.replaceAll("_", " ")}</dd></div><div><dt className="text-muted-foreground">Capture</dt><dd className="mt-1">{new Date(item.captured_at).toLocaleDateString()}</dd></div><div><dt className="text-muted-foreground">Confidence</dt><dd className="mt-1">{Math.round(item.classification_confidence * 100)}%</dd></div></dl></article>)}</div>
          </section>
        )}

        {section === "coverage" && (
          <section id="coverage">
            <SectionHeader eyebrow="Missing is not zero" title="Data-coverage diagnostics" copy="Availability, freshness, rights usability, and denominator quality determine coverage. The gaps below are why competitive rank is withheld." />
            <div className="mt-8 grid gap-7 lg:grid-cols-[15rem_minmax(0,1fr)]"><div><p className="text-7xl font-semibold tracking-[-0.06em]">{Math.round(data.coverage.confidence * 100)}%</p><p className="mt-3 text-sm">Coverage confidence</p><p className="mt-2 text-xs text-[var(--signal-red)]">Rank publish threshold: {Math.round((data.coverage.threshold ?? 0.6) * 100)}%</p></div><div className="divide-y divide-border border-y border-border">{data.coverage.families?.map((family) => <div key={family.name} className="grid gap-3 py-4 sm:grid-cols-[10rem_6rem_1fr]"><strong className="text-sm">{family.name}</strong><span className={family.status === "missing" ? "text-xs font-semibold text-[var(--signal-red)]" : "text-xs"}>{family.status} · {Math.round(family.score * 100)}%</span><p className="text-xs text-muted-foreground">{family.action}</p></div>)}</div></div>
          </section>
        )}

        {section === "methodology" && (
          <section id="methodology">
            <SectionHeader eyebrow={data.snapshot.model_version} title="Methodology and safeguards" copy="A versioned seven-day index combines only observed public performance and authorized owned analytics. Polling and synthetic archetypes remain separate evidence layers." />
            <div className="mt-8 grid gap-px bg-border sm:grid-cols-2 lg:grid-cols-3">{data.momentum_components.map((item) => <article key={item.key} className="bg-background p-6"><p className="text-3xl font-semibold">{Math.round(item.weight * 100)}%</p><h3 className="mt-2 text-sm font-semibold">{item.label}</h3></article>)}</div><div className="mt-8 border-l-4 border-[var(--signal-blue)] bg-[var(--signal-wash)] p-6 text-sm leading-7"><p><strong>Included:</strong> observed performance and authorized owned analytics.</p><p><strong>Excluded:</strong> polling and synthetic simulation.</p><p><strong>Gating:</strong> no rank below 60% coverage; missing values stay null; weights are not silently redistributed.</p><p><strong>Source rule:</strong> authoritative status and affiliation changes require primary evidence and human review.</p></div>
          </section>
        )}
      </div>
    </div>
  );
}
