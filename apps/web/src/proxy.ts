import { NextResponse, type NextRequest } from "next/server";

const SESSION_COOKIE = "finansys_access_token";

export function proxy(request: NextRequest) {
  if (request.cookies.has(SESSION_COOKIE)) return NextResponse.next();
  return NextResponse.redirect(new URL("/login", request.url));
}

export const config = {
  matcher: [
    "/",
    "/dashboard/:path*",
    "/gastos/:path*",
    "/metas/:path*",
    "/analises/:path*",
    "/assistente/:path*",
  ],
};
