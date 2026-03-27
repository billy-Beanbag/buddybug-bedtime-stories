import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import {
  getPrelaunchStaffAccessCookieValue,
  PRELAUNCH_STAFF_ACCESS_COOKIE,
} from "@/lib/prelaunch/config";

export const runtime = "nodejs";

function getSafeRedirectPath(value: string | null) {
  if (!value || !value.startsWith("/") || value.startsWith("//")) {
    return "/library";
  }
  return value;
}

export async function GET(request: NextRequest) {
  const configuredKey = process.env.PRELAUNCH_STAFF_ACCESS_KEY;
  if (!configuredKey) {
    return NextResponse.json({ message: "PRELAUNCH_STAFF_ACCESS_KEY is not configured." }, { status: 500 });
  }

  const requestKey = request.nextUrl.searchParams.get("key");
  if (requestKey !== configuredKey) {
    return NextResponse.json({ message: "Unauthorized" }, { status: 401 });
  }

  const nextPath = getSafeRedirectPath(request.nextUrl.searchParams.get("next"));
  const response = NextResponse.redirect(new URL(nextPath, request.url));
  response.cookies.set(PRELAUNCH_STAFF_ACCESS_COOKIE, getPrelaunchStaffAccessCookieValue(), {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 12,
  });
  return response;
}
