"use client";

const ONBOARDING_STEPS = [
  { key: "welcome", label: "Welcome" },
  { key: "child_setup", label: "Child" },
  { key: "preferences", label: "Preferences" },
  { key: "bedtime_mode", label: "Bedtime" },
  { key: "first_story", label: "First story" },
] as const;

function getActiveIndex(currentStep: string) {
  const index = ONBOARDING_STEPS.findIndex((step) => step.key === currentStep);
  return index >= 0 ? index : 0;
}

export function OnboardingProgress({ currentStep }: { currentStep: string }) {
  const activeIndex = getActiveIndex(currentStep);
  const activeStep = ONBOARDING_STEPS[activeIndex] ?? ONBOARDING_STEPS[0];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-xs font-medium uppercase tracking-[0.16em] text-indigo-100">
        <span>Setup progress</span>
        <span>
          {Math.min(activeIndex + 1, ONBOARDING_STEPS.length)} / {ONBOARDING_STEPS.length}
        </span>
      </div>
      <div className="grid grid-cols-5 gap-2">
        {ONBOARDING_STEPS.map((step, index) => (
          <div key={step.key} className="space-y-2">
            <div
              className={`h-2 rounded-full transition ${
                index <= activeIndex ? "bg-white shadow-[0_0_18px_rgba(255,255,255,0.45)]" : "bg-white/20"
              }`}
            />
          </div>
        ))}
      </div>
      <p className="text-xs font-medium uppercase tracking-[0.14em] text-indigo-100">Current step: {activeStep.label}</p>
    </div>
  );
}
