import { Nunito } from "next/font/google";

import { resolveApiUrl } from "@/lib/api";
import type { ReaderBookDetail, ReaderPageRead } from "@/lib/types";

const storyReadingFont = Nunito({
  subsets: ["latin"],
  weight: ["500", "700"],
});

interface ReaderPageViewProps {
  book: ReaderBookDetail;
  page: ReaderPageRead;
}

export function ReaderPageView({ book, page }: ReaderPageViewProps) {
  const imageUrl = resolveApiUrl(page.image_url);
  const isCover = page.layout_type === "cover" || page.page_number === 0;

  if (isCover) {
    return (
      <section className="flex min-h-0 flex-col overflow-hidden rounded-[2rem] border border-white/70 bg-white/92 shadow-sm">
        {imageUrl ? (
          <div className="flex min-h-[220px] items-center justify-center bg-slate-100 sm:min-h-[260px] md:min-h-[340px]">
            <img
              src={imageUrl}
              alt={book.title}
              className="h-full w-full object-contain object-center"
            />
          </div>
        ) : (
          <div className="flex min-h-[220px] items-center justify-center bg-indigo-100 text-indigo-700 sm:min-h-[260px] md:min-h-[340px]">
            {book.title}
          </div>
        )}
        <div className="flex-1 p-6 text-center sm:p-7">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Cover</p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-900">{book.title}</h2>
        </div>
      </section>
    );
  }

  return (
    <section className="grid min-h-0 gap-3 rounded-[2rem] border border-white/70 bg-white/92 p-3 shadow-sm sm:p-4 md:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)] md:p-4">
      {imageUrl ? (
        <div className="min-h-0 overflow-hidden rounded-[1.5rem] bg-slate-100">
          <img
            src={imageUrl}
            alt={`Page ${page.page_number}`}
            className="min-h-[240px] w-full object-cover object-center sm:min-h-[300px] md:h-full md:min-h-[420px]"
          />
        </div>
      ) : (
        <div className="flex min-h-[240px] items-center justify-center rounded-[1.5rem] bg-slate-100 text-slate-500 sm:min-h-[300px] md:h-full md:min-h-[420px]">
          Illustration coming soon
        </div>
      )}

      {(page.layout_type === "text_image" ||
        page.layout_type === "text_only" ||
        page.layout_type === "cover") && (
        <article className="min-h-0 rounded-[1.5rem] bg-slate-50/85">
          <div className="h-full p-5 sm:p-6 md:min-h-[420px] md:p-7">
            <p
              className={`${storyReadingFont.className} whitespace-pre-wrap text-[18px] leading-8 text-slate-800 sm:text-[19px] sm:leading-9 md:text-[20px] md:leading-9`}
            >
              {page.text_content}
            </p>
          </div>
        </article>
      )}
    </section>
  );
}
