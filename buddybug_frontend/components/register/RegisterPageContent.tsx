"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { apiPost } from "@/lib/api";
import { getStoredToken } from "@/lib/auth";
import type { CheckoutSessionResponse } from "@/lib/types";

type RegisterPlan = "free" | "premium";

export function RegisterPageContent({ plan }: { plan: RegisterPlan }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading, register } = useAuth();
  const [form, setForm] = useState({
    email: "",
    password: "",
    displayName: "",
    country: "",
    referralCode: "",
    acceptTerms: true,
    acceptPrivacy: true,
  });
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [manualFlow, setManualFlow] = useState(false);
  const pricingPreview = searchParams.get("source") === "pricing";

  const pageCopy = useMemo(
    () =>
      plan === "premium"
        ? {
            eyebrow: "Premium plan",
            title: "Create your Premium account",
            description: "Set up your Buddybug account first, then continue straight into secure Premium checkout.",
            note: "Premium is $9.99 and includes unlimited stories, full library access, bedtime packs, narration voices, unlimited child profiles, and personalised recommendations.",
            steps: [
              "Create one Buddybug account in the shared customer database",
              "Continue directly to Premium checkout",
              "Unlock paid features on the same account after payment succeeds",
            ],
            submitLabel: "Continue to Premium",
            submittingLabel: "Creating account...",
            alternateHref: "/register/free",
            alternateLabel: "Prefer to start free?",
          }
        : {
            eyebrow: "Free plan",
            title: "Create your Free Plan account",
            description: "Set up your Buddybug account first, then continue with your free access.",
            note: "The Free Plan includes 3 stories per week, a smaller library, 1 child profile, and no bedtime packs or narration voice.",
            steps: [
              "Keep the option to upgrade later without losing data or analytics history",
            ],
            submitLabel: "Create Free Account",
            submittingLabel: "Creating account...",
            alternateHref: "/register/premium",
            alternateLabel: "Want Premium instead?",
          },
    [plan],
  );

  useEffect(() => {
    if (!manualFlow && isAuthenticated && !pricingPreview) {
      router.replace(plan === "premium" ? "/upgrade" : "/library");
    }
  }, [isAuthenticated, manualFlow, plan, pricingPreview, router]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    const referralCode = new URLSearchParams(window.location.search).get("ref");
    if (!referralCode) {
      return;
    }
    setForm((current) => ({ ...current, referralCode }));
  }, []);

  async function handlePremiumCheckout() {
    const storedToken = getStoredToken();
    if (!storedToken) {
      router.push("/upgrade");
      return;
    }

    try {
      const response = await apiPost<CheckoutSessionResponse>(
        "/billing/checkout",
        {
          price_key: "premium_monthly",
          success_path: "/getting-started",
          cancel_path: "/getting-started",
        },
        { token: storedToken },
      );
      window.location.assign(response.checkout_url);
    } catch (err) {
      setError(
        err instanceof Error
          ? `${err.message} Your account was created. You can complete Premium signup from the upgrade page.`
          : "Your account was created. You can complete Premium signup from the upgrade page.",
      );
      setSubmitting(false);
    }
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setManualFlow(true);

    try {
      await register({
        email: form.email,
        password: form.password,
        display_name: form.displayName || undefined,
        country: form.country || undefined,
        referral_code: form.referralCode || undefined,
        accept_terms: form.acceptTerms,
        accept_privacy: form.acceptPrivacy,
      });

      if (plan === "premium") {
        await handlePremiumCheckout();
        return;
      }

      router.push("/getting-started");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to register");
      setSubmitting(false);
      setManualFlow(false);
      return;
    }
  }

  if (isLoading) {
    return <LoadingState message="Checking your session..." />;
  }

  return (
    <section className="space-y-5">
      {isAuthenticated && pricingPreview ? (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4 text-sm text-amber-900">
          You are already signed in, so this registration page is being shown for review only. To create another account, log
          out first.
        </div>
      ) : null}
      <div className="rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#111827_0%,#1e1b4b_42%,#312e81_74%,#4338ca_100%)] p-6 text-white shadow-[0_24px_60px_rgba(30,41,59,0.18)]">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-indigo-100">{pageCopy.eyebrow}</p>
        <h2 className="mt-3 text-3xl font-semibold">{pageCopy.title}</h2>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-indigo-50">{pageCopy.description}</p>
        <div className="mt-5 rounded-2xl border border-white/10 bg-white/10 px-4 py-4 text-sm text-indigo-50">
          {pageCopy.note}
        </div>
        <div className="mt-5 grid gap-3">
          {pageCopy.steps.map((step) => (
            <div key={step} className="rounded-2xl border border-white/10 bg-white/10 px-4 py-4 text-sm text-indigo-50">
              {step}
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm">
      <form className="space-y-4" onSubmit={handleSubmit}>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Email</span>
          <input
            type="email"
            value={form.email}
            onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none transition focus:border-indigo-400"
            placeholder="you@example.com"
            required
          />
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Password</span>
          <input
            type="password"
            value={form.password}
            onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none transition focus:border-indigo-400"
            placeholder="At least 8 characters"
            minLength={8}
            required
          />
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Display name</span>
          <input
            type="text"
            value={form.displayName}
            onChange={(event) => setForm((current) => ({ ...current, displayName: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none transition focus:border-indigo-400"
            placeholder="Optional"
          />
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Country</span>
          <input
            type="text"
            value={form.country}
            onChange={(event) => setForm((current) => ({ ...current, country: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none transition focus:border-indigo-400"
            placeholder="Optional"
          />
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Referral code</span>
          <input
            type="text"
            value={form.referralCode}
            onChange={(event) => setForm((current) => ({ ...current, referralCode: event.target.value.toUpperCase() }))}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none transition focus:border-indigo-400"
            placeholder="Optional"
          />
        </label>
        <label className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={form.acceptTerms}
            onChange={(event) => setForm((current) => ({ ...current, acceptTerms: event.target.checked }))}
            required
          />
          <span>
            I agree to the{" "}
            <Link href="/terms" className="font-medium text-indigo-700">
              Terms of Service
            </Link>
            .
          </span>
        </label>
        <label className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={form.acceptPrivacy}
            onChange={(event) => setForm((current) => ({ ...current, acceptPrivacy: event.target.checked }))}
            required
          />
          <span>
            I agree to the{" "}
            <Link href="/privacy-policy" className="font-medium text-indigo-700">
              Privacy Policy
            </Link>
            .
          </span>
        </label>

        {error ? <p className="text-sm text-rose-600">{error}</p> : null}

        <button
          type="submit"
          disabled={submitting || !form.acceptTerms || !form.acceptPrivacy || (isAuthenticated && pricingPreview)}
          className="w-full rounded-2xl bg-slate-900 px-4 py-3 font-medium text-white disabled:opacity-60"
        >
          {isAuthenticated && pricingPreview ? "Already signed in" : submitting ? pageCopy.submittingLabel : pageCopy.submitLabel}
        </button>
      </form>

      <p className="mt-4 text-sm text-slate-600">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-indigo-700">
          Login
        </Link>
      </p>
      <p className="mt-2 text-sm text-slate-600">
        <Link href={pageCopy.alternateHref} className="font-medium text-indigo-700">
          {pageCopy.alternateLabel}
        </Link>
      </p>
      </div>
    </section>
  );
}
