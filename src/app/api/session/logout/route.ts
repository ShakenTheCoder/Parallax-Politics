import { NextRequest, NextResponse } from "next/server";

import {
  SESSION_COOKIE,
  SESSION_MARKER_COOKIE,
  requireSameOrigin,
} from "@/lib/backend-session";

export async function POST(request: NextRequest) {
  const crossOrigin = requireSameOrigin(request);
  if (crossOrigin) return crossOrigin;
  const response = NextResponse.json({ status: "signed_out" });
  response.cookies.set(SESSION_COOKIE, "", { httpOnly: true, expires: new Date(0), path: "/" });
  response.cookies.set(SESSION_MARKER_COOKIE, "", { expires: new Date(0), path: "/" });
  response.headers.set("Cache-Control", "no-store");
  return response;
}

