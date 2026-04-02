import type { StoryMode } from "@/generated/prisma/client";

export type PrelaunchStoryPage = {
  pageNumber: number;
  heading?: string;
  text: string;
  imageUrl?: string | null;
  imageAlt?: string | null;
};

export type PrelaunchStoryBook = {
  slug: string;
  title: string;
  ageMin: number;
  ageMax: number;
  storyMode: StoryMode;
  coverImageUrl?: string | null;
  pages: PrelaunchStoryPage[];
};

export function buildContentHtmlFromPages(title: string, pages: PrelaunchStoryPage[]) {
  const pageHtml = pages
    .map((page) => {
      const heading = page.heading ? `<h2>${escapeHtml(page.heading)}</h2>` : "";
      return `<section>${heading}<p>${escapeHtml(page.text)}</p></section>`;
    })
    .join("");

  return `<h1>${escapeHtml(title)}</h1>${pageHtml}`;
}

export function parseStoryPages(value: unknown): PrelaunchStoryPage[] {
  if (!Array.isArray(value)) {
    return [];
  }

  const parsedPages: PrelaunchStoryPage[] = value
    .map<PrelaunchStoryPage | null>((item, index) => {
      if (!item || typeof item !== "object") {
        return null;
      }

      const record = item as Record<string, unknown>;
      const text = typeof record.text === "string" ? record.text.trim() : "";
      if (!text) {
        return null;
      }

      const pageNumberValue = typeof record.pageNumber === "number" ? record.pageNumber : index + 1;
      return {
        pageNumber: Number.isFinite(pageNumberValue) ? pageNumberValue : index + 1,
        heading: typeof record.heading === "string" ? record.heading : undefined,
        text,
        imageUrl: typeof record.imageUrl === "string" ? record.imageUrl : null,
        imageAlt: typeof record.imageAlt === "string" ? record.imageAlt : null,
      };
    })
    .filter((page): page is PrelaunchStoryPage => page !== null);

  return parsedPages.sort((left, right) => left.pageNumber - right.pageNumber);
}

function escapeHtml(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
