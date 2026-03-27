import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import {
  hasValidPrelaunchStaffAccess,
  isAllowedPrelaunchPath,
  PRELAUNCH_STAFF_ACCESS_COOKIE,
} from "@/lib/prelaunch/config";

export function proxy(request: NextRequest) {
  const { pathname, searchParams } = request.nextUrl;
  const isInternalReaderPreview = pathname.startsWith("/reader/") && searchParams.get("preview") === "1";
  const hasStaffBypass = hasValidPrelaunchStaffAccess(request.cookies.get(PRELAUNCH_STAFF_ACCESS_COOKIE)?.value);

  if (!hasStaffBypass && !isInternalReaderPreview && !isAllowedPrelaunchPath(pathname)) {
    return NextResponse.redirect(new URL("/", request.url));
  }
  return NextResponse.next();
}
