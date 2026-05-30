"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  api,
  clearSAToken,
  getSAToken,
  IdentityCandidate,
  PrincipalDetail,
  PrincipalSummary,
  CreatePrincipalOut,
} from "@/lib/api";

// --- small helpers -----------------------------------------------------------

function StatusBadge({ status }: { status: string }) {
  const color =
    status === "ready" ? "text-green-500 border-green-500" :
    status === "building" ? "text-yellow-500 border-yellow-500" :
    status === "failed" ? "text-red-500 border-red-500" :
    "text-muted-foreground border-border";
  return (
    <span className={`text-xs border px-2 py-0.5 ${color}`}>{status}</span>
  );
}

function Tag({ label }: { label: string }) {
  return <span className="text-xs border border-border px-2 py-0.5 text-muted-foreground">{label}</span>;
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
        <div className="flex gap-3">
          <button
            onClick={copy}
            className="flex-1 px-4 py-2 border border-border text-sm hover:bg-border transition-colors"
          >
            {copied ? "Copied ✓" : "Copy"}
          </button>
          <button
            onClick={onDismiss}
            className="flex-1 px-4 py-2 bg-foreground text-background text-sm font-medium hover:opacity-90 transition-opacity"
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
        <div className="flex items-center justify-between p-6 border-b border-border sticky top-0 bg-background z-10">
          <div>
            <h2 className="font-bold text-lg">{detail.full_name}</h2>
            <p className="text-xs text-muted-foreground">{detail.role_title || "—"} · {detail.party || "—"}</p>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground text-xl">✕</button>
        </div>

        <div className="p-6 space-y-6">
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
                  <span key={i} className="text-xs border border-yellow-600 text-yellow-600 px-2 py-0.5">{g}</span>
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
  nameQuery,
}: {
  candidate: IdentityCandidate;
  onConfirm: () => void;
  onRetry: (hint: string) => void;
  nameQuery: string;
}) {
  const [hint, setHint] = useState("");
  const confidence = Math.round(candidate.confidence * 100);

  return (
    <div className="border border-border p-6 space-y-4">
      <div className="flex justify-between items-start gap-4">
        <div className="space-y-1">
          <h3 className="font-bold text-lg">{candidate.full_name}</h3>
          {candidate.aliases.length > 0 && (
            <p className="text-xs text-muted-foreground">Also known as: {candidate.aliases.join(", ")}</p>
          )}
        </div>
        {candidate.photo_url && (
          <img src={candidate.photo_url} alt="" className="w-16 h-16 object-cover border border-border shrink-0" />
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
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
            className="text-xs border border-border px-2 py-0.5 hover:border-foreground transition-colors">
            {s.domain}
          </a>
        ))}
      </div>

      {candidate.ambiguity_notes && (
        <p className="text-xs border border-yellow-600 text-yellow-600 p-2">{candidate.ambiguity_notes}</p>
      )}

      <p className="text-xs text-muted-foreground">Confidence: {confidence}%</p>

      <div className="flex gap-3 pt-2">
        <button
          onClick={onConfirm}
          className="flex-1 px-4 py-2 bg-foreground text-background text-sm font-medium hover:opacity-90 transition-opacity"
        >
          Confirm — this is the principal
        </button>
        <div className="flex gap-2 flex-1">
          <input
            type="text"
            value={hint}
            onChange={(e) => setHint(e.target.value)}
            placeholder="Add hint…"
            className="flex-1 px-3 py-2 border border-border bg-background text-foreground text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-foreground"
          />
          <button
            onClick={() => onRetry(hint)}
            className="px-3 py-2 border border-border text-sm hover:bg-border transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    </div>
  );
}

// --- Main console ------------------------------------------------------------

