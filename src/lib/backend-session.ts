import { cookies } from "next/headers";
import type { NextRequest } from "next/server";

export const SESSION_COOKIE = "parallax.session_token";
export const SESSION_MARKER_COOKIE = "parallax.session";
export const BACKEND_BASE = process.env.BACKEND_API_BASE ?? "http://127.0.0.1:8000";
export const MAX_PROXY_BODY_BYTES = 1_000_000;

export async function readSessionToken(): Promise<string | null> {
  return (await cookies()).get(SESSION_COOKIE)?.value ?? null;
}

export function requireSameOrigin(request: NextRequest): Response | null {
  if (!new Set(["POST", "PUT", "PATCH", "DELETE"]).has(request.method)) return null;
  const origin = request.headers.get("origin");
  const fetchSite = request.headers.get("sec-fetch-site");
  const host = request.headers.get("host");
  const forwardedProtocol = request.headers.get("x-forwarded-proto")?.split(",", 1)[0]?.trim();
  let originMatches = false;
  try {
    const parsedOrigin = origin ? new URL(origin) : null;
    const expectedProtocol = forwardedProtocol
      ? `${forwardedProtocol}:`
      : request.nextUrl.protocol;
    originMatches = Boolean(
      parsedOrigin && host && parsedOrigin.host === host && parsedOrigin.protocol === expectedProtocol,
    );
  } catch {
    originMatches = false;
  }
  if (!originMatches || (fetchSite && fetchSite !== "same-origin")) {
    return Response.json({ detail: "Cross-origin request denied" }, { status: 403 });
  }
  return null;
}

export function requestBodyIsBounded(request: NextRequest): boolean {
  const raw = request.headers.get("content-length");
  if (!raw) return true;
  const length = Number(raw);
  return Number.isFinite(length) && length >= 0 && length <= MAX_PROXY_BODY_BYTES;
}

export function sessionCookieOptions(maxAge = 60 * 60) {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict" as const,
    path: "/",
    maxAge,
    priority: "high" as const,
  };
}
