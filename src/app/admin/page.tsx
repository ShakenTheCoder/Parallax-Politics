"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ScrambleLoader } from "@/components/ui/loader";
import {
  api,
  ApiError,
  getToken,
  IdentityCandidate,
  PrincipalDetail,
  PrincipalSummary,
  CreatePrincipalOut,
} from "@/lib/api";

// --- small helpers -----------------------------------------------------------

function StatusBadge({ status }: { status: string }) {
  const color = {
    ready: "text-emerald-700 border-emerald-600 bg-emerald-500/10",
    building: "text-amber-700 border-amber-600 bg-amber-500/10",
    pending: "text-sky-700 border-sky-600 bg-sky-500/10",
    failed: "text-red-700 border-red-600 bg-red-500/10",
  }[status] ?? "text-muted-foreground border-border";
  return (
    <span className={`text-[10px] font-semibold uppercase tracking-widest border px-2 py-1 ${color}`}>
      {status === "building" ? <ScrambleLoader target="ANALYZING" label="PIDAA is analyzing identity" className="text-[10px]" /> : status}
    </span>
  );
}

function Tag({ label }: { label: string }) {
  return <span className="text-[10px] uppercase tracking-widest border border-border px-2 py-1 text-muted-foreground">{label}</span>;
}

function SectionTitle({ title }: { title: string }) {
  return <p className="text-xs font-semibold tracking-widest uppercase text-muted-foreground mb-2">{title}</p>;
}

// --- Credentials modal -------------------------------------------------------

function CredentialsModal({ creds, onDismiss }: { creds: CreatePrincipalOut["credentials"]; onDismiss: () => void }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(`Username: ${creds.username}\nPassword: ${creds.password}`);
    setCopied(true);
  };
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4">
      <div className="bg-background border border-border p-8 w-full max-w-sm space-y-6">
        <div className="space-y-1">
          <h2 className="text-lg font-bold">Credentials — shown once</h2>
          <p className="text-xs text-muted-foreground">Save these now. The password cannot be retrieved again.</p>
        </div>
        <div className="space-y-3 font-mono text-sm border border-border p-4">
          <div><span className="text-muted-foreground">Username: </span>{creds.username}</div>
          <div><span className="text-muted-foreground">Password: </span>{creds.password}</div>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:gap-3">
          <button
            onClick={copy}
            className="min-h-11 flex-1 px-4 py-2 border border-border text-sm hover:bg-muted transition-colors"
          >
            {copied ? "Copied ✓" : "Copy"}
          </button>
          <button
            onClick={onDismiss}
            className="min-h-11 flex-1 px-4 py-2 bg-foreground text-background text-sm font-medium border border-foreground hover:bg-muted hover:text-foreground transition-colors"
          >
            I&apos;ve saved these
          </button>
        </div>
      </div>
    </div>
  );
}

// --- Identity drawer ---------------------------------------------------------

