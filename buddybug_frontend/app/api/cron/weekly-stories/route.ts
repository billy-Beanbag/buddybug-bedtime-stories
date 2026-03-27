import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { processWeeklyStoryCron } from "@/lib/prelaunch/service";
import { safeCompareBearerToken } from "@/lib/security";

export const runtime = "nodejs";

export async function GET(request: NextRequest) {
  const cronSecret = process.env.CRON_SECRET;
  if (!cronSecret) {
    console.error("[buddybug-cron] CRON_SECRET is not configured");
    return NextResponse.json({ message: "Cron secret is not configured." }, { status: 500 });
  }

  if (!safeCompareBearerToken(request.headers.get("authorization"), cronSecret)) {
    return NextResponse.json({ message: "Unauthorized" }, { status: 401 });
  }

  const summary = await processWeeklyStoryCron();
  console.info("[buddybug-cron] weekly run complete", summary);
  return NextResponse.json(summary);
}
