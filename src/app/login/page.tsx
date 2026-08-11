"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, isAdminRole } from "@/lib/api";
import { useSession } from "@/lib/SessionContext";
import RotatingEarth from "@/components/ui/wireframe-dotted-globe";

export default function Login() {
  const router = useRouter();
  const { loginSession } = useSession();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await api.login(username, password);
      loginSession(data.user);
      router.replace(isAdminRole(data.user.role) ? "/admin" : "/brief");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Login failed";
      setError(msg.includes("401") ? "Credential verification failed" : "Secure authentication service unavailable");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative isolate min-h-screen overflow-hidden bg-background text-foreground flex flex-col items-center justify-center px-4">
      <div className="pointer-events-none absolute inset-0 flex -translate-y-10 items-center justify-center opacity-25">
        <RotatingEarth width={760} height={600} className="w-full max-w-3xl" />
      </div>
      <div className="relative z-10 -translate-y-10 w-full max-w-md space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">Political Analysis Access</h1>
          <p className="text-muted-foreground">Authorized personnel only · Parallax Politics</p>
        </div>

        <form onSubmit={handleSubmit} className="mx-auto w-full max-w-xs space-y-6" autoComplete="on">
          <div className="space-y-4">
            <div>
              <input
                type="text"
                name="username"
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                autoCapitalize="none"
                autoCorrect="off"
                spellCheck={false}
                className="mx-auto block w-full max-w-xs px-4 py-2.5 border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-foreground"
                required
                disabled={loading}
              />
            </div>
            <div>
              <input
                type="password"
                name="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                className="mx-auto block w-full max-w-xs px-4 py-2.5 border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-foreground"
                required
                disabled={loading}
              />
            </div>
          </div>
          {error && (
            <div className="text-sm text-red-600 dark:text-red-400 text-center">
              {error}
            </div>
          )}
          <button
            type="submit"
            className="mx-auto block w-full max-w-[180px] px-4 py-2.5 bg-foreground text-background font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
            disabled={loading}
          >
            {loading ? "Authenticating..." : "Authenticate"}
          </button>
        </form>
      </div>
    </div>
  );
}
