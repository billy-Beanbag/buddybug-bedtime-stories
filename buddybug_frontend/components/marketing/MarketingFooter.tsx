import Link from "next/link";

export function MarketingFooter() {
  return (
    <footer className="border-t border-indigo-100/70 bg-[rgba(255,255,255,0.88)] backdrop-blur">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 text-sm text-slate-600 sm:px-6 md:grid-cols-3">
        <div>
          <h2 className="text-base font-semibold text-slate-900">Buddybug</h2>
          <p className="mt-2 leading-6">
            A warm family storytelling app for illustrated bedtime reading, gentle narration, and calmer nightly
            routines.
          </p>
        </div>
        <div>
          <h3 className="font-semibold text-slate-900">Explore</h3>
          <div className="mt-3 grid gap-2">
            <Link href="/library" className="hover:text-slate-900">
              Library
            </Link>
            <Link href="/children" className="hover:text-slate-900">
              Children
            </Link>
            <Link href="/bedtime-pack" className="hover:text-slate-900">
              Bedtime Pack
            </Link>
            <Link href="/pricing" className="hover:text-slate-900">
              Pricing
            </Link>
          </div>
        </div>
        <div>
          <h3 className="font-semibold text-slate-900">Account</h3>
          <div className="mt-3 grid gap-2">
            <Link href="/login" className="hover:text-slate-900">
              Login
            </Link>
            <Link href="/register" className="hover:text-slate-900">
              Register
            </Link>
            <Link href="/status" className="hover:text-slate-900">
              Status
            </Link>
            <Link href="/privacy" className="hover:text-slate-900">
              Privacy
            </Link>
            <Link href="/support" className="hover:text-slate-900">
              Support
            </Link>
          </div>
        </div>
      </div>
      <div className="border-t border-indigo-100/70 px-4 py-4 text-center text-xs text-slate-500 sm:px-6">
        © 2026 Buddybug. Calm stories, child-friendly routines, and a gentler end to the day.
      </div>
    </footer>
  );
}
