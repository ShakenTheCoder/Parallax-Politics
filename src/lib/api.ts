// Lightweight API client for the Parallax Politics backend.
// All browser traffic passes through the same-origin Next.js backend-for-frontend.
// The bearer token is held only in an HttpOnly cookie and never exposed to JS.
export const API_BASE = "/api/backend";

const SESSION_MARKER_KEY = "parallax.session";

export function isAdminRole(role: string | null | undefined): boolean {
  return role === "superadmin";
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

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return getCookie(SESSION_MARKER_KEY);
}
export function clearToken() {
  if (typeof window !== "undefined") {
    clearCookie(SESSION_MARKER_KEY);
  }
}

async function request<T>(
  path: string,
  init: RequestInit & { auth?: boolean; saAuth?: boolean } = {}
): Promise<T> {
  const { headers } = init;
  const rest = { ...init };
  delete rest.headers;
  delete rest.auth;
  delete rest.saAuth;
  const h = new Headers(headers);
  h.set("Content-Type", "application/json");
  const backendPath = path.startsWith("/api/v1/") ? path.slice("/api/v1".length) : path;
  const url = path.startsWith("/api/session/") ? path : `${API_BASE}${backendPath}`;
  const res = await fetch(url, { ...rest, headers: h, credentials: "same-origin", cache: "no-store" });
  if (!res.ok) {
    const text = await res.text();
    throw new ApiError(res.status, `${res.status} ${res.statusText}: ${text}`);
  }
  if (res.status === 204) return undefined as T;

  const body = await res.text();
  return (body ? JSON.parse(body) : undefined) as T;
}

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

// --- Types ------------------------------------------------------------------

export type UserOut = {
  id: string;
  username: string;
  display_name: string | null;
  role: string;
  has_profile: boolean;
};

export type UserRole = "principal" | "superadmin";

export type AdminUser = UserOut & {
  created_at: string;
  role: UserRole;
};

export type AdminUserCreate = {
  username: string;
  password: string;
  display_name?: string;
  role: UserRole;
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
  profile_image_url: string | null;
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
  command_view?: CommandView | null;
};

export type BriefGenerateOut = {
  run_id: string;
  status: string;
};

