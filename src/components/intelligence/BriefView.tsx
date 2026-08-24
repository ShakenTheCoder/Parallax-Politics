"use client";

import Image from "next/image";

import type { BriefImportance, ThirtySecondBrief } from "@/lib/api";

type Opinion = NonNullable<ThirtySecondBrief["latest_opinion"]>;
type Rating = ThirtySecondBrief["watchlist"][number];

const IMPORTANCE_LABEL: Record<BriefImportance, string> = {
  critical: "Critical",
  high: "High importance",
  medium: "Medium importance",
  low: "Low importance",
  unrated: "Importance pending",
};

const IMPORTANCE_STYLE: Record<BriefImportance, string> = {
  critical: "border-red-500/70 bg-red-500/10 text-red-500",
  high: "border-orange-500/70 bg-orange-500/10 text-orange-500",
  medium: "border-border bg-muted text-foreground",
  low: "border-border bg-muted text-muted-foreground",
  unrated: "border-dashed border-border text-muted-foreground",
};

function formatDate(value: string | null, includeTime = false): string {
  if (!value) return "Not updated yet";
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    ...(includeTime ? { hour: "numeric", minute: "2-digit" } : {}),
  });
}

function deltaLabel(value: number | null): string {
  if (value === null) return "Change unavailable";
  if (value === 0) return "No change";
  return `${value > 0 ? "↑" : "↓"} ${Math.abs(value).toFixed(1)} points`;
}

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

function RatingRow({ rating }: { rating: Rating }) {
  return (
    <li className={`grid grid-cols-[1.5rem_3rem_minmax(0,1fr)_auto] items-center gap-2 border-t border-border py-4 sm:grid-cols-[1.6rem_3.5rem_minmax(0,1fr)_auto] sm:gap-3 ${rating.is_principal ? "-mx-3 bg-muted/50 px-3" : ""}`}>
      <span className="text-center text-sm font-semibold text-muted-foreground" aria-label={rating.rank ? `Rank ${rating.rank}` : "Rank unavailable"}>
        {rating.rank ?? "—"}
      </span>
      <Portrait url={rating.portrait_url} name={rating.name} size="small" />
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <p className="truncate font-semibold">{rating.name}</p>
          {rating.is_principal && <span className="rounded-full bg-foreground px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-background">You</span>}
        </div>
        <p className="mt-0.5 line-clamp-2 text-xs leading-5 text-muted-foreground">{rating.position || "Position not verified"}</p>
      </div>
      <div className="text-right">
        <p className="text-xl font-semibold tabular-nums">{rating.score?.toFixed(1) ?? "—"}</p>
        <p className={`mt-0.5 whitespace-nowrap text-[11px] ${rating.delta !== null && rating.delta < 0 ? "text-red-500" : "text-muted-foreground"}`}>
          {deltaLabel(rating.delta)}
        </p>
      </div>
    </li>
  );
}

function OpinionCard({ opinion, latest = false }: { opinion: Opinion; latest?: boolean }) {
  return (
    <article className={latest ? "border-l-4 border-l-foreground bg-muted/30 p-5" : "border-t border-border py-5"}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <time className="text-xs text-muted-foreground" dateTime={opinion.generated_at}>{formatDate(opinion.generated_at, true)}</time>
        <span className={`rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide ${IMPORTANCE_STYLE[opinion.importance]}`}>
          {IMPORTANCE_LABEL[opinion.importance]}
        </span>
      </div>
      <p className={`${latest ? "mt-4 text-lg leading-7" : "mt-3 text-sm leading-6"}`}>{opinion.summary}</p>
      <p className="mt-3 text-[11px] text-muted-foreground">
        {opinion.source_count ? `${opinion.source_count} supporting source${opinion.source_count === 1 ? "" : "s"}` : "Supporting sources pending"}
      </p>
    </article>
  );
}

function EmptyState({ children }: { children: React.ReactNode }) {
  return <div className="rounded-xl border border-dashed border-border bg-muted/30 px-5 py-7 text-sm leading-6 text-muted-foreground">{children}</div>;
}

