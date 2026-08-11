"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { api, getToken, PrincipalDetail } from "@/lib/api";

const sectionLabels: Record<string, string> = {
  family: "Family and personal life",
  education: "Education",
  career_timeline: "Political career",
  current_position: "Current office",
  party_history: "Political affiliations",
  electoral_record: "Electoral history",
  policy_stances: "Political positions",
  voice_signature: "Public communication",
  controversies: "Controversies and proceedings",
  network: "Political relationships",
};

function titleCase(value: string) {
  return value.replace(/^_+/, "").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function isEmpty(value: unknown): boolean {
  if (value == null || value === "") return true;
  if (Array.isArray(value)) return value.length === 0 || value.every(isEmpty);
  if (typeof value === "object") return Object.entries(value as Record<string, unknown>).filter(([key]) => !key.startsWith("_")).every(([, item]) => isEmpty(item));
  return false;
}

function ReadableValue({ value }: { value: unknown }) {
  if (isEmpty(value)) return null;
  if (Array.isArray(value)) {
    return <ul className="my-2 space-y-2 pl-5">{value.map((item, index) => <li key={index} className="list-disc"><ReadableValue value={item} /></li>)}</ul>;
  }
  if (typeof value === "object" && value) {
    const entries = Object.entries(value as Record<string, unknown>).filter(([key, item]) => !key.startsWith("_") && !isEmpty(item));
    return <dl className="my-2 space-y-2">{entries.map(([key, item]) => <div key={key} className="grid gap-1 sm:grid-cols-[10rem_1fr]"><dt className="text-sm font-medium text-muted-foreground">{titleCase(key)}</dt><dd><ReadableValue value={item} /></dd></div>)}</dl>;
  }
  if (typeof value === "boolean") return <span>{value ? "Yes" : "No"}</span>;
  return <span>{String(value)}</span>;
}

function IdentityRecord() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const profileId = searchParams.get("profileId");
  const [detail, setDetail] = useState<PrincipalDetail | null>(null);
  const [error, setError] = useState("");
  const [imageFailed, setImageFailed] = useState(false);

  useEffect(() => {
    if (!getToken()) { router.replace("/login"); return; }
    if (!profileId) { setError("No identity record was selected."); return; }
    let active = true;
    let timer: ReturnType<typeof setInterval> | undefined;
    const load = async () => {
      try {
        const record = await api.getPrincipalDetail(profileId);
        if (!active) return;
        setDetail(record);
        setError("");
        if (record.pidaa_status === "ready" && timer) clearInterval(timer);
      } catch { if (active) setError("The requested identity record is unavailable."); }
    };
    void load();
    timer = setInterval(load, 5000);
    return () => { active = false; if (timer) clearInterval(timer); };
  }, [profileId, router]);

  const sections = useMemo(() => {
    if (!detail) return [];
    return Object.entries(sectionLabels)
      .map(([key, label]) => ({ label, data: detail.identity[key as keyof typeof detail.identity] }))
      .filter(({ data }) => !isEmpty(data));
  }, [detail]);

  if (error) return <main className="mx-auto min-h-screen max-w-3xl px-5 py-12"><Link href="/admin" className="text-sm text-muted-foreground hover:text-foreground">← Identity registry</Link><p className="mt-8">{error}</p></main>;
  if (!detail) return <main className="mx-auto min-h-screen max-w-3xl px-5 py-12 text-sm text-muted-foreground">Retrieving identity record…</main>;

  const basics = detail.identity.basics as Record<string, unknown>;
  const portraitUrl = detail.profile_image_url || detail.identity.profile_image_url || (typeof basics.profile_image_url === "string" ? basics.profile_image_url : null);
  const summary = detail.overview || (typeof basics.summary === "string" ? basics.summary : null);
  const sources = ((detail.identity.source_index as Record<string, unknown>)?.sources as Array<Record<string, unknown>> | undefined) ?? [];

  return <main className="min-h-screen bg-background text-foreground">
    <article className="mx-auto max-w-4xl px-5 py-8 sm:px-8 sm:py-12">
      <Link href="/admin" className="text-xs uppercase tracking-[0.16em] text-muted-foreground hover:text-foreground">← Identity registry</Link>

      <header className="mt-10">
        <p className="mb-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">Verified political biography</p>
        <h1 className="font-serif text-4xl leading-tight sm:text-5xl">{detail.full_name}</h1>
        <p className="mt-3 text-lg text-muted-foreground">{detail.role_title || "Role pending verification"}{detail.party ? ` · ${detail.party}` : ""}</p>
        <p className="mt-2 text-xs text-muted-foreground">Last verified {detail.built_at ? new Date(detail.built_at).toLocaleDateString() : "pending"} · {detail.pidaa_status === "enriching" ? "Deep research in progress" : "Evidence record ready"}</p>
      </header>

      <div className="mt-10 flow-root">
        <aside className="mb-8 bg-muted/60 p-4 sm:float-right sm:mb-6 sm:ml-8 sm:w-72">
          <div className="aspect-[4/5] overflow-hidden bg-background">
            {portraitUrl && !imageFailed ? <img src={portraitUrl} onError={() => setImageFailed(true)} alt={`Portrait of ${detail.full_name}`} className="h-full w-full object-cover object-top" /> : <div className="flex h-full items-center justify-center text-6xl text-muted-foreground/50">{detail.full_name.slice(0, 1)}</div>}
          </div>
          <dl className="mt-4 space-y-3 text-sm">
            <div><dt className="text-xs uppercase tracking-wider text-muted-foreground">Name</dt><dd className="mt-0.5 font-medium">{detail.full_name}</dd></div>
            {detail.role_title && <div><dt className="text-xs uppercase tracking-wider text-muted-foreground">Office</dt><dd className="mt-0.5">{detail.role_title}</dd></div>}
            {detail.party && <div><dt className="text-xs uppercase tracking-wider text-muted-foreground">Party</dt><dd className="mt-0.5">{detail.party}</dd></div>}
            {!isEmpty(basics.born) && <div><dt className="text-xs uppercase tracking-wider text-muted-foreground">Born</dt><dd className="mt-0.5"><ReadableValue value={basics.born} /></dd></div>}
            {!isEmpty(basics.birthplace) && <div><dt className="text-xs uppercase tracking-wider text-muted-foreground">Birthplace</dt><dd className="mt-0.5"><ReadableValue value={basics.birthplace} /></dd></div>}
          </dl>
        </aside>

        <section className="text-[1.02rem] leading-8">
          {summary ? <p>{summary}</p> : <p>{detail.full_name} is a Philippine political figure currently recorded as {detail.role_title || "holding public office"}.</p>}
          {!isEmpty(basics.aliases) && <p className="mt-4"><span className="font-medium">Also known as: </span><ReadableValue value={basics.aliases} /></p>}
        </section>

        <div className="mt-12 space-y-12">
          {sections.map(({ label, data }) => <section key={label}>
            <h2 className="mb-4 font-serif text-2xl">{label}</h2>
            <div className="text-[0.98rem] leading-7"><ReadableValue value={data} /></div>
          </section>)}
          {sections.length === 0 && <section><h2 className="mb-4 font-serif text-2xl">Research status</h2><p className="text-muted-foreground">Deep biographical research is in progress. Verified sections will appear here automatically.</p></section>}
        </div>
      </div>

      {sources.length > 0 && <section className="mt-14">
        <h2 className="mb-4 font-serif text-2xl">References</h2>
        <ol className="space-y-2 pl-5 text-sm text-muted-foreground">{sources.map((source, index) => <li key={index} className="list-decimal"><a href={String(source.url || "#")} target="_blank" rel="noopener noreferrer" className="hover:text-foreground">{String(source.title || source.domain || source.url || "Source")}</a></li>)}</ol>
      </section>}
    </article>
  </main>;
}

export default function IdentityPage() {
  return <Suspense fallback={<main className="mx-auto min-h-screen max-w-3xl px-5 py-12 text-sm text-muted-foreground">Retrieving identity record…</main>}><IdentityRecord /></Suspense>;
}