export type BriefActiveOut = {
  run_id: string | null;
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
  profile_image_url: string | null;
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
  profile_image_url: string | null;
  overview: string | null;
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

export type PoliticalFigureSummary = {
  id: string;
  slug: string;
  canonical_name: string;
  aliases: string[];
  category: string;
  current_role: string | null;
  office: string | null;
  party: string | null;
  region: string | null;
  status: string;
  portrait_url: string | null;
  confidence: number;
  last_verified_at: string | null;
  coverage_gaps: string[];
  social_platforms: string[];
};

export type PoliticalFigureDetail = PoliticalFigureSummary & {
  jurisdiction: string | null;
  faction: string | null;
  portrait_source_url: string | null;
  portrait_attribution: string | null;
  data: Record<string, unknown>;
  social_accounts: { platform: string; url: string; handle?: string | null; account_type: string; verification: string }[];
  relationships: Record<string, unknown>[];
  source_ledger: { url: string; title?: string | null; publisher?: string | null; supports: string[]; confidence: number; accessed_at?: string | null }[];
  snapshot_count: number;
};

// --- Audience Center Types ---

export type PersonalAudienceInstructions = {
  target_name: string;
  aliases: string[];
  focus_keywords: string[];
  priority_topics: string[];
  extraction_fields: string[];
  instructions_summary: string;
};

export type CompetitorsAudienceInstructions = {
  primary_competitors: string[];
  competitor_keywords: string[];
  topics_of_contention: string[];
  tracking_priorities: string[];
  instructions_summary: string;
};

export type ContextualAudienceInstructions = {
  target_regions: string[];
  demographic_segments: string[];
  salient_issues: string[];
  instructions_summary: string;
};

export type FacebookAnalysisCategoryResult = {
  category_name: string;
  sentiment_distribution: Record<string, number>;
  top_themes: string[];
  engagement_metrics: Record<string, number>;
  key_findings: string[];
};

export type FacebookAnalysisResult = {
  categories: FacebookAnalysisCategoryResult[];
  overall_landscape_summary: string;
  actionable_recommendations: string[];
};

export type AudienceInstructionsSummary = {
  personal: PersonalAudienceInstructions | null;
  competitors: CompetitorsAudienceInstructions | null;
  contextual: ContextualAudienceInstructions | null;
  facebook_analysis: FacebookAnalysisResult | null;
  last_updated_at: string | null;
};

// --- Intelligence control plane ---

export type IntelligenceSignal = {
  id: string;
  subject_id: string | null;
  platform: string;
  event_type: string;
  language: string;
  title: string | null;
  content_excerpt: string;
  url: string;
  published_at: string | null;
  observed_at: string;
  engagement: Record<string, number>;
  provenance: Record<string, unknown>;
};

export type PresenceMetric = {
  subject_id: string;
  full_name: string;
  signal_count: number;
  engagement_total: number;
  share_of_voice_pct: number;
  latest_signal_at: string | null;
};

export type IntelligenceOverview = {
  generated_at: string;
  freshness_minutes: number | null;
  monitored_candidates: number;
  signals_24h: number;
  sources_active: number;
  scenarios_pending_review: number;
  presence: PresenceMetric[];
  recent_signals: IntelligenceSignal[];
  data_notice: string;
  election?: Record<string, unknown> | null;
  command_view?: CommandView | null;
  momentum?: Record<string, unknown> | null;
  coverage?: CoverageReport | null;
  latest_poll?: PollRecord | null;
};

export type CommandMetricTile = {
  key: string;
  label: string;
  value: string;
  delta: string;
  evidence_ids: string[];
};

export type CommandView = {
  subject: string;
  watch_status: string;
  score: number | null;
  previous_score: number | null;
  delta: number | null;
  rank: number | null;
  rank_suppressed: boolean;
  coverage_confidence: number;
  freshness_minutes: number | null;
  model_version: string;
  headline: string;
  tiles: CommandMetricTile[];
  opportunity: string;
  risk: string;
  next_move: string;
  next_move_reviewed: boolean;
  coverage_note: string;
};

export type BriefImportance = "critical" | "high" | "medium" | "low" | "unrated";

export type ThirtySecondBrief = {
  identity: {
    name: string;
    position: string | null;
    portrait_url: string | null;
  };
  score: {
    value: number | null;
    delta: number | null;
    updated_at: string | null;
  };
  watchlist: {
    is_principal: boolean;
    rank: number | null;
    name: string;
    position: string | null;
    portrait_url: string | null;
    score: number | null;
    delta: number | null;
  }[];
  appearances_window_hours: number;
  appearances: {
    id: string;
    caption: string;
    source_name: string;
    source_url: string;
    appeared_at: string;
  }[];
  latest_opinion: {
    id: string;
    summary: string;
    importance: BriefImportance;
    generated_at: string;
    source_count: number;
  } | null;
  previous_opinions: {
    id: string;
    summary: string;
    importance: BriefImportance;
    generated_at: string;
    source_count: number;
  }[];
  data_status: "live" | "partial" | "unavailable";
  notice: string;
};

export type PollRecord = {
  pollster: string;
  published_at?: string;
  field_dates: string;
  sample: number;
  population?: string;
  mode?: string;
  margin_of_error: string;
  question?: string;
  source_url?: string;
  layer?: string;
  results?: { name: string; value: number }[];
};

export type CoverageReport = {
  confidence: number;
  threshold?: number;
  rank_suppressed: boolean;
  families?: { name: string; status: string; score: number; freshness: string | null; action: string }[];
  missing_sources: string[];
};

export type AnalysisCenter = {
  snapshot: { effective_at: string; mode: string; notice: string; model_version: string; [key: string]: unknown };
  election: { label: string; date: string; official_calendar_status: string; watchlist_label: string };
  command_view: CommandView;
  momentum_components: { key: string; label: string; weight: number; score: number; delta: number }[];
  timeline: { date: string; values: Record<string, number> }[];
  watchlist: { slug: string; name: string; office: string; poll: number; strongest_channel: string; issue: string; watch_status: string; rank: number | null; momentum: number; movement: number; earned_visibility: number; cadence: string }[];
  channels: { name: string; score: number | null; coverage: number; comparison: string }[];
  narratives: { name: string; stage: string; velocity: number; owner: string; source_diversity: number; evidence_ids: string[] }[];
  appearances: { id: string; title: string; figure: string; occurred_at: string; source_status: string; topics: { label: string; share: number }[]; message_consistency: number; quote_pickup: number; lift: Record<string, number>; evidence_ids: string[] }[];
  audience_lab: { name: string; basis: string; synthetic: boolean; sample_runs: number; consensus: number; variance: number; rubric: Record<string, number>; note: string }[];
  latest_poll: PollRecord;
  coverage: CoverageReport;
  evidence: { id: string; title: string; url: string; source: string; published_at: string | null; captured_at: string; layer: string; rights: string; geography: string; classification_confidence: number; observation_type: string }[];
  provider_status: Record<string, string>;
};

export type ScenarioComparison = {
  context_pack: string;
  provider_status: string;
  cohorts: number;
  results: { id: string; title: string; rubric: Record<string, number>; consensus: number; variance: number; sample_runs_per_cohort: number; label: string }[];
  warnings: string[];
};

export type IntelligenceScenario = {
  id: string;
  subject_id: string;
  title: string;
  narrative: string;
  proposed_action: string;
  cohort: Record<string, unknown>;
  effective_at: string;
  status: string;
  forecast: {
    direction?: string;
    lower_pct?: number;
    central_pct?: number;
    upper_pct?: number;
    confidence?: number;
    signal_count?: number;
    representative_calibration?: boolean;
    valid_until?: string;
  };
  assumptions: string[];
  evidence: { url?: string; title?: string | null; observed_at?: string }[];
  model_version: string;
  created_at: string;
};

export type StrategyVerdict = {
  id: string;
  scenario_id: string;
  status: string;
  recommendation: string;
  rationale: string;
  confidence: number;
  risk_level: string;
  critic: Record<string, unknown>;
  evidence: { url?: string; title?: string | null }[];
  expires_at: string;
  approved_by: string | null;
  approved_at: string | null;
  created_at: string;
};

export type AgentDefinition = {
  id: string;
  name: string;
  role: string;
  stage: string;
  verdict_authority: boolean;
};

export type AgentFleet = {
  agents: AgentDefinition[];
  invariant: string;
};

export type CollectionSource = {
  id: string;
  name: string;
  base_url: string;
  authority: string;
  connector_kind: string;
  status: string;
  schedule_minutes: number;
  robots_observed: boolean;
  allowed_paths: string[];
  last_collected_at: string | null;
};

export type CollectionSubscription = {
  id: string;
  collection_source_id: string;
  subject_id: string;
  path: string;
  language: string;
  event_type: string;
  status: string;
  next_due_at: string;
  last_collected_at: string | null;
  last_error: string | null;
  consecutive_failures: number;
};

export type ScenarioCreateInput = {
  subject_id?: string;
  title: string;
  narrative: string;
  proposed_action: string;
  cohort: {
    label: string;
    sample_size: number;
    regions: string[];
    age_band?: string;
    evidence_basis: string;
  };
};

// --- Endpoints --------------------------------------------------------------

export const api = {
  async login(username: string, password: string): Promise<LoginResponse> {
    return request<LoginResponse>("/api/session/login", {
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
  async getActiveBrief(): Promise<BriefActiveOut> {
    return request<BriefActiveOut>("/api/v1/briefs/active");
  },
  async getBrief(id: string): Promise<BriefOut> {
    return request<BriefOut>(`/api/v1/briefs/${id}`);
  },
  async getLatestBrief(): Promise<BriefOut> {
    return request<BriefOut>("/api/v1/briefs/latest");
  },
  async archiveBrief(id: string): Promise<void> {
    await request<void>(`/api/v1/briefs/${id}/archive`, { method: "POST" });
  },
  async getMyIdentity(): Promise<MyIdentityOut> {
    return request<MyIdentityOut>("/api/v1/briefs/me/identity");
  },

  // --- Audience Center ---
  async analyzeAudience(): Promise<BriefGenerateOut> {
    return request<BriefGenerateOut>("/api/v1/audience/analyze", { method: "POST" });
  },
  async getAudienceInstructions(): Promise<AudienceInstructionsSummary> {
    return request<AudienceInstructionsSummary>("/api/v1/audience/instructions");
  },

  // --- Intelligence ---
  async getIntelligenceOverview(): Promise<IntelligenceOverview> {
    return request<IntelligenceOverview>("/api/v1/intelligence/overview");
  },
  async getBriefView(): Promise<ThirtySecondBrief> {
    return request<ThirtySecondBrief>("/api/v1/intelligence/brief");
  },
  async getAnalysisCenter(): Promise<AnalysisCenter> {
    return request<AnalysisCenter>("/api/v1/intelligence/analysis");
  },
  async compareScenarioVariants(variants: { id: string; title: string; message: string }[]): Promise<ScenarioComparison> {
    return request<ScenarioComparison>("/api/v1/intelligence/scenario-comparison", {
      method: "POST",
      body: JSON.stringify({ variants }),
    });
  },
  async getAgentFleet(): Promise<AgentFleet> {
    return request<AgentFleet>("/api/v1/intelligence/agents");
  },
  async listScenarios(): Promise<IntelligenceScenario[]> {
    return request<IntelligenceScenario[]>("/api/v1/intelligence/scenarios");
  },
  async createScenario(payload: ScenarioCreateInput): Promise<{ scenario: IntelligenceScenario; verdict: StrategyVerdict }> {
    return request<{ scenario: IntelligenceScenario; verdict: StrategyVerdict }>("/api/v1/intelligence/scenarios", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  async listVerdicts(): Promise<StrategyVerdict[]> {
    return request<StrategyVerdict[]>("/api/v1/intelligence/verdicts");
  },
  async reviewVerdict(id: string, decision: "approved" | "rejected", review_note: string): Promise<StrategyVerdict> {
    return request<StrategyVerdict>(`/api/v1/intelligence/verdicts/${encodeURIComponent(id)}`, {
      method: "PATCH",
      body: JSON.stringify({ decision, review_note }),
      saAuth: true,
    });
  },
  async listCollectionSources(): Promise<CollectionSource[]> {
    return request<CollectionSource[]>("/api/v1/intelligence/sources", { saAuth: true });
  },
  async createCollectionSource(payload: {
    name: string;
    base_url: string;
    authority: "official_api" | "licensed_feed" | "public_web" | "representative_poll" | "consented_panel";
    connector_kind: "scrapling" | "official_api" | "licensed_feed";
    schedule_minutes: number;
    robots_observed: boolean;
    allowed_paths: string[];
  }): Promise<CollectionSource> {
    return request<CollectionSource>("/api/v1/intelligence/sources", {
      method: "POST",
      body: JSON.stringify(payload),
      saAuth: true,
    });
  },
  async collectSource(sourceId: string, payload: {
    subject_id?: string;
    path: string;
    language: "und" | "en" | "fil";
    event_type: string;
  }): Promise<{ created: boolean; signal: IntelligenceSignal }> {
    return request<{ created: boolean; signal: IntelligenceSignal }>(`/api/v1/intelligence/sources/${encodeURIComponent(sourceId)}/collect`, {
      method: "POST",
      body: JSON.stringify(payload),
      saAuth: true,
    });
  },
  async listCollectionSubscriptions(): Promise<CollectionSubscription[]> {
    return request<CollectionSubscription[]>("/api/v1/intelligence/subscriptions", { saAuth: true });
  },
  async createCollectionSubscription(sourceId: string, payload: {
    subject_id: string;
    path: string;
    language: "und" | "en" | "fil";
    event_type: string;
  }): Promise<CollectionSubscription> {
    return request<CollectionSubscription>(
      `/api/v1/intelligence/sources/${encodeURIComponent(sourceId)}/subscriptions`,
      {
        method: "POST",
        body: JSON.stringify(payload),
        saAuth: true,
      },
    );
  },

  // --- Admin console ---
  async disambiguatePrincipal(name_query: string, hint?: string): Promise<IdentityCandidate> {
    return request<IdentityCandidate>("/api/v1/admin/disambiguate", {
      method: "POST",
      body: JSON.stringify({ name_query, hint: hint || null }),
      saAuth: true,
    });
  },
  async createPrincipal(name_query: string, candidate: IdentityCandidate): Promise<CreatePrincipalOut> {
    return request<CreatePrincipalOut>("/api/v1/admin/principals", {
      method: "POST",
      body: JSON.stringify({ name_query, candidate }),
      saAuth: true,
    });
  },
  async listGlossaryFigures(params?: { q?: string; category?: string }): Promise<PoliticalFigureSummary[]> {
    const search = new URLSearchParams();
    if (params?.q) search.set("q", params.q);
    if (params?.category) search.set("category", params.category);
    return request<PoliticalFigureSummary[]>(`/api/v1/admin/glossary/figures${search.size ? `?${search}` : ""}`, { saAuth: true });
  },
  async getGlossaryFigure(slug: string): Promise<PoliticalFigureDetail> {
    return request<PoliticalFigureDetail>(`/api/v1/admin/glossary/figures/${encodeURIComponent(slug)}`, { saAuth: true });
  },
  async seedGlossary(): Promise<{ run_id: string; status: string }> {
    return request<{ run_id: string; status: string }>("/api/v1/admin/glossary/seed", { method: "POST", saAuth: true });
  },
  async refreshGlossaryFigure(slug: string): Promise<{ run_id: string; status: string }> {
    return request<{ run_id: string; status: string }>(`/api/v1/admin/glossary/figures/${encodeURIComponent(slug)}/refresh`, { method: "POST", saAuth: true });
  },
  async listPrincipals(): Promise<PrincipalSummary[]> {
    return request<PrincipalSummary[]>("/api/v1/admin/principals", { saAuth: true });
  },
  async getPrincipalDetail(profileId: string): Promise<PrincipalDetail> {
    return request<PrincipalDetail>(`/api/v1/admin/principals/${profileId}`, { saAuth: true });
  },
  async rerunPidaa(profileId: string): Promise<{ run_id: string; status: string }> {
    return request<{ run_id: string; status: string }>(`/api/v1/admin/principals/${profileId}/rerun`, {
      method: "POST",
      saAuth: true,
    });
  },
  async archivePrincipal(profileId: string): Promise<void> {
    return request<void>(`/api/v1/admin/principals/${profileId}`, {
      method: "DELETE",
      saAuth: true,
    });
  },
  async listUsers(): Promise<AdminUser[]> {
    return request<AdminUser[]>("/api/v1/admin/users", { saAuth: true });
  },
  async createUser(payload: AdminUserCreate): Promise<AdminUser> {
    return request<AdminUser>("/api/v1/admin/users", {
      method: "POST",
      body: JSON.stringify(payload),
      saAuth: true,
    });
  },
  async deleteUser(userId: string): Promise<void> {
    return request<void>(`/api/v1/admin/users/${encodeURIComponent(userId)}`, {
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
  const res = await fetch(`${API_BASE}/runs/${encodeURIComponent(runId)}/events`, {
    credentials: "same-origin",
    cache: "no-store",
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
