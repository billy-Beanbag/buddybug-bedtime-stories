"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { BillingRecoveryBanner } from "@/components/BillingRecoveryBanner";
import { BedtimePackSummaryCard } from "@/components/BedtimePackSummaryCard";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { PreferenceProfileCard } from "@/components/PreferenceProfileCard";
import { PremiumUpgradeCard } from "@/components/PremiumUpgradeCard";
import { ProfileCard } from "@/components/ProfileCard";
import { ReengagementList } from "@/components/ReengagementList";
import { WeeklyHighlightCard } from "@/components/WeeklyHighlightCard";
import { ContinueOnboardingCard } from "@/components/onboarding/ContinueOnboardingCard";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { useLocale } from "@/context/LocaleContext";
import { trackLanguageChanged } from "@/lib/analytics";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import { LOCALE_LABELS, SUPPORTED_LOCALES, normalizeLocale, type Locale } from "@/lib/i18n";
import type {
  AchievementDashboardResponse,
  BillingPortalResponse,
  BillingRecoveryPromptResponse,
  BillingStatusResponse,
  CheckoutSessionResponse,
  PrivacyPreferenceRead,
  ReadingPlanRead,
  UserStoryProfileRead,
} from "@/lib/types";

export default function ProfilePage() {
  const {
    user,
    token,
    subscription,
    billing,
    isAuthenticated,
    isEducator,
    isLoading,
    logout,
    refreshMe,
    refreshSubscription,
    refreshBilling,
  } = useAuth();
  const { selectedChildProfile } = useChildProfiles();
  const { locale, setLocale, t } = useLocale();
  const [refreshing, setRefreshing] = useState(false);
  const [profile, setProfile] = useState<UserStoryProfileRead | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [rebuilding, setRebuilding] = useState(false);
  const [billingStatus, setBillingStatus] = useState<BillingStatusResponse | null>(null);
  const [billingActionLoading, setBillingActionLoading] = useState<"checkout" | "portal" | null>(null);
  const [billingActionError, setBillingActionError] = useState<string | null>(null);
  const [billingQueryState, setBillingQueryState] = useState<string | null>(null);
  const [billingRecoveryPrompt, setBillingRecoveryPrompt] = useState<BillingRecoveryPromptResponse | null>(null);
  const [selectedLanguage, setSelectedLanguage] = useState<Locale>(locale);
  const [languageSaving, setLanguageSaving] = useState(false);
  const [languageMessage, setLanguageMessage] = useState<string | null>(null);
  const [languageError, setLanguageError] = useState<string | null>(null);
  const [privacyPreference, setPrivacyPreference] = useState<PrivacyPreferenceRead | null>(null);
  const [achievementDashboard, setAchievementDashboard] = useState<AchievementDashboardResponse | null>(null);
  const [readingPlans, setReadingPlans] = useState<ReadingPlanRead[]>([]);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      setRefreshing(true);
      void Promise.all([refreshMe(), refreshSubscription(), refreshBilling()]).finally(() => setRefreshing(false));
    }
  }, [isAuthenticated, isLoading, refreshBilling, refreshMe, refreshSubscription]);

  useEffect(() => {
    if (billing) {
      setBillingStatus(billing);
    }
  }, [billing]);

  useEffect(() => {
    setSelectedLanguage(normalizeLocale(user?.language || locale));
  }, [locale, user?.language]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    const params = new URLSearchParams(window.location.search);
    setBillingQueryState(params.get("billing"));
  }, []);

  useEffect(() => {
    if (!token || !isAuthenticated) {
      setProfile(null);
      setPrivacyPreference(null);
      setBillingRecoveryPrompt(null);
      return;
    }

    async function loadProfile() {
      setProfileLoading(true);
      setProfileError(null);
      try {
        const response = await apiGet<UserStoryProfileRead>("/feedback/me/profile", { token });
        setProfile(response);
      } catch (err) {
        setProfileError(err instanceof Error ? err.message : "Unable to load preference profile");
      } finally {
        setProfileLoading(false);
      }
    }

    void loadProfile();
  }, [isAuthenticated, token]);

  useEffect(() => {
    if (!token || !isAuthenticated) {
      setPrivacyPreference(null);
      return;
    }

    void apiGet<PrivacyPreferenceRead>("/privacy/me/preferences", { token })
      .then((response) => setPrivacyPreference(response))
      .catch(() => setPrivacyPreference(null));
  }, [isAuthenticated, token]);

  useEffect(() => {
    if (!token || !isAuthenticated) {
      setBillingRecoveryPrompt(null);
      return;
    }

    void apiGet<BillingRecoveryPromptResponse>("/billing-recovery/me", { token })
      .then((response) => setBillingRecoveryPrompt(response))
      .catch(() => setBillingRecoveryPrompt(null));
  }, [isAuthenticated, token]);

  useEffect(() => {
    if (!token || !isAuthenticated) {
      setAchievementDashboard(null);
      setReadingPlans([]);
      return;
    }

    void apiGet<AchievementDashboardResponse>("/achievements/me", {
      token,
      query: { child_profile_id: selectedChildProfile?.id },
    })
      .then((response) => setAchievementDashboard(response))
      .catch(() => setAchievementDashboard(null));

    void apiGet<ReadingPlanRead[]>("/reading-plans/me", {
      token,
      query: { status: "active", child_profile_id: selectedChildProfile?.id },
    })
      .then((response) => setReadingPlans(response))
      .catch(() => setReadingPlans([]));
  }, [isAuthenticated, selectedChildProfile?.id, token]);

  async function handleRebuildProfile() {
    if (!token) {
      return;
    }

    setRebuilding(true);
    setProfileError(null);
    try {
      const rebuilt = await apiPost<UserStoryProfileRead>("/feedback/me/profile/rebuild", undefined, { token });
      setProfile(rebuilt);
    } catch (err) {
      setProfileError(err instanceof Error ? err.message : "Unable to rebuild profile");
    } finally {
      setRebuilding(false);
    }
  }

  async function handleUpgrade() {
    if (!token) {
      return;
    }

    setBillingActionLoading("checkout");
    setBillingActionError(null);
    try {
      const response = await apiPost<CheckoutSessionResponse>(
        "/billing/checkout",
        { price_key: "premium_monthly" },
        { token },
      );
      window.location.assign(response.checkout_url);
    } catch (err) {
      setBillingActionError(err instanceof Error ? err.message : "Unable to start checkout");
      setBillingActionLoading(null);
    }
  }

  async function handleManageBilling() {
    if (!token) {
      return;
    }

    setBillingActionLoading("portal");
    setBillingActionError(null);
    try {
      const response = await apiPost<BillingPortalResponse>("/billing/portal", undefined, { token });
      window.location.assign(response.portal_url);
    } catch (err) {
      setBillingActionError(err instanceof Error ? err.message : "Unable to open billing portal");
      setBillingActionLoading(null);
    }
  }

  async function handleSaveLanguagePreference() {
    if (!token) {
      return;
    }

    setLanguageSaving(true);
    setLanguageError(null);
    setLanguageMessage(null);
    try {
      await apiPatch("/users/me", { language: selectedLanguage }, { token });
      void trackLanguageChanged(selectedLanguage, {
        token,
        user,
        previousLanguage: locale,
        source: "profile_language_save",
      });
      setLocale(selectedLanguage);
      await refreshMe();
      setLanguageMessage(t("languageSaved"));
    } catch (err) {
      setLanguageError(err instanceof Error ? err.message : "Unable to update language preference");
    } finally {
      setLanguageSaving(false);
    }
  }

  if (isLoading || refreshing) {
    return <LoadingState message="Loading your profile..." />;
  }

  if (!isAuthenticated || !user) {
    return (
      <div className="space-y-4">
        <EmptyState
          title={t("profileUnavailableTitle")}
          description={t("profileUnavailableDescription")}
        />
        <div className="grid grid-cols-2 gap-3">
          <Link
            href="/login"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
          >
            {t("login")}
          </Link>
          <Link
            href="/register"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
          >
            {t("register")}
          </Link>
        </div>
      </div>
    );
  }

  const tier = billingStatus?.subscription_tier || subscription?.subscription_tier || user.subscription_tier;
  const status = billingStatus?.subscription_status || subscription?.subscription_status || user.subscription_status;
  const hasPremiumAccess = Boolean(
    billingStatus?.has_premium_access || subscription?.has_premium_access || user.is_admin,
  );
  const accessDate = billingStatus?.trial_ends_at || billingStatus?.subscription_expires_at;
  const hasBillingPortal = Boolean(
    billingStatus?.stripe_customer_id || user.subscription_status !== "none" || status !== "none",
  );
  const hasOpenBillingRecovery = Boolean(billingRecoveryPrompt?.has_open_recovery && billingRecoveryPrompt.case);

  return (
    <section className="space-y-4">
      <ProfileCard user={user} />
      {isEducator ? (
        <section className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#111827_0%,#1e1b4b_42%,#312e81_74%,#4338ca_100%)] p-6 text-white shadow-[0_24px_60px_rgba(30,41,59,0.18)]">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.12),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(251,191,36,0.16),transparent_26%)]" />
          <div className="relative">
          <h2 className="text-2xl font-semibold text-white">Educator tools</h2>
          <p className="mt-1 text-sm text-indigo-100">
            Manage teacher-friendly classroom reading sets separately from family bedtime collections.
          </p>
          <Link
            href="/educator"
            className="mt-4 inline-flex rounded-2xl border border-white/30 bg-white/20 px-4 py-3 text-sm font-medium text-white hover:bg-white/30"
          >
            Open educator workspace
          </Link>
          </div>
        </section>
      ) : null}
      <ContinueOnboardingCard />
      <BedtimePackSummaryCard loadLatest />
      <ReengagementList surface="profile" title="Helpful reminders" compact limit={2} />
      <WeeklyHighlightCard loadLatest compact />
      <BillingRecoveryBanner
        prompt={billingRecoveryPrompt}
        onAction={handleManageBilling}
        actionLoading={billingActionLoading === "portal"}
      />
      <section className="relative space-y-3 overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#0f172a_0%,#1d2457_45%,#302a6f_78%,#47377a_100%)] p-6 text-white shadow-[0_24px_60px_rgba(30,41,59,0.16)]">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,244,196,0.18),transparent_28%),radial-gradient(circle_at_18%_18%,rgba(129,140,248,0.2),transparent_30%)]" />
        <div className="relative">
        <div>
          <h2 className="text-2xl font-semibold text-white">Achievements</h2>
          <p className="mt-1 text-sm text-indigo-100">
            Keep an eye on gentle reading milestones for your family and child profiles.
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-2xl border border-white/25 bg-white/15 px-4 py-3">
            <p className="text-sm text-indigo-200">Earned</p>
            <p className="mt-1 text-2xl font-semibold text-white">
              {achievementDashboard?.earned_achievements.length || 0}
            </p>
          </div>
          <div className="rounded-2xl border border-white/25 bg-white/15 px-4 py-3">
            <p className="text-sm text-indigo-200">Current streak</p>
            <p className="mt-1 text-2xl font-semibold text-white">{achievementDashboard?.current_streak || 0}</p>
          </div>
          <div className="rounded-2xl border border-white/25 bg-white/15 px-4 py-3">
            <p className="text-sm text-indigo-200">Longest streak</p>
            <p className="mt-1 text-2xl font-semibold text-white">{achievementDashboard?.longest_streak || 0}</p>
          </div>
        </div>
        <Link
          href="/achievements"
          className="rounded-2xl border border-white/30 bg-white/20 px-4 py-3 text-center font-medium text-white hover:bg-white/30"
        >
          Open achievements
        </Link>
        </div>
      </section>
      <section className="relative space-y-3 overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#111827_0%,#1e1b4b_42%,#312e81_74%,#4338ca_100%)] p-6 text-white shadow-[0_24px_60px_rgba(30,41,59,0.16)]">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.12),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(251,191,36,0.16),transparent_26%)]" />
        <div className="relative">
        <div>
          <h2 className="text-2xl font-semibold text-white">Reading plans</h2>
          <p className="mt-1 text-sm text-indigo-100">
            Build a gentle rhythm for bedtime, narrated stories, or weekly family reading.
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3">
            <p className="text-sm text-indigo-200">Active plans</p>
            <p className="mt-1 text-2xl font-semibold text-white">{readingPlans.length}</p>
          </div>
          <div className="rounded-2xl border border-white/25 bg-white/15 px-4 py-3 sm:col-span-2">
            <p className="text-sm text-indigo-200">Current focus</p>
            <p className="mt-1 font-medium text-white">
              {readingPlans[0]?.title || "No active reading plan yet"}
            </p>
          </div>
        </div>
        <Link
          href="/reading-plans"
          className="rounded-2xl border border-white/30 bg-white/20 px-4 py-3 text-center font-medium text-white hover:bg-white/30"
        >
          Open reading plans
        </Link>
        </div>
      </section>
      <section className="space-y-4 rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">{t("subscriptionTitle")}</h2>
          <p className="mt-1 text-sm text-slate-600">{t("subscriptionDescription")}</p>
        </div>

        <dl className="grid gap-3 text-sm">
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <dt className="text-slate-500">{t("tier")}</dt>
            <dd className="mt-1 font-medium text-slate-900">{tier}</dd>
          </div>
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <dt className="text-slate-500">{t("status")}</dt>
            <dd className="mt-1 font-medium text-slate-900">{status}</dd>
          </div>
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <dt className="text-slate-500">{t("premiumAccess")}</dt>
            <dd className="mt-1 font-medium text-slate-900">{hasPremiumAccess ? t("active") : t("notActive")}</dd>
          </div>
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <dt className="text-slate-500">{billingStatus?.trial_ends_at ? t("trialEnds") : t("currentPeriodRenewal")}</dt>
            <dd className="mt-1 font-medium text-slate-900">
              {accessDate ? new Date(accessDate).toLocaleString() : t("noBillingDate")}
            </dd>
          </div>
        </dl>

        {billingQueryState === "success" ? (
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
            Billing update received. Your subscription status will refresh shortly.
          </div>
        ) : null}
        {billingQueryState === "cancel" ? (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
            Checkout was canceled. You can upgrade whenever you are ready.
          </div>
        ) : null}
        {billingActionError ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {billingActionError}
          </div>
        ) : null}
        {hasOpenBillingRecovery ? (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            {billingRecoveryPrompt?.message}
          </div>
        ) : null}
        {hasPremiumAccess || hasBillingPortal ? (
          <div className="grid gap-3 sm:grid-cols-2">
            <button
              type="button"
              onClick={handleManageBilling}
              disabled={billingActionLoading !== null}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 font-medium text-slate-900 disabled:opacity-60"
            >
              {billingActionLoading === "portal"
                ? "Opening portal..."
                : hasOpenBillingRecovery
                  ? (billingRecoveryPrompt?.action_label || "Update Billing")
                  : t("manageBilling")}
            </button>
          </div>
        ) : null}
        <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-600">
          Stripe billing is now wired for checkout and subscription management.
        </div>
      </section>
      {!hasPremiumAccess ? <PremiumUpgradeCard onUpgrade={handleUpgrade} loading={billingActionLoading === "checkout"} /> : null}
      <section className="space-y-4 rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">{t("profileLanguageTitle")}</h2>
          <p className="mt-1 text-sm text-slate-600">{t("profileLanguageDescription")}</p>
        </div>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">{t("languageLabel")}</span>
          <select
            value={selectedLanguage}
            onChange={(event) => setSelectedLanguage(normalizeLocale(event.target.value))}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
          >
            {SUPPORTED_LOCALES.map((option) => (
              <option key={option} value={option}>
                {LOCALE_LABELS[option]}
              </option>
            ))}
          </select>
        </label>
        {languageMessage ? (
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
            {languageMessage}
          </div>
        ) : null}
        {languageError ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {languageError}
          </div>
        ) : null}
        <button
          type="button"
          onClick={handleSaveLanguagePreference}
          disabled={languageSaving}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 font-medium text-slate-900 disabled:opacity-60"
        >
          {languageSaving ? t("savingLanguage") : t("saveLanguage")}
        </button>
      </section>
      <div className="rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#1e1b4b,#312e81,#4338ca)] px-4 py-3 text-sm text-indigo-50 shadow-[0_18px_45px_rgba(49,46,129,0.16)]">
        {t("recommendationsProfileNote")}
      </div>
      <section className="relative space-y-3 overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#0f172a_0%,#1d2457_45%,#302a6f_78%,#47377a_100%)] p-6 text-white shadow-[0_24px_60px_rgba(30,41,59,0.16)]">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,244,196,0.18),transparent_28%),radial-gradient(circle_at_18%_18%,rgba(129,140,248,0.2),transparent_30%)]" />
        <div className="relative">
        <div>
          <h2 className="text-2xl font-semibold text-white">Settings & Controls</h2>
          <p className="mt-1 text-sm text-indigo-100">
            Family controls, privacy, notifications, downloads, and app details now live in one settings hub for a cleaner mobile app structure.
          </p>
        </div>
        {privacyPreference ? (
          <div className="rounded-2xl border border-white/25 bg-white/15 px-4 py-3 text-sm text-indigo-50">
            Marketing emails: {privacyPreference.marketing_email_opt_in ? "On" : "Off"} • Recommendation personalization:{" "}
            {privacyPreference.allow_recommendation_personalization ? "On" : "Off"}
          </div>
        ) : null}
        <Link
          href="/settings"
          className="rounded-2xl border border-white/30 bg-white/20 px-4 py-3 text-center font-medium text-white hover:bg-white/30"
        >
          Open settings
        </Link>
        </div>
      </section>
      <section className="relative space-y-3 overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#111827_0%,#1e1b4b_42%,#312e81_74%,#4338ca_100%)] p-6 text-white shadow-[0_24px_60px_rgba(30,41,59,0.16)]">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.12),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(251,191,36,0.16),transparent_26%)]" />
        <div className="relative">
        <div>
          <h2 className="text-2xl font-semibold text-white">Growth & Gifts</h2>
          <p className="mt-1 text-sm text-indigo-100">
            Share Buddybug with another parent or create a premium gift code for a different family.
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          <Link
            href="/refer"
            className="rounded-2xl border border-white/30 bg-white/20 px-4 py-3 text-center font-medium text-white hover:bg-white/30"
          >
            Refer a Friend
          </Link>
          <Link
            href="/gifts"
            className="rounded-2xl border border-white/30 bg-white/20 px-4 py-3 text-center font-medium text-white hover:bg-white/30"
          >
            Gift Buddybug
          </Link>
          <Link
            href="/promo"
            className="rounded-2xl border border-white/30 bg-white/20 px-4 py-3 text-center font-medium text-white hover:bg-white/30"
          >
            Redeem Code
          </Link>
        </div>
        </div>
      </section>
      {profileLoading ? <LoadingState message="Loading preference profile..." /> : null}
      {profileError ? (
        <EmptyState title="Preference profile unavailable" description={profileError} />
      ) : (
        <PreferenceProfileCard
          profile={profile}
          rebuilding={rebuilding}
          onRebuild={handleRebuildProfile}
        />
      )}
      <div className="grid gap-3">
        <Link
          href="/saved"
          className="rounded-2xl border border-indigo-300 bg-indigo-600 px-4 py-3 text-center font-medium text-white shadow-md hover:bg-indigo-500"
        >
          Open saved library
        </Link>
        <Link
          href="/settings"
          className="rounded-2xl border border-indigo-300 bg-indigo-600 px-4 py-3 text-center font-medium text-white shadow-md hover:bg-indigo-500"
        >
          Open settings
        </Link>
        <Link
          href="/family-digest"
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
        >
          Open family digest
        </Link>
        <Link
          href="/bedtime-pack"
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
        >
          Open bedtime pack
        </Link>
        <Link
          href="/reading-plans"
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
        >
          Open reading plans
        </Link>
        <button
          type="button"
          onClick={logout}
          className="rounded-2xl border border-slate-300 bg-slate-700 px-4 py-3 font-medium text-white hover:bg-slate-600"
        >
          {t("logout")}
        </button>
        <Link
          href="/library"
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
        >
          {t("backToLibrary")}
        </Link>
      </div>
    </section>
  );
}
