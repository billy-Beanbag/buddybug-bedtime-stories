"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const router = useRouter();
  const { isAdmin, isAuthenticated, isLoading, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      router.replace(isAdmin ? "/admin" : "/library");
    }
  }, [isAdmin, isAuthenticated, router]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await login({ email, password });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unable to log in";
      setError(
        email === "admin@buddybug.local" && msg.toLowerCase().includes("invalid")
          ? `${msg} Restart the backend and try again.`
          : msg,
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (isLoading) {
    return <LoadingState message="Checking your session..." />;
  }

  return (
    <section className="rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm overflow-hidden">
      <h2 className="text-2xl font-semibold text-slate-900">Login</h2>
      <p className="mt-2 text-sm text-slate-600">Use your Buddybug account to save progress and continue reading.</p>

      <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Email</span>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none ring-0 transition focus:border-indigo-400"
            placeholder="you@example.com"
            required
          />
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Password</span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none ring-0 transition focus:border-indigo-400"
            placeholder="Your password"
            required
          />
        </label>

        {error ? <p className="text-sm text-rose-600">{error}</p> : null}

        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => {
              setEmail("admin@buddybug.local");
              setPassword("Admin123!");
              setError(null);
            }}
            className="flex-1 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-medium text-slate-700"
          >
            Demo: Admin123!
          </button>
          <button
            type="button"
            onClick={() => {
              setEmail("admin@buddybug.local");
              setPassword("demo");
              setError(null);
            }}
            className="flex-1 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-medium text-slate-700"
          >
            Demo: demo
          </button>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-2xl bg-slate-900 px-4 py-3 font-medium text-white disabled:opacity-60"
        >
          {submitting ? "Logging in..." : "Login"}
        </button>
      </form>

      <p className="mt-4 text-sm text-slate-600">
        Need an account?{" "}
        <Link href="/register" className="font-medium text-indigo-700">
          Register
        </Link>
      </p>
    </section>
  );
}
