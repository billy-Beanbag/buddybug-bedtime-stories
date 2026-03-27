import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { ZodError } from "zod";

import { createOrRefreshSubscriber, deliverWelcomeStory } from "@/lib/prelaunch/service";
import { signupSchema } from "@/lib/prelaunch/validation";
import { sha256 } from "@/lib/security";
import { enforceSignupRateLimit } from "@/lib/security/rate-limit";
import { getClientIp, getRequestUserAgent } from "@/lib/security/request";

export const runtime = "nodejs";

function flattenZodErrors(error: ZodError) {
  const fieldErrors: Record<string, string> = {};
  for (const issue of error.issues) {
    const path = issue.path[0];
    if (typeof path === "string" && !fieldErrors[path]) {
      fieldErrors[path] = issue.message;
    }
  }
  return fieldErrors;
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const parsed = signupSchema.parse(body);

    if (parsed.website) {
      return NextResponse.json(
        {
          message: "Thanks. If your email is valid, your first story will arrive shortly.",
        },
        { status: 200 },
      );
    }

    const rateLimitKey = sha256(`${getClientIp(request)}:${getRequestUserAgent(request)}:${parsed.parentEmail.toLowerCase()}`);
    await enforceSignupRateLimit(rateLimitKey);

    const subscriber = await createOrRefreshSubscriber(parsed);
    const welcomeResult = await deliverWelcomeStory(subscriber.id);

    if (welcomeResult.status === "exhausted") {
      return NextResponse.json(
        {
          message: welcomeResult.message,
        },
        { status: 202 },
      );
    }

    return NextResponse.json({
      message: "You're in. Your first bedtime story is on its way to your inbox now.",
    });
  } catch (error) {
    if (error instanceof ZodError) {
      return NextResponse.json(
        {
          message: "Please correct the highlighted fields and try again.",
          errors: flattenZodErrors(error),
        },
        { status: 400 },
      );
    }

    if (error instanceof Error && error.message.includes("Too many signup attempts")) {
      return NextResponse.json(
        {
          message: error.message,
        },
        { status: 429 },
      );
    }

    console.error("[buddybug-signup] unexpected failure", error);
    return NextResponse.json(
      {
        message: "We couldn't finish your signup just now. Please try again in a moment.",
      },
      { status: 500 },
    );
  }
}
