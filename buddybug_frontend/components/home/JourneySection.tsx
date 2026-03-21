import Link from "next/link";

const journeySteps = [
  {
    label: "Home",
    href: "/",
    description: "Begin with a clear, welcoming overview of Buddybug and tonight's options.",
  },
  {
    label: "Child Profile",
    href: "/children",
    description: "Choose who you're reading for so bedtime suggestions feel personal.",
  },
  {
    label: "Bedtime Pack",
    href: "/bedtime-pack",
    description: "Open a curated evening pack or select an individual story from the library.",
  },
  {
    label: "Reader",
    href: "/library",
    description: "Read together, follow the illustrations, or listen calmly with narration.",
  },
];

export function JourneySection() {
  return (
    <section className="rounded-[2.5rem] border border-white/70 bg-white/82 p-6 shadow-[0_18px_45px_rgba(15,23,42,0.06)] backdrop-blur sm:p-8">
      <div className="max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-indigo-700">Tonight's journey</p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
          See the product flow at a glance
        </h2>
        <p className="mt-3 text-base leading-7 text-slate-600">
          Buddybug is designed to feel easy to follow. The path from landing page to bedtime reading stays simple and
          visible.
        </p>
      </div>

      <div className="mt-8 grid gap-3 lg:grid-cols-[repeat(4,minmax(0,1fr))]">
        {journeySteps.map((step, index) => (
          <div key={step.label} className="flex flex-col gap-3 lg:flex-row lg:items-center">
            <Link
              href={step.href}
              className="group flex-1 rounded-[1.75rem] border border-indigo-100 bg-[linear-gradient(180deg,#ffffff,#f8f7ff)] p-5 transition hover:border-indigo-200 hover:shadow-sm"
            >
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">Step {index + 1}</p>
              <h3 className="mt-3 text-lg font-semibold text-slate-900 group-hover:text-indigo-700">{step.label}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">{step.description}</p>
            </Link>
            {index < journeySteps.length - 1 ? (
              <div className="flex items-center justify-center text-2xl text-indigo-300 lg:px-1">→</div>
            ) : null}
          </div>
        ))}
      </div>
    </section>
  );
}
