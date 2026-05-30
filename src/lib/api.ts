// Lightweight API client for the Parallax Politics backend.
// Configure base URL via NEXT_PUBLIC_API_BASE (defaults to localhost:8000).

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

const TOKEN_KEY = "parallax.token";
const SA_TOKEN_KEY = "parallax.superadmin.token";

function setCookie(name: string, value: string, days = 7) {
  if (typeof window === "undefined") return;
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)};expires=${expires};path=/`;
}
function getCookie(name: string): string | null {
  if (typeof window === "undefined") return null;
  const m = document.cookie.match(new RegExp("(?:^|; )" + name.replace(/([$?*|{}\\^+[\]])/g, "\\$1") + "=([^;]*)"));
  return m ? decodeURIComponent(m[1]) : null;
}
function clearCookie(name: string) {
  if (typeof window === "undefined") return;
  document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
}

export function setToken(token: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_KEY, token);
    setCookie(TOKEN_KEY, token);
  }
}
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}
export function clearToken() {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
    clearCookie(TOKEN_KEY);
  }
}

export function setSAToken(token: string) {
  if (typeof window !== "undefined") localStorage.setItem(SA_TOKEN_KEY, token);
}
export function getSAToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(SA_TOKEN_KEY);
}
export function clearSAToken() {
  if (typeof window !== "undefined") localStorage.removeItem(SA_TOKEN_KEY);
}

async function request<T>(
  path: string,
  init: RequestInit & { auth?: boolean; saAuth?: boolean } = {}
): Promise<T> {
  const { auth = true, saAuth = false, headers, ...rest } = init;
  const h = new Headers(headers);
  h.set("Content-Type", "application/json");
  if (saAuth) {
    const tok = getSAToken();
    if (tok) h.set("Authorization", `Bearer ${tok}`);
  } else if (auth) {
    const tok = getToken();
    if (tok) h.set("Authorization", `Bearer ${tok}`);
  }
  const res = await fetch(`${API_BASE}${path}`, { ...rest, headers: h });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return (await res.json()) as T;
}

// --- Types ------------------------------------------------------------------

export type UserOut = {
  id: string;
  username: string;
  display_name: string | null;
  role: string;
  access_code: string | null;
  has_profile: boolean;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  user: UserOut;
};

export type SocialLinks = {
  linkedin?: string;
  facebook?: string;
  instagram?: string;
  x?: string;
  youtube?: string;
};

export type UserProfileOut = {
  full_name: string;
  country: string;
  age: number;
  birthdate: string;
  social_links: SocialLinks;
};

export type SourceItem = {
  url: string;
  title: string | null;
  domain: string;
  published_at: string | null;
  excerpt: string | null;
  credibility_score: number;
};

export type SourcePack = {
  query: string;
  sources: SourceItem[];
  coverage_gaps: string[];
};

export type DomainBriefing = {
  relevant_concepts: string[];
  institutional_constraints: string[];
  precedent_cases: string[];
  risk_flags: string[];
  notes: string | null;
};

export type DemographicCohort = {
  name: string;
  share_pct: number | null;
  salient_issues: string[];
  media_mix: Record<string, number>;
};

export type DemographicBriefing = {
  region: string;
  cohorts: DemographicCohort[];
  notes: string | null;
};

export type PrincipalIdentityArtifact = {
  full_name: string;
  basics: Record<string, unknown>;
  family: Record<string, unknown>;
  education: Record<string, unknown>;
  career_timeline: Record<string, unknown>;
  current_position: Record<string, unknown>;
  party_history: Record<string, unknown>;
  electoral_record: Record<string, unknown>;
  policy_stances: Record<string, unknown>;
  voice_signature: Record<string, unknown>;
  controversies: Record<string, unknown>;
  network: Record<string, unknown>;
  source_index: Record<string, unknown>;
  coverage_gaps: string[];
};

export type PrincipalOut = {
  id: string;
  slug: string;
  full_name: string;
  role_title: string | null;
  party: string | null;
  pack_id: string;
  identity: Record<string, unknown>;
  career: Record<string, unknown>;
  stances: Record<string, unknown>;
  voice_patterns: Record<string, unknown>;
  vulnerabilities: Record<string, unknown>;
  allies_rivals: Record<string, unknown>;
  media_footprint: Record<string, unknown>;
};

export type RunArtifacts = {
  source_pack: SourcePack | null;
  domain_briefing: DomainBriefing | null;
  demographic_briefing: DemographicBriefing | null;
  principal_identity: PrincipalIdentityArtifact | null;
};

export type RunStatus = "queued" | "running" | "completed" | "failed" | "budget_exhausted";

export type RunOut = {
  id: string;
  status: RunStatus;
  run_kind: string;
  situation_prompt: string;
  total_cost_usd: number;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  error: string | null;
  artifacts: RunArtifacts;
  principal: PrincipalOut | null;
};

// --- Brief types ------------------------------------------------------------

export type TopicStance = "lead" | "engage" | "avoid";

export type TopRisk = {
  label: string;
  severity: number;
  summary: string;
  time_horizon: string;
};

export type TopOpportunity = {
  label: string;
  magnitude: number;
  summary: string;
  time_horizon: string;
};

export type BriefTopic = {
  topic: string;
  stance: TopicStance;
  rationale: string;
  angle: string | null;
};

export type BriefActionCard = {
  what: string;
  who: string;
  where: string;
  when: string;
  how: string;
  proof: string;
  avoid: string;
  confidence: number;
  success_kpis: string[];
};

export type BriefSource = {
  url: string;
  title: string | null;
  domain: string | null;
  published_at: string | null;
  credibility_score: number;
  used_for: string[];
};

export type BriefSummary = {
  id: string;
  created_at: string;
  top_risk_label: string;
  top_opportunity_label: string;
  action_what: string;
  confidence: number;
  cost_usd: number;
};

export type BriefOut = {
  id: string;
  profile_id: string;
  run_id: string | null;
  created_at: string;
  top_risk: TopRisk;
  top_opportunity: TopOpportunity;
  topics: BriefTopic[];
  action_card: BriefActionCard;
  reasoning: string;
  sources: BriefSource[];
  model: string | null;
  cost_usd: number;
  confidence: number;
};

export type BriefGenerateOut = {
  run_id: string;
  status: string;
};

export type MyIdentityOut = {
  profile_id: string;
  full_name: string;
  role_title: string | null;
  party: string | null;
  pack_id: string;
  pidaa_status: string;
  built_at: string | null;
  identity: PrincipalIdentitySection | null;
};

export type IdentityCandidate = {
  full_name: string;
  aliases: string[];
  current_role: string | null;
  party: string | null;
  region: string | null;
  born: string | null;
  birthplace: string | null;
  photo_url: string | null;
  one_line_bio: string | null;
  top_sources: { url: string; title: string; domain: string }[];
  confidence: number;
  ambiguity_notes: string | null;
};

export type PrincipalIdentitySection = {
  basics: Record<string, unknown>;
  family: Record<string, unknown>;
  education: Record<string, unknown>;
  career_timeline: Record<string, unknown>;
  current_position: Record<string, unknown>;
  party_history: Record<string, unknown>;
  electoral_record: Record<string, unknown>;
  policy_stances: Record<string, unknown>;
  voice_signature: Record<string, unknown>;
  controversies: Record<string, unknown>;
  network: Record<string, unknown>;
  source_index: Record<string, unknown>;
  coverage_gaps: string[];
};

export type PrincipalSummary = {
  profile_id: string;
  identity_id: string;
  full_name: string;
  role_title: string | null;
  party: string | null;
  pack_id: string;
  pidaa_status: string;
  built_at: string | null;
  username: string;
};

export type PrincipalDetail = PrincipalSummary & {
  identity: PrincipalIdentitySection;
};

export type CreatePrincipalOut = {
  profile_id: string;
  identity_id: string;
  run_id: string;
  credentials: { username: string; password: string };
};

// --- Endpoints --------------------------------------------------------------

export const api = {
  async login(username: string, password: string): Promise<LoginResponse> {
    return request<LoginResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
      auth: false,
    });
  },
  async getMe(): Promise<UserOut> {
    return request<UserOut>("/api/v1/auth/me");
  },
  async getRun(id: string): Promise<RunOut> {
    return request<RunOut>(`/api/v1/runs/${id}`);
  },

  // --- Brief ---
  async generateBrief(): Promise<BriefGenerateOut> {
    return request<BriefGenerateOut>("/api/v1/briefs", { method: "POST" });
  },
  async listBriefs(): Promise<BriefSummary[]> {
    return request<BriefSummary[]>("/api/v1/briefs");
  },
  async getBrief(id: string): Promise<BriefOut> {
    return request<BriefOut>(`/api/v1/briefs/${id}`);
  },
  async getLatestBrief(): Promise<BriefOut> {
    return request<BriefOut>("/api/v1/briefs/latest");
  },
  async getMyIdentity(): Promise<MyIdentityOut> {
    return request<MyIdentityOut>("/api/v1/briefs/me/identity");
  },

  openRunEvents(runId: string): EventSource {
    const token = getToken() ?? "";
    const url = `${API_BASE}/api/v1/runs/${runId}/events?token=${encodeURIComponent(token)}`;
    return new EventSource(url);
  },

  // --- Superadmin ---
  async verifySuperadmin(code: string): Promise<{ token: string }> {
    return request<{ token: string }>("/api/v1/superadmin/verify", {
      method: "POST",
      body: JSON.stringify({ code }),
      auth: false,
    });
  },
  async disambiguatePrincipal(name_query: string, hint?: string): Promise<IdentityCandidate> {
    return request<IdentityCandidate>("/api/v1/superadmin/disambiguate", {
      method: "POST",
      body: JSON.stringify({ name_query, hint: hint || null }),
      saAuth: true,
    });
  },
  async createPrincipal(name_query: string, candidate: IdentityCandidate): Promise<CreatePrincipalOut> {
    return request<CreatePrincipalOut>("/api/v1/superadmin/principals", {
      method: "POST",
      body: JSON.stringify({ name_query, candidate }),
      saAuth: true,
    });
  },
  async listPrincipals(): Promise<PrincipalSummary[]> {
    return request<PrincipalSummary[]>("/api/v1/superadmin/principals", { saAuth: true });
  },
  async getPrincipalDetail(profileId: string): Promise<PrincipalDetail> {
    return request<PrincipalDetail>(`/api/v1/superadmin/principals/${profileId}`, { saAuth: true });
  },
  async rerunPidaa(profileId: string): Promise<{ run_id: string; status: string }> {
    return request<{ run_id: string; status: string }>(`/api/v1/superadmin/principals/${profileId}/rerun`, {
      method: "POST",
      saAuth: true,
    });
  },
  async archivePrincipal(profileId: string): Promise<void> {
    return request<void>(`/api/v1/superadmin/principals/${profileId}`, {
      method: "DELETE",
      saAuth: true,
    });
  },
};

// --- SSE helper -------------------------------------------------------------
// EventSource cannot send Authorization headers, so the backend SSE endpoint
// also accepts the token via query string fallback (TODO: add server-side
// support). For now we poll getRun() while showing in-progress events from
// a manual fetch-stream reader.

export async function* streamRunEvents(
  runId: string,
  signal?: AbortSignal
): AsyncGenerator<{ type: string; [k: string]: unknown }> {
  const tok = getToken();
  const res = await fetch(`${API_BASE}/api/v1/runs/${runId}/events`, {
    headers: tok ? { Authorization: `Bearer ${tok}` } : {},
    signal,
  });
  if (!res.body) return;
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    // SSE messages are separated by "\n\n"
    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const chunk = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const dataLine = chunk
        .split("\n")
        .find((l) => l.startsWith("data:"));
      if (!dataLine) continue;
      try {
        const payload = JSON.parse(dataLine.slice(5).trim());
        yield payload;
      } catch {
        // ignore malformed
      }
    }
  }
}
