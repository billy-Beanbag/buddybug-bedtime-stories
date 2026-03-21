import type { Metadata } from "next";

import { CTASection } from "@/components/marketing/CTASection";
import { FAQSection } from "@/components/marketing/FAQSection";
import { MarketingPageTracker } from "@/components/marketing/MarketingPageTracker";
import { faqItems } from "@/lib/marketing-content";

export const metadata: Metadata = {
  title: "Buddybug FAQ | Family Story App Questions",
  description: "Answers about Buddybug age range, child profiles, narrated stories, saved stories, languages, and parental controls.",
  openGraph: {
    title: "Buddybug FAQ",
    description: "Get clear answers about Buddybug for parents considering a bedtime story app for their family.",
  },
};

export default function FaqPage() {
  const faqJsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqItems.map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: item.answer,
      },
    })),
  };

  return (
    <div className="space-y-12 md:space-y-16">
      <MarketingPageTracker eventName="marketing_faq_viewed" source="marketing_faq" />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }} />
      <section className="rounded-[2.5rem] border border-white/70 bg-white/85 p-8 shadow-sm md:p-10">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-indigo-700">FAQ</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-900">Questions parents ask before trying Buddybug</h1>
        <p className="mt-4 max-w-3xl text-base leading-7 text-slate-600">
          These answers cover the basics of age range, Free Plan limits, Premium access, child profiles, and how Buddybug supports safer bedtime reading.
        </p>
      </section>

      <FAQSection items={faqItems} />

      <CTASection
        headline="Ready to see how Buddybug feels in real use?"
        description="Start on the Free Plan, explore Buddybug, and decide if Premium is right for your family."
        source="marketing_faq_footer"
      />
    </div>
  );
}
