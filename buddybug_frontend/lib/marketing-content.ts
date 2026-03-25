export interface MarketingNavItem {
  href: string;
  label: string;
}

export interface MarketingFeature {
  icon: string;
  title: string;
  description: string;
}

export interface MarketingTestimonial {
  quote: string;
  name: string;
  context: string;
}

export interface MarketingPricingTier {
  name: string;
  priceLabel: string;
  description: string;
  features: string[];
  highlighted?: boolean;
  ctaKind: "start-free" | "upgrade";
}

export interface MarketingFaqItem {
  question: string;
  answer: string;
}

export const marketingNavItems: MarketingNavItem[] = [
  { href: "/", label: "Home" },
  { href: "/features", label: "Features" },
  { href: "/pricing", label: "Pricing" },
  { href: "/how-it-works", label: "How It Works" },
  { href: "/for-parents", label: "For Parents" },
  { href: "/faq", label: "FAQ" },
];

export const heroBullets = [
  "Illustrated, calming stories for ages 3-7",
  "Narrated playback for quiet bedtime listening",
  "Child profiles, parental controls, and daily picks",
];

export const featureCards: MarketingFeature[] = [
  {
    icon: "Moon",
    title: "Illustrated bedtime stories",
    description: "Soft, child-friendly storybooks designed to help families slow down and settle into bedtime.",
  },
  {
    icon: "Audio",
    title: "Narrated playback",
    description: "Read or listen together with audio-friendly stories and voice options for calmer evenings.",
  },
  {
    icon: "Profiles",
    title: "Child profiles",
    description: "Keep age bands, languages, reading progress, and preferences personalized for each child.",
  },
  {
    icon: "Shield",
    title: "Parental controls",
    description: "Bedtime mode, age-aware filtering, and family-safe defaults help keep story time gentle.",
  },
  {
    icon: "Sparkles",
    title: "Daily story suggestions",
    description: "Buddybug surfaces a thoughtful next story for tonight based on profile, language, and bedtime context.",
  },
  {
    icon: "Offline",
    title: "Saved library",
    description: "Save stories for later and keep family favorites organized inside your Buddybug account for quick repeat reads.",
  },
  {
    icon: "Globe",
    title: "Multilingual-ready",
    description: "English is ready today, with multilingual foundations in place for more families and markets.",
  },
  {
    icon: "Adventure",
    title: "Ready to grow with your family",
    description: "The platform already supports older 8-12 adventures as Buddybug expands beyond bedtime.",
  },
];

export const parentBenefits = [
  "Make bedtime feel calmer and more consistent",
  "Find age-appropriate stories without browsing stress",
  "Support more than one child from one account",
];

export const childBenefits = [
  "Gentle illustrations and warm story worlds",
  "Voices and read-aloud support for independent listening",
  "Story picks that feel made for their age and interests",
];

export const howItWorksSteps = [
  {
    step: "1",
    title: "Choose a child profile",
    description: "Set age band, language, and bedtime-safe defaults for the child you are reading with tonight.",
  },
  {
    step: "2",
    title: "Read or listen to a story",
    description: "Open a story, preview it for free, or listen with narrated playback when audio is available.",
  },
  {
    step: "3",
    title: "Let Buddybug suggest the next one",
    description: "Buddybug uses family-safe personalization to recommend another story that fits the moment.",
  },
];

export const pricingTiers: MarketingPricingTier[] = [
  {
    name: "Free Plan",
    priceLabel: "$0",
    description: "Create a free Buddybug account to start with a lighter weekly story plan.",
    features: [
      "3 stories per week",
      "Restricted access to a smaller library",
      "No narration voice",
      "1 child profile only",
      "No bedtime packs",
    ],
    ctaKind: "start-free",
  },
  {
    name: "Premium",
    priceLabel: "$9.99/mo",
    description: "Unlock the full Buddybug experience for families who want bedtime stories as part of a real routine.",
    features: [
      "Unlimited stories",
      "Full library access",
      "Bedtime packs",
      "Narration voices",
      "Saved library tools",
      "Unlimited child profiles",
      "Personalised recommendations",
    ],
    highlighted: true,
    ctaKind: "upgrade",
  },
];

export const testimonials: MarketingTestimonial[] = [
  {
    quote: "My daughter asks for Buddybug every night.",
    name: "Placeholder parent quote",
    context: "Bedtime routines",
  },
  {
    quote: "Bedtime feels calmer and easier now.",
    name: "Placeholder family quote",
    context: "Evening wind-down",
  },
  {
    quote: "The narrated stories are a lifesaver.",
    name: "Placeholder caregiver quote",
    context: "Busy parent moments",
  },
];

export const faqItems: MarketingFaqItem[] = [
  {
    question: "What age is Buddybug for?",
    answer: "Buddybug is currently positioned for families with children ages 3-7, with foundations already in place for 8-12 story adventures.",
  },
  {
    question: "Can I use Buddybug for more than one child?",
    answer: "The Free Plan includes 1 child profile. Premium unlocks unlimited child profiles with age band, language, progress, and bedtime-aware recommendations.",
  },
  {
    question: "Does Buddybug read stories aloud?",
    answer: "Premium includes narration voices. The Free Plan does not include narration voice access.",
  },
  {
    question: "Can I save stories for later?",
    answer: "Yes. Families can save stories and keep favorites organized in their Buddybug library for quick access later.",
  },
  {
    question: "Is there a free plan?",
    answer: "Yes. The Free Plan includes 3 stories per week, a smaller library, 1 child profile, and no bedtime packs or narration voice. All you need is a free Buddybug account.",
  },
  {
    question: "Can I change language?",
    answer: "Yes. Buddybug is built with multilingual support in mind, and language preferences can be set per account or child profile.",
  },
  {
    question: "Are there stories for older children?",
    answer: "Yes. Buddybug already supports 8-12 expansion lanes, with more older-child adventures ready to grow over time.",
  },
  {
    question: "How do parental controls work?",
    answer: "Parents can set safer defaults for bedtime mode, autoplay, age-band access, and premium voice visibility, with optional child-level overrides.",
  },
];

export const finalCta = {
  headline: "Make bedtime easier with Buddybug",
  description: "Start on the Free Plan with a Buddybug account, then upgrade to Premium whenever your family wants unlimited stories and full access.",
};
