import { NextRequest } from "next/server";

import {
  BACKEND_BASE,
  MAX_PROXY_BODY_BYTES,
  readSessionToken,
  requestBodyIsBounded,
  requireSameOrigin,
} from "@/lib/backend-session";

const ALLOWED_SEGMENT = /^[A-Za-z0-9._-]+$/;

async function proxyRequest(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const crossOrigin = requireSameOrigin(request);
  if (crossOrigin) return crossOrigin;
  if (!requestBodyIsBounded(request)) {
    return Response.json({ detail: "Request body too large" }, { status: 413 });
  }
  const token = await readSessionToken();
  if (!token) return Response.json({ detail: "Authentication required" }, { status: 401 });

  const { path } = await context.params;
  if (
    !path.length ||
    path.some(
      (segment) =>
        !ALLOWED_SEGMENT.test(segment) || segment === "." || segment === "..",
    )
  ) {
    return Response.json({ detail: "Invalid backend path" }, { status: 400 });
  }
  const target = new URL(`/api/v1/${path.join("/")}`, BACKEND_BASE);
  request.nextUrl.searchParams.forEach((value, key) => target.searchParams.append(key, value));

  const headers = new Headers({
    Authorization: `Bearer ${token}`,
    Accept: request.headers.get("accept") ?? "application/json",
  });
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("Content-Type", contentType);
  const hasBody = !new Set(["GET", "HEAD"]).has(request.method);
  const body = hasBody ? await request.arrayBuffer() : undefined;
  if (body && body.byteLength > MAX_PROXY_BODY_BYTES) {
    return Response.json({ detail: "Request body too large" }, { status: 413 });
  }

  try {
    const backend = await fetch(target, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
      signal: AbortSignal.timeout(30_000),
    });
    const responseHeaders = new Headers();
    responseHeaders.set("Content-Type", backend.headers.get("content-type") ?? "application/json");
    responseHeaders.set("Cache-Control", "no-store");
    return new Response(backend.body, { status: backend.status, headers: responseHeaders });
  } catch {
    return Response.json({ detail: "Backend service unavailable" }, { status: 503 });
  }
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
