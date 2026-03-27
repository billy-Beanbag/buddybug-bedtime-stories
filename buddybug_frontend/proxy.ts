import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { isAllowedPrelaunchPath } from "@/lib/prelaunch/config";

export function proxy(request: NextRequest) {
  if (!isAllowedPrelaunchPath(request.nextUrl.pathname)) {
    return NextResponse.redirect(new URL("/", request.url));
  }
  return NextResponse.next();
}