export default function SuperadminConsole() {
  const router = useRouter();
  const [principals, setPrincipals] = useState<PrincipalSummary[]>([]);
  const [loadingList, setLoadingList] = useState(true);

  // Create flow
  const [nameQuery, setNameQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [candidate, setCandidate] = useState<IdentityCandidate | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [newCreds, setNewCreds] = useState<CreatePrincipalOut["credentials"] | null>(null);
  const [createError, setCreateError] = useState("");

  // Detail drawer
  const [detail, setDetail] = useState<PrincipalDetail | null>(null);

  const guardSA = useCallback(() => {
    if (!getSAToken()) router.replace("/superadmin/enter");
  }, [router]);

  const loadPrincipals = useCallback(async () => {
    try {
      const list = await api.listPrincipals();
      setPrincipals(list);
    } catch {
      router.replace("/superadmin/enter");
    } finally {
      setLoadingList(false);
    }
  }, [router]);

  useEffect(() => {
    guardSA();
    loadPrincipals();
  }, [guardSA, loadPrincipals]);

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

  const handleViewDetail = async (profileId: string) => {
    try {
      const d = await api.getPrincipalDetail(profileId);
      setDetail(d);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to load detail");
    }
  };

  const handleSignOut = () => {
    clearSAToken();
    router.push("/");
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {newCreds && <CredentialsModal creds={newCreds} onDismiss={() => setNewCreds(null)} />}
      {detail && <IdentityDrawer detail={detail} onClose={() => setDetail(null)} />}

      {/* Top bar */}
      <div className="border-b border-border px-6 py-4 flex items-center justify-between sticky top-0 bg-background z-30">
        <div className="flex items-center gap-3">
          <span className="font-bold tracking-tight">Parallax</span>
          <span className="text-xs text-muted-foreground border border-border px-2 py-0.5">Superadmin</span>
          <span className="text-xs text-muted-foreground">Philippines POC</span>
        </div>
        <button onClick={handleSignOut} className="text-xs text-muted-foreground hover:text-foreground transition-colors">
          Sign out
        </button>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-10 space-y-12">

        {/* Create principal */}
        <section className="space-y-4">
          <h2 className="text-xs font-semibold tracking-widest uppercase text-muted-foreground">Create New Principal</h2>

          <form onSubmit={handleSearch} className="flex gap-3">
            <input
              type="text"
              placeholder="Full name (e.g. Sara Duterte)"
              value={nameQuery}
              onChange={(e) => setNameQuery(e.target.value)}
              className="flex-1 px-4 py-3 border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-foreground"
              disabled={searching || confirming}
            />
            <button
              type="submit"
              className="px-6 py-3 bg-foreground text-background font-medium hover:opacity-90 transition-opacity disabled:opacity-50 shrink-0"
              disabled={searching || !nameQuery.trim() || confirming}
            >
              {searching ? "Searching…" : "Search"}
            </button>
          </form>

          {createError && <p className="text-sm text-red-600 dark:text-red-400">{createError}</p>}

          {candidate && (
            <CandidateCard
              candidate={candidate}
              nameQuery={nameQuery}
              onConfirm={handleConfirm}
              onRetry={(hint) => handleSearch(new Event("submit") as unknown as React.FormEvent, hint)}
            />
          )}
          {confirming && (
            <p className="text-sm text-muted-foreground">Creating principal and queuing PIDAA build…</p>
          )}
        </section>

        {/* Principals list */}
        <section className="space-y-4">
          <h2 className="text-xs font-semibold tracking-widest uppercase text-muted-foreground">
            Principals ({principals.length})
          </h2>

          {loadingList ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : principals.length === 0 ? (
            <p className="text-sm text-muted-foreground">No principals yet.</p>
          ) : (
            <div className="space-y-2">
              {principals.map((p) => (
                <div key={p.profile_id} className="border border-border p-4 flex items-center gap-4 flex-wrap">
                  <div className="flex-1 min-w-0 space-y-0.5">
                    <p className="font-medium">{p.full_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {p.role_title || "—"} · {p.party || "—"} · @{p.username}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0 flex-wrap">
                    <StatusBadge status={p.pidaa_status} />
                    {p.built_at && (
                      <span className="text-xs text-muted-foreground hidden sm:inline">
                        {new Date(p.built_at).toLocaleDateString()}
                      </span>
                    )}
                    <button
                      onClick={() => handleViewDetail(p.profile_id)}
                      className="text-xs border border-border px-3 py-1 hover:bg-border transition-colors"
                    >
                      View
                    </button>
                    <button
                      onClick={() => handleRerun(p.profile_id)}
                      className="text-xs border border-border px-3 py-1 hover:bg-border transition-colors"
                    >
                      Rerun PIDAA
                    </button>
                    <button
                      onClick={() => handleArchive(p.profile_id, p.full_name)}
                      className="text-xs border border-red-500 text-red-500 px-3 py-1 hover:bg-red-500 hover:text-background transition-colors"
                    >
                      Archive
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
