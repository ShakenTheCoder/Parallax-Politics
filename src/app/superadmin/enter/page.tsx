"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, API_BASE, setSAToken } from "@/lib/api";

console.log("[Superadmin] API_BASE:", API_BASE);

export default function SuperadminEnter() {
  const router = useRouter();
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      console.log("[Superadmin] Attempting verify with code:", code.trim());
      const { token } = await api.verifySuperadmin(code.trim());
      console.log("[Superadmin] Verify success, storing token");
      setSAToken(token);
      router.push("/superadmin");
    } catch (err) {
      console.error("[Superadmin] Verify failed:", err);
      const msg = err instanceof Error ? err.message : "Request failed";
      if (msg.includes("403") || msg.includes("Invalid")) {
        setError("Invalid superadmin code.");
      } else if (msg.includes("401")) {
        setError("Authentication required.");
      } else if (msg.includes("NetworkError") || msg.includes("fetch") || msg.includes("Failed to fetch")) {
        setError("Cannot connect to server. Is the backend running?");
      } else {
        setError(`Error: ${msg}`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">Superadmin</h1>
          <p className="text-xs text-muted-foreground tracking-widest uppercase">Parallax · Philippines POC</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="password"
            placeholder="Superadmin code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="w-full px-4 py-3 border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-foreground"
            required
            autoFocus
            disabled={loading}
          />
          {error && <p className="text-sm text-red-600 dark:text-red-400 text-center">{error}</p>}
          <button
            type="submit"
            className="w-full px-4 py-3 bg-foreground text-background font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
            disabled={loading || !code.trim()}
          >
            {loading ? "Verifying…" : "Enter"}
          </button>
        </form>
      </div>
    </div>
  );
}
