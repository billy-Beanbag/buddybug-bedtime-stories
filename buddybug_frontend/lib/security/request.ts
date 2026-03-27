import type { NextRequest } from "next/server";

export function getClientIp(request: NextRequest) {
  const forwardedFor = request.headers.get("x-forwarded-for");
  if (forwardedFor) {
    return forwardedFor.split(",")[0]?.trim() || "unknown";
  }
  return request.headers.get("x-real-ip") || "unknown";
}

export function getRequestUserAgent(request: NextRequest) {
  return request.headers.get("user-agent") || "unknown";
}
