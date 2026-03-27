"use client";

import { useMemo, useState } from "react";

type SignupFormProps = {
  formId: string;
  title?: string;
  compact?: boolean;
  attribution?: string | null;
};

type FieldErrors = Partial<Record<"parentEmail" | "childFirstName" | "childAge" | "consentToEmails", string>>;

const AGE_OPTIONS = Array.from({ length: 11 }, (_, index) => index + 2);

export function SignupForm({ formId, title = "Join the pre-launch list", compact = false, attribution = null }: SignupFormProps) {
  const [parentEmail, setParentEmail] = useState("");
  const [childFirstName, setChildFirstName] = useState("");
  const [childAge, setChildAge] = useState("4");
  const [consentToEmails, setConsentToEmails] = useState(false);
  const [website, setWebsite] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [wasSuccessful, setWasSuccessful] = useState(false);

  const cardClasses = useMemo(
    () =>
      compact
        ? "rounded-[2rem] border border-indigo-100 bg-white/90 p-6 shadow-[0_18px_45px_rgba(99,102,241,0.12)]"
        : "rounded-[2rem] border border-indigo-100 bg-white/95 p-6 shadow-[0_22px_60px_rgba(99,102,241,0.16)] sm:p-7",
    [compact],
  );

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setErrors({});
    setStatusMessage(null);

    const response = await fetch("/api/signup", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        parentEmail,
        childFirstName,
        childAge: Number(childAge),
        consentToEmails,
        marketingAttribution: attribution,
        website,
      }),
    });

    const data = (await response.json().catch(() => ({}))) as {
      message?: string;
      errors?: FieldErrors;
    };

    if (!response.ok) {
      setErrors(data.errors || {});
      setStatusMessage(data.message || "We could not save your signup just yet.");
      setSubmitting(false);
      return;
    }

    setWasSuccessful(true);
    setStatusMessage(data.message || "You are on the list.");
    setSubmitting(false);
    setParentEmail("");
    setChildFirstName("");
    setChildAge("4");
    setConsentToEmails(false);
    setWebsite("");
  }

  return (
    <form id={formId} onSubmit={handleSubmit} className={cardClasses} noValidate>
      <div className="mb-5">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-indigo-500">Buddybug pre-launch</p>
        <h2 className="mt-2 text-2xl font-semibold text-slate-950">{title}</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Tell us where to send a calming bedtime story each week, plus a personalised launch-day gift story later on.
        </p>
      </div>

      <div className="grid gap-4">
        <label className="grid gap-2 text-sm font-medium text-slate-800">
          Parent email
          <input
            type="email"
            autoComplete="email"
            value={parentEmail}
            onChange={(event) => setParentEmail(event.target.value)}
            aria-invalid={errors.parentEmail ? "true" : "false"}
            aria-describedby={errors.parentEmail ? `${formId}-parentEmail-error` : undefined}
            className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-950 outline-none transition focus:border-indigo-400 focus:bg-white"
            placeholder="parent@example.com"
            required
          />
          {errors.parentEmail ? (
            <span id={`${formId}-parentEmail-error`} className="text-sm text-rose-600">
              {errors.parentEmail}
            </span>
          ) : null}
        </label>

        <div className="grid gap-4 sm:grid-cols-[1.4fr_0.8fr]">
          <label className="grid gap-2 text-sm font-medium text-slate-800">
            Child first name
            <input
              type="text"
              autoComplete="off"
              value={childFirstName}
              onChange={(event) => setChildFirstName(event.target.value)}
              aria-invalid={errors.childFirstName ? "true" : "false"}
              aria-describedby={errors.childFirstName ? `${formId}-childFirstName-error` : undefined}
              className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-950 outline-none transition focus:border-indigo-400 focus:bg-white"
              placeholder="Daphne"
              required
            />
            {errors.childFirstName ? (
              <span id={`${formId}-childFirstName-error`} className="text-sm text-rose-600">
                {errors.childFirstName}
              </span>
            ) : null}
          </label>

          <label className="grid gap-2 text-sm font-medium text-slate-800">
            Child age
            <select
              value={childAge}
              onChange={(event) => setChildAge(event.target.value)}
              aria-invalid={errors.childAge ? "true" : "false"}
              aria-describedby={errors.childAge ? `${formId}-childAge-error` : undefined}
              className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-950 outline-none transition focus:border-indigo-400 focus:bg-white"
            >
              {AGE_OPTIONS.map((age) => (
                <option key={age} value={age}>
                  {age}
                </option>
              ))}
            </select>
            {errors.childAge ? (
              <span id={`${formId}-childAge-error`} className="text-sm text-rose-600">
                {errors.childAge}
              </span>
            ) : null}
          </label>
        </div>

        <label className="flex items-start gap-3 rounded-2xl border border-indigo-100 bg-indigo-50/70 px-4 py-3 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={consentToEmails}
            onChange={(event) => setConsentToEmails(event.target.checked)}
            className="mt-1 h-4 w-4 rounded border-slate-300 text-indigo-600"
            required
          />
          <span>
            I agree to receive one free bedtime story email each week from Buddybug during pre-launch, plus a personalised
            launch-day gift story for my child. I can unsubscribe any time.
          </span>
        </label>
        {errors.consentToEmails ? <p className="text-sm text-rose-600">{errors.consentToEmails}</p> : null}

        <label className="sr-only" aria-hidden="true">
          Leave this field empty
          <input type="text" tabIndex={-1} autoComplete="off" value={website} onChange={(event) => setWebsite(event.target.value)} />
        </label>

        <button
          type="submit"
          disabled={submitting}
          className="inline-flex items-center justify-center rounded-full bg-indigo-600 px-5 py-3 text-sm font-semibold text-white shadow-[0_14px_30px_rgba(79,70,229,0.28)] transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {submitting ? "Saving your signup..." : wasSuccessful ? "You're on the list" : "Get weekly bedtime stories"}
        </button>
      </div>

      {statusMessage ? (
        <p className={`mt-4 text-sm ${errors.parentEmail || errors.childFirstName || errors.childAge || errors.consentToEmails ? "text-rose-600" : "text-emerald-700"}`}>
          {statusMessage}
        </p>
      ) : null}
    </form>
  );
}
