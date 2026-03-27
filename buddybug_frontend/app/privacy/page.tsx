import { PrivacyDashboardPage } from "@/components/privacy/PrivacyDashboardPage";
import { isPrelaunchModeEnabled } from "@/lib/prelaunch/config";

export default function PrivacyPage() {
  if (isPrelaunchModeEnabled()) {
    return (
      <section className="rounded-[2rem] border border-white/70 bg-white/90 p-6 shadow-sm sm:p-8">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-500">Privacy</p>
        <h1 className="mt-3 text-3xl font-semibold text-slate-950">Buddybug pre-launch privacy notice</h1>
        <div className="mt-4 space-y-4 text-sm leading-7 text-slate-600">
          <p>
            During pre-launch, Buddybug only collects the information needed to send bedtime stories by email: parent email
            address, child first name, child age, consent to receive emails, and optional marketing attribution.
          </p>
          <p>
            We do not create public profiles, public libraries, or visible subscriber dashboards. Story links are private,
            token-based links sent directly by email.
          </p>
          <p>
            You can unsubscribe at any time from any email we send. If you contact us for data questions, we will work from
            the email address used to subscribe.
          </p>
        </div>
      </section>
    );
  }

  return <PrivacyDashboardPage />;
}
