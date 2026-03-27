import { isPrelaunchModeEnabled } from "@/lib/prelaunch/config";

export default function TermsPage() {
  if (isPrelaunchModeEnabled()) {
    return (
      <section className="rounded-[2rem] border border-white/70 bg-white/90 p-6 shadow-sm sm:p-8">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-500">Terms</p>
        <h1 className="mt-3 text-3xl font-semibold text-slate-950">Buddybug pre-launch terms</h1>
        <div className="mt-4 space-y-4 text-sm leading-7 text-slate-600">
          <p>
            Buddybug pre-launch access is limited to the public landing page, signup form, unsubscribe flow, and private
            story links delivered by email.
          </p>
          <p>
            Story emails are offered as a free pre-launch experience and may change as the product evolves. We reserve the
            right to update, pause, or retire pre-launch content while we prepare the full launch.
          </p>
          <p>
            By subscribing, you confirm that you are the parent or guardian responsible for the email address provided and
            that you consent to receive weekly story emails until you unsubscribe.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm">
      <h1 className="text-3xl font-semibold text-slate-900">Terms of Service</h1>
      <p className="mt-3 text-sm leading-6 text-slate-600">
        This is a placeholder Buddybug Terms of Service page for the first privacy foundation release. It exists so
        legal acceptance can link to a stable in-app location while fuller policy content is prepared.
      </p>
    </section>
  );
}