export default function BriefView({ brief }: { brief: ThirtySecondBrief }) {
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

      <section className="mt-8 rounded-2xl bg-muted px-5 py-6 text-foreground sm:px-7" aria-labelledby="current-score">
        <p id="current-score" className="text-[10px] font-semibold uppercase tracking-[0.19em] opacity-65">Current score</p>
        <div className="mt-3 flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between sm:gap-5">
          <p className="text-6xl font-semibold leading-none tracking-[-0.06em] tabular-nums sm:text-7xl">{brief.score.value?.toFixed(1) ?? "—"}</p>
          <div className="text-left sm:pb-1 sm:text-right">
            <p className="text-sm font-semibold">{deltaLabel(brief.score.delta)}</p>
            <p className="mt-1 text-[11px] opacity-65">Updated {formatDate(brief.score.updated_at, true)}</p>
          </div>
        </div>
        {brief.score.value === null && <p className="mt-5 border-t border-foreground/25 pt-4 text-xs leading-5 opacity-75">A score will appear after a source-backed momentum snapshot is produced.</p>}
      </section>

      <section className="mt-10" aria-labelledby="watchlist-ratings">
        <div className="flex flex-col items-start gap-2 sm:flex-row sm:items-end sm:justify-between sm:gap-4">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.19em] text-muted-foreground">Compared on the same evidence window</p>
            <h2 id="watchlist-ratings" className="mt-2 text-2xl font-semibold tracking-tight">Watchlist ratings</h2>
          </div>
          <span className="text-xs text-muted-foreground">Rank · score · change</span>
        </div>
        {brief.watchlist.length ? (
          <ol className="mt-5 border-b border-border">
            {brief.watchlist.map((rating) => <RatingRow key={`${rating.is_principal ? "principal" : "watch"}-${rating.name}`} rating={rating} />)}
          </ol>
        ) : (
          <div className="mt-5"><EmptyState>No evidence-backed watchlist ratings are available yet.</EmptyState></div>
        )}
      </section>

      <section className="mt-10" aria-labelledby="appearances-heading">
        <p className="text-[10px] font-bold uppercase tracking-[0.19em] text-muted-foreground">Last {brief.appearances_window_hours} hours</p>
        <h2 id="appearances-heading" className="mt-2 text-2xl font-semibold tracking-tight">Public media appearances</h2>
        {brief.appearances.length ? (
          <ol className="mt-5 border-b border-border">
            {brief.appearances.map((appearance) => (
              <li key={appearance.id} className="border-t border-border py-5">
                <div className="flex items-start gap-4">
                  <time dateTime={appearance.appeared_at} className="w-16 shrink-0 text-[11px] leading-5 text-muted-foreground">
                    {new Date(appearance.appeared_at).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" })}<br />
                    {new Date(appearance.appeared_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                  </time>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium leading-6">{appearance.caption}</p>
                    <a href={appearance.source_url} target="_blank" rel="noreferrer" className="mt-2 inline-flex max-w-full break-words text-xs font-semibold text-foreground">
                      {appearance.source_name} · Open full source ↗
                    </a>
                  </div>
                </div>
              </li>
            ))}
          </ol>
        ) : (
          <div className="mt-5"><EmptyState>No verified public media appearances were captured in the last {brief.appearances_window_hours} hours.</EmptyState></div>
        )}
      </section>

      <section className="mt-10" aria-labelledby="media-opinion-heading">
        <p className="text-[10px] font-bold uppercase tracking-[0.19em] text-muted-foreground">Public media brief</p>
        <h2 id="media-opinion-heading" className="mt-2 text-2xl font-semibold tracking-tight">Latest opinion about you</h2>
        <div className="mt-5">
          {brief.latest_opinion ? <OpinionCard opinion={brief.latest_opinion} latest /> : <EmptyState>No source-backed media opinion has been produced yet.</EmptyState>}
        </div>

        <h3 className="mt-8 text-sm font-semibold">Previous three opinions</h3>
        {brief.previous_opinions.length ? (
          <div className="mt-2 border-b border-border">
            {brief.previous_opinions.map((opinion) => <OpinionCard key={opinion.id} opinion={opinion} />)}
          </div>
        ) : (
          <div className="mt-4"><EmptyState>Previous opinions will appear here as new 36-hour briefs are generated.</EmptyState></div>
        )}
      </section>

      <p className="mt-10 border-t border-border pt-5 text-[11px] leading-5 text-muted-foreground">{brief.notice}</p>
    </div>
  );
}
