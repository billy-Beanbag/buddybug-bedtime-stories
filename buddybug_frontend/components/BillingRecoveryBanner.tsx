"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";

import { useAuth } from "@/context/AuthContext";
import { trackEvent } from "@/lib/analytics";
import type { BillingRecoveryPromptResponse } from "@/lib/types";

function recoveryMetadata(prompt: BillingRecoveryPromptResponse) {
  return {
    recovery_case_id: prompt.case?.id ?? null,
    recovery_status: prompt.case?.recovery_status ?? null,
    billing_status_snapshot: prompt.case?.billing_status_snapshot ?? null,
    source_type: prompt.case?.source_type ?? null,
  };
}

export function BillingRecoveryBanner({
  prompt,
  onAction,
  actionLoading = false,
}: {
  prompt: BillingRecoveryPromptResponse | null;
  onAction?: () => Promise<void> | void;
  actionLoading?: boolean;
}) {
  const { token, user } = useAuth();
  const viewedCaseIdRef = useRef<number | null>(null);

  useEffect(() => {
    if (!prompt?.has_open_recovery || !prompt.case || viewedCaseIdRef.current === prompt.case.id) {
      return;
    }
    viewedCaseIdRef.current = prompt.case.id;
    void trackEvent(
      {
        event_name: "billing_recovery_prompt_viewed",
        metadata: {
          ...recoveryMetadata(prompt),
          surface: "profile_billing_recovery_banner",
        },
      },
      { token, user },
    );
  }, [prompt, token, user]);

  if (!prompt?.has_open_recovery || !prompt.case || !prompt.message || !prompt.action_label) {
    return null;
  }

  const content = (
    <>
      <div>
        <h2 className="text-lg font-semibold text-amber-950">{prompt.case.title}</h2>
        <p className="mt-2 text-sm leading-6 text-amber-900">{prompt.message}</p>
      </div>
      <div className="flex flex-wrap gap-3">
        {onAction ? (
          <button
            type="button"
            onClick={() => {
              void trackEvent(
                {
                  event_name: "billing_recovery_prompt_clicked",
                  metadata: {
                    ...recoveryMetadata(prompt),
                    surface: "profile_billing_recovery_banner",
                    action_route: prompt.action_route,
                  },
                },
                { token, user },
              );
              void onAction();
            }}
            disabled={actionLoading}
            className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
          >
            {actionLoading ? "Opening billing..." : prompt.action_label}
          </button>
        ) : prompt.action_route ? (
          <Link
            href={prompt.action_route}
            onClick={() => {
              void trackEvent(
                {
                  event_name: "billing_recovery_prompt_clicked",
                  metadata: {
                    ...recoveryMetadata(prompt),
                    surface: "profile_billing_recovery_banner",
                    action_route: prompt.action_route,
                  },
                },
                { token, user },
              );
            }}
            className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white"
          >
            {prompt.action_label}
          </Link>
        ) : null}
        <span className="rounded-2xl border border-amber-200 bg-white/70 px-4 py-3 text-sm text-amber-900">
          We’ll keep this gentle and only show it when premium billing needs attention.
        </span>
      </div>
    </>
  );

  return (
    <section className="rounded-[2rem] border border-amber-200 bg-amber-50/90 p-5 shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">{content}</div>
    </section>
  );
}
