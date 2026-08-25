"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { redirect, useRouter } from "next/navigation";
import { api, AudienceInstructionsSummary, isAdminRole } from "@/lib/api";
import { useSession } from "@/lib/SessionContext";

export default function AudienceRedirectPage() {
  redirect("/analysis#audience-lab");
}

export function LegacyAudienceCenterPage() {
  const router = useRouter();
  const { user, loading: sessionLoading } = useSession();
  const [activeTab, setActiveTab] = useState<"personal" | "competitors" | "contextual" | "facebook">("personal");
  const [instructions, setInstructions] = useState<AudienceInstructionsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchInstructions = useCallback(async () => {
    try {
      const data = await api.getAudienceInstructions();
      setInstructions(data);
    } catch (err) {
      // Don't show error if it's just a 404/not found (meaning no instructions yet)
      const msg = err instanceof Error ? err.message : String(err);
      if (!msg.includes("404")) {
        console.error("Failed to fetch audience instructions:", err);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (sessionLoading) return;
    if (isAdminRole(user?.role)) {
      router.replace("/admin");
      return;
    }
    const task = window.setTimeout(() => void fetchInstructions(), 0);
    return () => {
      window.clearTimeout(task);
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [fetchInstructions, router, sessionLoading, user?.role]);

  const handleGenerate = async () => {
    if (generating) return;
    
    setGenerating(true);
    setError(null);
    
    try {
      await api.analyzeAudience();
      
      // Simple polling mechanism to check for completion
      // (Since we don't have a dedicated SSE endpoint for audience runs right now, 
      // we'll just poll the instructions endpoint until we get new data)
      const startTime = Date.now();
      
      pollRef.current = setInterval(async () => {
        try {
          const newData = await api.getAudienceInstructions();
          // If we got valid new instructions back, we can stop polling
          if (newData && (newData.personal || newData.competitors || newData.contextual)) {
            setInstructions(newData);
            setGenerating(false);
            if (pollRef.current) clearInterval(pollRef.current);
          }
        } catch {
          // Ignore polling errors
        }
        
        // Timeout after 60 seconds
        if (Date.now() - startTime > 60000) {
          setGenerating(false);
          setError("Generation timed out. Please try refreshing the page.");
          if (pollRef.current) clearInterval(pollRef.current);
        }
      }, 5000);
      
    } catch (err) {
      setGenerating(false);
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const renderPersonalTab = () => {
    const data = instructions?.personal;
    if (!data) return renderEmptyState("Personal Audience");
    
    return (
      <div className="space-y-6">
        <div className="border border-border p-5 space-y-4">
          <div className="flex justify-between items-baseline border-b border-border pb-3">
            <h3 className="text-sm font-semibold tracking-widest uppercase">Target Focus</h3>
            <span className="text-xs text-muted-foreground border px-2 py-0.5 border-border">READY</span>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-1">Target Name</p>
              <p className="text-sm font-medium">{data.target_name}</p>
            </div>
            <div>
              <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-1">Aliases</p>
              <div className="flex flex-wrap gap-1">
                {data.aliases.map((alias, i) => (
                  <span key={i} className="text-xs bg-muted px-2 py-0.5 border border-border">{alias}</span>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="border border-border p-5 space-y-4">
          <h3 className="text-sm font-semibold tracking-widest uppercase border-b border-border pb-3">Extraction Guidelines</h3>
          
          <div className="space-y-4">
            <div>
              <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-2">Priority Topics</p>
              <ul className="list-disc pl-5 space-y-1">
                {data.priority_topics.map((topic, i) => (
                  <li key={i} className="text-sm">{topic}</li>
                ))}
              </ul>
            </div>
            
            <div>
              <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-2">Focus Keywords</p>
              <div className="flex flex-wrap gap-1.5">
                {data.focus_keywords.map((kw, i) => (
                  <span key={i} className="text-xs font-mono border border-border px-1.5 py-0.5">{kw}</span>
                ))}
              </div>
            </div>
            
          </div>
        </div>

        <div className="border-l-2 border-foreground pl-4 py-2 bg-muted/20">
          <p className="text-sm italic text-muted-foreground">{data.instructions_summary}</p>
        </div>
      </div>
    );
  };

  const renderCompetitorsTab = () => {
    const data = instructions?.competitors;
    if (!data) return renderEmptyState("Competitor Intelligence");
    
    return (
      <div className="space-y-6">
        <div className="border border-border p-5 space-y-4">
          <div className="flex justify-between items-baseline border-b border-border pb-3">
            <h3 className="text-sm font-semibold tracking-widest uppercase">Primary Competitors</h3>
            <span className="text-xs text-muted-foreground border px-2 py-0.5 border-border">READY</span>
          </div>
          
          <div className="flex flex-wrap gap-2">
            {data.primary_competitors.map((comp, i) => (
              <span key={i} className="text-sm font-medium border border-red-500/60 bg-red-500/5 px-3 py-1.5">{comp}</span>
            ))}
          </div>
        </div>

        <div className="border border-border p-5 space-y-4">
          <h3 className="text-sm font-semibold tracking-widest uppercase border-b border-border pb-3">Adversarial Tracking</h3>
          
          <div className="space-y-4">
            <div>
              <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-2">Topics of Contention</p>
              <ul className="list-disc pl-5 space-y-1">
                {data.topics_of_contention.map((topic, i) => (
                  <li key={i} className="text-sm">{topic}</li>
                ))}
              </ul>
            </div>
            
            <div>
              <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-2">Tracking Priorities</p>
              <ul className="list-disc pl-5 space-y-1">
                {data.tracking_priorities.map((priority, i) => (
                  <li key={i} className="text-sm text-muted-foreground">{priority}</li>
                ))}
              </ul>
            </div>
            
            <div>
              <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-2">Competitor Keywords</p>
              <div className="flex flex-wrap gap-1.5">
                {data.competitor_keywords.map((kw, i) => (
                  <span key={i} className="text-xs font-mono border border-border px-1.5 py-0.5">{kw}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
        
        <div className="border-l-2 border-foreground pl-4 py-2 bg-muted/20">
          <p className="text-sm italic text-muted-foreground">{data.instructions_summary}</p>
        </div>
      </div>
    );
  };

  const renderContextualTab = () => {
    const data = instructions?.contextual;
    if (!data) return renderEmptyState("Contextual & Regional Audience");
    
    return (
      <div className="space-y-6">
        <div className="border border-border p-5 space-y-4">
          <div className="flex justify-between items-baseline border-b border-border pb-3">
            <h3 className="text-sm font-semibold tracking-widest uppercase">Demographic Focus</h3>
            <span className="text-xs text-muted-foreground border px-2 py-0.5 border-border">READY</span>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-2">Target Regions</p>
              <div className="flex flex-wrap gap-1.5">
                {data.target_regions.map((region, i) => (
                  <span key={i} className="text-xs border border-border px-2 py-0.5">{region}</span>
                ))}
              </div>
            </div>
            <div>
              <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-2">Key Cohorts</p>
              <div className="flex flex-wrap gap-1.5">
                {data.demographic_segments.map((segment, i) => (
                  <span key={i} className="text-xs border border-blue-500/60 bg-blue-500/5 px-2 py-0.5">{segment}</span>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="border border-border p-5 space-y-4">
          <h3 className="text-sm font-semibold tracking-widest uppercase border-b border-border pb-3">Macro Environment</h3>
          
          <div className="space-y-4">
            <div>
              <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-2">Salient Issues</p>
              <ul className="list-disc pl-5 space-y-1">
                {data.salient_issues.map((issue, i) => (
                  <li key={i} className="text-sm">{issue}</li>
                ))}
              </ul>
            </div>
            
          </div>
        </div>
        
        <div className="border-l-2 border-foreground pl-4 py-2 bg-muted/20">
          <p className="text-sm italic text-muted-foreground">{data.instructions_summary}</p>
        </div>
      </div>
    );
  };

  const renderFacebookTab = () => {
    const data = instructions?.facebook_analysis;
    if (!data) return renderEmptyState("Facebook Landscape Analysis");
    
    return (
      <div className="space-y-6">
        <div className="border border-border p-5 space-y-4">
          <div className="flex justify-between items-baseline border-b border-border pb-3">
            <h3 className="text-sm font-semibold tracking-widest uppercase">Overall Landscape Summary</h3>
            <span className="text-xs text-muted-foreground border px-2 py-0.5 border-border">ANALYZED</span>
          </div>
          <p className="text-sm">{data.overall_landscape_summary}</p>
        </div>

        {data.categories.map((cat, idx) => (
          <div key={idx} className="border border-border p-5 space-y-4">
            <h3 className="text-sm font-semibold tracking-widest uppercase border-b border-border pb-3">
              {cat.category_name} Analysis
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-2">Sentiment Distribution</p>
                <div className="flex gap-2 text-sm">
                  {Object.entries(cat.sentiment_distribution).map(([sentiment, val]) => (
                    <span key={sentiment} className="font-medium">
                      {sentiment}: {val}%
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-2">Engagement Metrics</p>
                <div className="flex gap-4 text-sm">
                  {Object.entries(cat.engagement_metrics).map(([metric, val]) => (
                    <span key={metric} className="font-medium">
                      {metric}: {val}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div>
              <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-2">Top Themes</p>
              <div className="flex flex-wrap gap-1.5">
                {cat.top_themes.map((theme, i) => (
                  <span key={i} className="text-xs bg-muted px-2 py-0.5 border border-border">{theme}</span>
                ))}
              </div>
            </div>

            <div>
              <p className="text-[10px] tracking-widest uppercase text-muted-foreground mb-2">Key Findings</p>
              <ul className="list-disc pl-5 space-y-1 text-sm">
                {cat.key_findings.map((finding, i) => (
                  <li key={i}>{finding}</li>
                ))}
              </ul>
            </div>
          </div>
        ))}

        <div className="border border-border p-5 space-y-4 bg-muted/10">
          <h3 className="text-sm font-semibold tracking-widest uppercase border-b border-border pb-3">Actionable Recommendations</h3>
          <ul className="list-disc pl-5 space-y-2 text-sm font-medium">
            {data.actionable_recommendations.map((rec, i) => (
              <li key={i}>{rec}</li>
            ))}
          </ul>
        </div>
      </div>
    );
  };

  const renderEmptyState = (title: string) => (
    <div className="p-10 text-center space-y-3">
      <p className="text-sm font-medium">{title} Instructions Not Found</p>
      <p className="text-xs text-muted-foreground">
        Run the audience analysis to generate extraction instructions for this perspective.
      </p>
    </div>
  );

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="max-w-4xl mx-auto px-4 py-10 space-y-8">
        
        {/* Header Section */}
        <div className="space-y-2">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Audience Center</h1>
              <p className="text-sm text-muted-foreground mt-1">
                Data extraction instructions and monitoring directives generated by specialized agents.
              </p>
            </div>
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="bg-foreground text-background px-4 py-2 text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity whitespace-nowrap"
            >
              {generating ? "Analyzing Audience..." : "Run Audience Analysis"}
            </button>
          </div>
          {error && <p className="text-sm text-red-500 mt-2">{error}</p>}
          {instructions?.last_updated_at && !generating && (
            <p className="text-xs text-muted-foreground mt-2">
              Last updated: {new Date(instructions.last_updated_at).toLocaleString()}
            </p>
          )}
        </div>

        {/* Tabs */}
        {loading ? (
          <div className="py-10 text-center"><p className="text-sm text-muted-foreground animate-pulse">Loading instructions...</p></div>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center gap-1 border-b border-border overflow-x-auto">
              <button
                onClick={() => setActiveTab("personal")}
                className={`px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap ${
                  activeTab === "personal"
                    ? "tab-active"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Personal
              </button>
              <button
                onClick={() => setActiveTab("competitors")}
                className={`px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap ${
                  activeTab === "competitors"
                    ? "tab-active"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Competitors
              </button>
              <button
                onClick={() => setActiveTab("contextual")}
                className={`px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap ${
                  activeTab === "contextual"
                    ? "tab-active"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Contextual
              </button>
              <button
                onClick={() => setActiveTab("facebook")}
                className={`px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap ${
                  activeTab === "facebook"
                    ? "tab-active"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Facebook Analysis
              </button>
            </div>

            {/* Tab Content */}
            <div className="min-h-[400px]">
              {activeTab === "personal" && renderPersonalTab()}
              {activeTab === "competitors" && renderCompetitorsTab()}
              {activeTab === "contextual" && renderContextualTab()}
              {activeTab === "facebook" && renderFacebookTab()}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
