import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { PRELAUNCH_STAFF_ACCESS_COOKIE } from "@/lib/prelaunch/config";

export const runtime = "nodejs";

export async function GET(request: NextRequest) {
  const response = NextResponse.redirect(new URL("/", request.url));
  response.cookies.set(PRELAUNCH_STAFF_ACCESS_COOKIE, "", {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 0,
  });
  return response;
}
