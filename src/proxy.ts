import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const TOKEN_KEY = "parallax.token";

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Auth-required routes
  if (pathname === "/brief" || pathname.startsWith("/brief/")) {
    const token = request.cookies.get(TOKEN_KEY)?.value;
    if (!token) {
      return NextResponse.redirect(new URL("/login", request.url));
    }
  }

  return NextResponse.next();
}

export const proxyConfig = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