function IdentityDrawer({ detail, onClose }: { detail: PrincipalDetail; onClose: () => void }) {
  const id = detail.identity;

  function JsonBlock({ data }: { data: Record<string, unknown> }) {
    if (!data || !Object.keys(data).length) return <p className="text-xs text-muted-foreground italic">No data</p>;
    return <pre className="text-xs font-mono whitespace-pre-wrap text-muted-foreground overflow-auto max-h-48">{JSON.stringify(data, null, 2)}</pre>;
  }

  const sections = [
    ["Basics", id.basics],
    ["Family", id.family],
    ["Education", id.education],
    ["Career Timeline", id.career_timeline],
    ["Current Position", id.current_position],
    ["Party History", id.party_history],
    ["Electoral Record", id.electoral_record],
    ["Policy Stances", id.policy_stances],
    ["Voice Signature", id.voice_signature],
    ["Controversies", id.controversies],
    ["Network", id.network],
  ] as [string, Record<string, unknown>][];

  return (
    <div className="fixed inset-0 z-40 flex">
      <div className="flex-1" onClick={onClose} />
      <div className="w-full max-w-2xl bg-background border-l border-border overflow-y-auto flex flex-col">
        <div className="flex items-start justify-between gap-4 p-4 sm:p-6 border-b border-border sticky top-0 bg-background z-10">
          <div>
            <h2 className="font-bold text-lg">{detail.full_name}</h2>
            <p className="text-xs text-muted-foreground">{detail.role_title || "—"} · {detail.party || "—"}</p>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground text-xl transition-colors">✕</button>
        </div>

        <div className="p-4 sm:p-6 space-y-6">
          <div className="flex gap-2 flex-wrap items-center">
            <StatusBadge status={detail.pidaa_status} />
            {detail.built_at && <span className="text-xs text-muted-foreground">{new Date(detail.built_at).toLocaleString()}</span>}
            <span className="text-xs text-muted-foreground">@{detail.username}</span>
          </div>

          {id.coverage_gaps.length > 0 && (
            <div>
              <SectionTitle title="Coverage Gaps" />
              <div className="flex flex-wrap gap-1.5">
                {id.coverage_gaps.map((g, i) => (
                  <span key={i} className="text-[10px] uppercase tracking-widest border border-border text-muted-foreground px-2 py-1">{g}</span>
                ))}
              </div>
            </div>
          )}

          {sections.map(([title, data]) => (
            <div key={title} className="border border-border p-4">
              <SectionTitle title={title} />
              <JsonBlock data={data} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// --- Disambiguation card -----------------------------------------------------

function CandidateCard({
  candidate,
  onConfirm,
  onRetry,
}: {
  candidate: IdentityCandidate;
  onConfirm: () => void;
  onRetry: (hint: string) => void;
}) {
  const [hint, setHint] = useState("");
  const [imageFailed, setImageFailed] = useState(false);
  const confidence = Math.round(candidate.confidence * 100);

  return (
    <div className="w-full max-w-2xl border border-border bg-background p-3 sm:p-4 space-y-4">
      <div className="flex items-start gap-4">
        {candidate.photo_url && !imageFailed ? (
          <img
            src={candidate.photo_url}
            alt={`Profile of ${candidate.full_name}`}
            onError={() => setImageFailed(true)}
            className="h-28 w-24 shrink-0 object-cover border border-border"
          />
        ) : (
          <div className="flex h-28 w-24 shrink-0 items-center justify-center border border-border bg-muted text-2xl text-muted-foreground" aria-label="Portrait unavailable">{candidate.full_name.slice(0, 1)}</div>
        )}
        <div className="min-w-0 flex-1 space-y-1">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Highest-ranked identity match · {confidence}% confidence</p>
          <h3 className="font-bold text-lg">{candidate.full_name}</h3>
          {candidate.aliases.length > 0 && (
            <p className="text-xs text-muted-foreground">Also known as: {candidate.aliases.join(", ")}</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 text-sm min-[420px]:grid-cols-2">
        {[
          ["Role", candidate.current_role],
          ["Party", candidate.party],
          ["Region", candidate.region],
          ["Born", candidate.born ? `${candidate.born} · ${candidate.birthplace || ""}` : candidate.birthplace],
        ].filter(([, v]) => v).map(([k, v]) => (
          <div key={k as string}>
            <p className="text-xs text-muted-foreground">{k as string}</p>
            <p>{v as string}</p>
          </div>
        ))}
      </div>

      {candidate.one_line_bio && (
        <p className="text-sm text-muted-foreground italic">{candidate.one_line_bio}</p>
      )}

      <div className="flex gap-1.5 flex-wrap">
        {candidate.top_sources.map((s, i) => (
          <a key={i} href={s.url} target="_blank" rel="noopener noreferrer"
            className="candidate-source text-xs px-2 py-1 transition-colors">
            {s.domain}
          </a>
        ))}
      </div>

      {candidate.ambiguity_notes && (
        <p className="text-xs bg-muted/60 text-foreground p-2">{candidate.ambiguity_notes}</p>
      )}

      <div className="flex flex-col sm:flex-row gap-3 pt-2">
        <button
          onClick={onConfirm}
            className="min-h-11 w-full sm:w-36 px-3 py-2 bg-foreground text-background text-sm font-medium border border-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          Confirm
        </button>
        <div className="flex gap-2 flex-1 min-w-0">
          <input
            type="text"
            value={hint}
            onChange={(e) => setHint(e.target.value)}
            placeholder="Add hint…"
            className="min-h-11 min-w-0 flex-1 px-3 py-2 border border-border bg-background text-foreground text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-foreground"
          />
          <button
            onClick={() => onRetry(hint)}
            className="min-h-11 px-4 py-2 border border-border text-sm hover:bg-muted transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    </div>
  );
}

// --- Main console ------------------------------------------------------------

export default function AdminConsole() {
  const router = useRouter();
  const [identities, setIdentities] = useState<PrincipalSummary[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [registryError, setRegistryError] = useState("");

  // Create flow
  const [nameQuery, setNameQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [candidate, setCandidate] = useState<IdentityCandidate | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [newCreds, setNewCreds] = useState<CreatePrincipalOut["credentials"] | null>(null);
  const [createError, setCreateError] = useState("");

  const guardAdmin = useCallback(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  const loadPrincipals = useCallback(async () => {
    try {
      const list = await api.listPrincipals();
      setIdentities(list);
      setRegistryError("");
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        router.replace("/login");
        return;
      }
      setRegistryError("Identity registry is temporarily unavailable. Your session remains active.");
    } finally {
      setLoadingList(false);
    }
  }, [router]);

  useEffect(() => {
    guardAdmin();
    loadPrincipals();
  }, [guardAdmin, loadPrincipals]);

  const handleSearch = async (e: React.FormEvent, hint?: string) => {
    e?.preventDefault();
    if (!nameQuery.trim()) return;
    setSearching(true);
    setCandidate(null);
    setCreateError("");
    try {
      const c = await api.disambiguatePrincipal(nameQuery.trim(), hint);
      setCandidate(c);
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setSearching(false);
    }
  };

  const handleConfirm = async () => {
    if (!candidate) return;
    setConfirming(true);
    setCreateError("");
    try {
      const result = await api.createPrincipal(nameQuery, candidate);
      setNewCreds(result.credentials);
      setCandidate(null);
      setNameQuery("");
      loadPrincipals();
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Creation failed");
    } finally {
      setConfirming(false);
    }
  };

  const handleRerun = async (profileId: string) => {
    try {
      await api.rerunPidaa(profileId);
      await loadPrincipals();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Rerun failed");
    }
  };

  const handleArchive = async (profileId: string, name: string) => {
    if (!confirm(`Archive ${name}? This cannot be undone.`)) return;
    try {
      await api.archivePrincipal(profileId);
      await loadPrincipals();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Archive failed");
    }
  };

  const handleViewDetail = (profileId: string) => {
    router.push(`/identity?profileId=${encodeURIComponent(profileId)}`);
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {newCreds && <CredentialsModal creds={newCreds} onDismiss={() => setNewCreds(null)} />}

      <div className="max-w-6xl mx-auto px-3 py-6 sm:px-5 sm:py-10 space-y-8 sm:space-y-12">

        {/* Create principal */}
        <section className="w-full max-w-3xl space-y-4">
          <h2 className="text-xs font-semibold tracking-[0.2em] uppercase text-muted-foreground">Add New Identity</h2>

          <form onSubmit={handleSearch} className="flex max-w-2xl flex-col sm:flex-row gap-2">
            <input
              type="text"
              placeholder="Full name (e.g. Sara Duterte)"
              value={nameQuery}
              onChange={(e) => setNameQuery(e.target.value)}
              className="flex-1 px-3 py-2 border border-border bg-background text-foreground text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-foreground"
              disabled={searching || confirming}
            />
            <button
              type="submit"
              className="min-h-11 w-full sm:w-auto px-5 py-2 bg-foreground text-background text-sm font-medium border border-foreground hover:bg-muted hover:text-foreground transition-colors disabled:opacity-50 shrink-0"
              disabled={searching || !nameQuery.trim() || confirming}
            >
              {searching ? (
                <ScrambleLoader target="IDENTIFING" label="Identifying identity" className="text-[11px]" />
              ) : "Search"}
            </button>
          </form>

          <p className="max-w-2xl text-xs leading-relaxed text-muted-foreground">
            PIDAA — Person Identity Deep Analyzer Agent: Builds detailed identity dossiers for confirmed political figures.
          </p>

          {createError && <p className="text-sm text-red-600 dark:text-red-400">{createError}</p>}

          {candidate && (
            <CandidateCard
              candidate={candidate}
              onConfirm={handleConfirm}
              onRetry={(hint) => handleSearch(new Event("submit") as unknown as React.FormEvent, hint)}
            />
          )}
          {confirming && (
            <p className="flex items-center gap-2 text-sm text-muted-foreground"><ScrambleLoader target="ANALYZING" label="PIDAA is analyzing identity" className="text-[10px]" /> Creating identity profile…</p>
          )}
        </section>

        {/* Identity gallery */}
        <section className="space-y-4">
          <h2 className="text-xs font-semibold tracking-[0.2em] uppercase text-muted-foreground border-b border-border pb-3">
            Identity Registry ({identities.length})
          </h2>

          {loadingList ? (
            <p className="text-sm text-muted-foreground">Loading identity registry…</p>
          ) : identities.length === 0 ? (
            <p className="text-sm text-muted-foreground">No identities have been registered.</p>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {identities.map((identity) => (
                <article key={identity.profile_id} className="overflow-hidden border border-border bg-background">
                  <div className="relative aspect-[4/3] bg-muted">
                    {identity.profile_image_url ? (
                      <img src={identity.profile_image_url} alt={`Profile of ${identity.full_name}`} className="h-full w-full object-cover" />
                    ) : (
                      <div className="flex h-full items-center justify-center text-5xl font-bold text-muted-foreground/40" aria-hidden="true">
                        {identity.full_name.slice(0, 1)}
                      </div>
                    )}
                    <div className="absolute left-3 top-3"><StatusBadge status={identity.pidaa_status} /></div>
                  </div>
                  <div className="space-y-3 p-4">
                    <div>
                      <h3 className="font-semibold">{identity.full_name}</h3>
                      <p className="text-xs text-muted-foreground">{identity.role_title || "Role pending verification"}</p>
                    </div>
                    <p className="min-h-10 text-sm text-muted-foreground line-clamp-2">
                      {identity.overview || identity.party || "Identity dossier is awaiting analysis."}
                    </p>
                    <div className="flex items-center justify-between border-y border-border py-2 text-[10px] uppercase tracking-widest text-muted-foreground">
                      <span>{identity.built_at ? new Date(identity.built_at).toLocaleDateString() : "Not built"}</span>
                      <span>{identity.party || "Unaligned"}</span>
                    </div>
                    <div className="grid grid-cols-1 gap-2 min-[420px]:grid-cols-2 sm:flex">
                      <button onClick={() => handleViewDetail(identity.profile_id)} className="min-h-11 border border-foreground bg-foreground px-3 py-2 text-xs font-medium text-background hover:opacity-90 min-[420px]:col-span-2 sm:flex-1">View full</button>
                      <button onClick={() => handleRerun(identity.profile_id)} className="min-h-11 border border-border px-3 py-2 text-xs hover:bg-muted sm:shrink-0">Rerun PIDAA</button>
                      <button onClick={() => handleArchive(identity.profile_id, identity.full_name)} className="min-h-11 border border-red-600 px-3 py-2 text-xs text-red-700 hover:bg-red-500/10 sm:shrink-0">Archive</button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
          {registryError && <p className="text-sm text-red-700">{registryError}</p>}
        </section>
      </div>
    </div>
  );
}
