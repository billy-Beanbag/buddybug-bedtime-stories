const steps = [
  {
    number: "01",
    title: "Choose your child's profile",
    description: "Pick the child profile you will be reading to, so suggestions, language, and reading progress stay personal.",
  },
  {
    number: "02",
    title: "Pick a story or bedtime pack",
    description: "Open a single illustrated story or let Buddybug gather a calm bedtime pack for the evening.",
  },
  {
    number: "03",
    title: "Read together or listen calmly",
    description: "Turn pages at your own pace or switch on narration for a softer wind-down at the end of the day.",
  },
];

export function HowItWorks() {
  return (
    <section className="space-y-6">
      <div className="max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-indigo-700">How Buddybug works</p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
          A gentle rhythm from choosing a story to saying goodnight
        </h2>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {steps.map((step) => (
          <article
            key={step.number}
            className="group relative overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#111827_0%,#1e1b4b_42%,#312e81_74%,#4338ca_100%)] p-6 text-white shadow-[0_24px_60px_rgba(30,41,59,0.18)]"
          >
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.12),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(251,191,36,0.16),transparent_26%)]" />
            <div className="pointer-events-none absolute right-4 top-4 h-16 w-16 rounded-full border border-white/10 bg-white/5 blur-2xl transition duration-500 group-hover:scale-110" />
            <div className="relative">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-100">{step.number}</p>
              <h3 className="mt-4 text-xl font-semibold text-white">{step.title}</h3>
              <p className="mt-3 text-sm leading-6 text-indigo-100">{step.description}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
