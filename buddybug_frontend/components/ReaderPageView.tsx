import { resolveApiUrl } from "@/lib/api";
import type { ReaderBookDetail, ReaderPageRead } from "@/lib/types";

interface ReaderPageViewProps {
  book: ReaderBookDetail;
  page: ReaderPageRead;
}

export function ReaderPageView({ book, page }: ReaderPageViewProps) {
  const imageUrl = resolveApiUrl(page.image_url);
  const isCover = page.layout_type === "cover" || page.page_number === 0;

  if (isCover) {
    return (
      <section className="flex min-h-0 flex-col overflow-hidden rounded-[2rem] border border-white/70 bg-white/92 shadow-sm md:min-h-[calc(100vh-15.5rem)]">
        {imageUrl ? (
          <div className="flex h-[28vh] min-h-[180px] items-center justify-center bg-slate-100 sm:h-[30vh] md:h-[40vh] md:min-h-[280px]">
            <img
              src={imageUrl}
              alt={book.title}
              className="h-full w-full object-contain object-center"
            />
          </div>
        ) : (
          <div className="flex h-[28vh] min-h-[180px] items-center justify-center bg-indigo-100 text-indigo-700 sm:h-[30vh] md:h-[40vh] md:min-h-[280px]">
            {book.title}
          </div>
        )}
        <div className="flex-1 p-5 text-center sm:p-6">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Cover</p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-900">{book.title}</h2>
        </div>
      </section>
    );
  }

  return (
    <section className="grid min-h-0 gap-3 rounded-[2rem] border border-white/70 bg-white/92 p-3 shadow-sm sm:p-4 md:min-h-[calc(100vh-15.5rem)] md:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)] md:p-4">
      {imageUrl ? (
        <div className="min-h-0 overflow-hidden rounded-[1.5rem] bg-slate-100">
          <img
            src={imageUrl}
            alt={`Page ${page.page_number}`}
            className="h-[24vh] min-h-[170px] w-full object-cover object-center sm:h-[26vh] md:h-full md:min-h-[360px]"
          />
        </div>
      ) : (
        <div className="flex h-[24vh] min-h-[170px] items-center justify-center rounded-[1.5rem] bg-slate-100 text-slate-500 sm:h-[26vh] md:h-full md:min-h-[360px]">
          Illustration coming soon
        </div>
      )}

      {(page.layout_type === "text_image" ||
        page.layout_type === "text_only" ||
        page.layout_type === "cover") && (
        <article className="min-h-0 overflow-hidden rounded-[1.5rem] bg-slate-50/85">
          <div className="h-full max-h-[28vh] overflow-y-auto p-4 sm:max-h-[30vh] sm:p-5 md:max-h-none md:min-h-[360px] md:p-6">
            <p className="whitespace-pre-wrap text-[15px] leading-7 text-slate-800 sm:text-base">{page.text_content}</p>
          </div>
        </article>
      )}
    </section>
  );
}
