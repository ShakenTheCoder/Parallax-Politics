"use client";

import Image from "next/image";
import { useState } from "react";

import type { ActivityWindow, ThirtySecondBrief } from "@/lib/api";

type Rating = ThirtySecondBrief["watchlist"][number];

function Portrait({ url, name, size = "large" }: { url: string | null; name: string; size?: "large" | "small" }) {
  const sizeClass = size === "large" ? "h-24 w-24 sm:h-28 sm:w-28" : "h-14 w-14";
  return (
    <div className={`${sizeClass} relative shrink-0 overflow-hidden rounded-[0.9rem] bg-muted ring-1 ring-border`}>
      {url ? (
        <Image src={url} alt={`${name} profile`} fill sizes={size === "large" ? "112px" : "56px"} className="object-cover object-top" />
      ) : (
        <span className="flex h-full w-full items-center justify-center text-2xl font-semibold text-muted-foreground" aria-label={`${name} profile picture unavailable`}>
          {name.trim().charAt(0).toUpperCase() || "?"}
        </span>
      )}
    </div>
  );
}

function MonitoringBadge({ state }: { state: Rating["monitoring_state"] }) {
  const tone = state === "emerging"
    ? "border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-300"
    : state === "active"
      ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
      : "border-border bg-muted/40 text-muted-foreground";
  return <span className={`rounded-full border px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] ${tone}`}>{state}</span>;
}

function CompetitorCard({ rating, hours }: { rating: Rating; hours: number }) {
  return (
    <article className="border-b border-border py-4 first:pt-0">
      <div className="flex items-start gap-3">
        <Portrait url={rating.portrait_url} name={rating.name} size="small" />
        <div className="min-w-0 flex-1 pt-0.5">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold leading-5">{rating.name}</h3>
            <MonitoringBadge state={rating.monitoring_state} />
          </div>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">{rating.position || "Position not verified"}</p>
          <p className="mt-2 text-[11px] text-muted-foreground">
            {rating.analyzed_appearances} analyzed {rating.analyzed_appearances === 1 ? "appearance" : "appearances"} · last {hours}h
          </p>
        </div>
      </div>
    </article>
  );
}

export default function BriefView({ brief, onWindowChange, windowLoading = false }: { brief: ThirtySecondBrief; onWindowChange?: (window: ActivityWindow) => void; windowLoading?: boolean }) {
  const [watchlistOpen, setWatchlistOpen] = useState(true);
  const competitors = brief.watchlist.filter((rating) => !rating.is_principal);

  return (
    <div className="mx-auto w-full max-w-2xl pb-12">
      <header className="pt-2 sm:pt-4">
        <section className="flex items-start gap-4 sm:items-center sm:gap-5" aria-labelledby="brief-identity">
          <Portrait url={brief.identity.portrait_url} name={brief.identity.name} />
          <div className="min-w-0">
            <h1 id="brief-identity" className="text-2xl font-semibold leading-tight tracking-[-0.035em] sm:text-4xl">{brief.identity.name}</h1>
            <p className="mt-1 text-sm leading-6 text-muted-foreground">{brief.identity.position || "Position not verified"}</p>
          </div>
        </section>
      </header>

      <section className="mt-10" aria-labelledby="competitors-heading">
        <button
          type="button"
          onClick={() => setWatchlistOpen((open) => !open)}
          className="flex w-full items-center justify-between gap-4 text-left"
          aria-expanded={watchlistOpen}
          aria-controls="competitors-content"
        >
          <div>
            <h2 id="competitors-heading" className="text-2xl font-semibold tracking-tight">Competitors</h2>
            <p className="mt-1 text-xs text-muted-foreground">Verified direct appearances and public statements</p>
          </div>
          <span className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>{watchlistOpen ? "Collapse" : "Expand"}</span>
            <span aria-hidden="true" className="text-lg leading-none">{watchlistOpen ? "−" : "+"}</span>
          </span>
        </button>
        {watchlistOpen && (
          <div id="competitors-content">
            <label className="mt-5 flex items-center justify-between gap-4 border-y border-border py-3 text-xs text-muted-foreground">
              Activity period
              <select
                value={brief.activity_window}
                disabled={windowLoading}
                onChange={(event) => onWindowChange?.(event.target.value as ActivityWindow)}
                className="rounded-md border border-border bg-background px-3 py-2 text-sm font-medium text-foreground disabled:opacity-60"
                aria-label="Competitor activity period"
              >
                <option value="6h">Last 6 hours</option>
                <option value="24h">Last 24 hours</option>
                <option value="7d">Last week</option>
              </select>
            </label>
            {competitors.length ? (
              <div className="mt-5 grid grid-cols-1">
                {competitors.map((competitor) => <CompetitorCard key={competitor.name} rating={competitor} hours={brief.activity_window_hours} />)}
              </div>
            ) : (
              <p className="mt-5 border border-dashed border-border bg-muted/30 px-5 py-7 text-sm leading-6 text-muted-foreground">
                No evidence-backed competitors are available yet.
              </p>
            )}
          </div>
        )}
      </section>

      <p className="mt-10 border-t border-border pt-5 text-[11px] leading-5 text-muted-foreground">{brief.notice}</p>
    </div>
  );
}
