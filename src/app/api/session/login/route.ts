import { NextRequest, NextResponse } from "next/server";

import {
  BACKEND_BASE,
  MAX_PROXY_BODY_BYTES,
  SESSION_COOKIE,
  SESSION_MARKER_COOKIE,
  requestBodyIsBounded,
  requireSameOrigin,
  sessionCookieOptions,
} from "@/lib/backend-session";

type BackendLogin = {
  access_token?: unknown;
  token_type?: unknown;
  user?: unknown;
};

export async function POST(request: NextRequest) {
  const crossOrigin = requireSameOrigin(request);
  if (crossOrigin) return crossOrigin;
  if (!requestBodyIsBounded(request)) {
    return Response.json({ detail: "Request body too large" }, { status: 413 });
  }

  const rawBody = await request.arrayBuffer();
  if (rawBody.byteLength > MAX_PROXY_BODY_BYTES) {
    return Response.json({ detail: "Request body too large" }, { status: 413 });
  }

  let credentials: unknown;
  try {
    credentials = JSON.parse(new TextDecoder().decode(rawBody));
  } catch {
    return Response.json({ detail: "Invalid authentication request" }, { status: 400 });
  }
  if (
    typeof credentials !== "object" ||
    credentials === null ||
    typeof (credentials as Record<string, unknown>).username !== "string" ||
    typeof (credentials as Record<string, unknown>).password !== "string"
  ) {
    return Response.json({ detail: "Invalid authentication request" }, { status: 400 });
  }

  let backend: Response;
  try {
    backend = await fetch(`${BACKEND_BASE}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(credentials),
      cache: "no-store",
      signal: AbortSignal.timeout(12_000),
    });
  } catch {
    return Response.json({ detail: "Authentication service unavailable" }, { status: 503 });
  }

  const payload = (await backend.json().catch(() => ({}))) as BackendLogin;
  if (!backend.ok || typeof payload.access_token !== "string" || !payload.user) {
    return Response.json(
      { detail: backend.status === 429 ? "Authentication temporarily unavailable" : "Invalid username or password" },
      { status: backend.status === 429 ? 429 : 401 },
    );
  }

  const response = NextResponse.json({ access_token: "", token_type: "bearer", user: payload.user });
  const role = (payload.user as Record<string, unknown>).role;
  const maxAge = role === "superadmin" ? 15 * 60 : 60 * 60;
  response.cookies.set(SESSION_COOKIE, payload.access_token, sessionCookieOptions(maxAge));
  response.cookies.set(SESSION_MARKER_COOKIE, "active", {
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge,
  });
  response.headers.set("Cache-Control", "no-store");
  return response;
}
