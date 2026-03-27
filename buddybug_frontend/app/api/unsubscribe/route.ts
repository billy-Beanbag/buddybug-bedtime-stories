import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { ZodError } from "zod";

import { APP_URL } from "@/lib/prelaunch/config";
import { unsubscribeSubscriberByToken } from "@/lib/prelaunch/service";
import { unsubscribeSchema } from "@/lib/prelaunch/validation";

export const runtime = "nodejs";

function buildRedirectUrl(result: "success" | "invalid") {
  const url = new URL("/", APP_URL);
  url.searchParams.set("unsubscribe", result);
  return url;
}

async function handleUnsubscribe(token: string) {
  const unsubscribed = await unsubscribeSubscriberByToken(token);
  return unsubscribed ? "success" : "invalid";
}

export async function GET(request: NextRequest) {
  const token = request.nextUrl.searchParams.get("token") || "";
  const outcome = await handleUnsubscribe(token);
  return NextResponse.redirect(buildRedirectUrl(outcome));
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const parsed = unsubscribeSchema.parse(body);
    const unsubscribed = await unsubscribeSubscriberByToken(parsed.token);
    return NextResponse.json({
      message: unsubscribed ? "You have been unsubscribed from Buddybug emails." : "That unsubscribe link is not valid anymore.",
    });
  } catch (error) {
    if (error instanceof ZodError) {
      return NextResponse.json(
        {
          message: "Missing or invalid unsubscribe token.",
        },
        { status: 400 },
      );
    }

    console.error("[buddybug-unsubscribe] unexpected failure", error);
    return NextResponse.json(
      {
        message: "We couldn't complete that unsubscribe request just now.",
      },
      { status: 500 },
    );
  }
}
