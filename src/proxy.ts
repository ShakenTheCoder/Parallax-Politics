import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const TOKEN_KEY = "parallax.session_token";

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // The backend remains the authorization authority; Proxy only rejects clearly
  // unauthenticated navigation before client code renders protected pages.
  const protectedRoute = ["/admin", "/identity", "/brief", "/audience", "/intelligence"].some(
    (route) => pathname === route || pathname.startsWith(`${route}/`),
  );
  if (protectedRoute) {
    const token = request.cookies.get(TOKEN_KEY)?.value;
    if (!token) {
      return NextResponse.redirect(new URL("/login", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
