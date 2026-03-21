import type { PublicStatusNoticeRead } from "@/lib/types";

const NOTICE_STYLE: Record<string, string> = {
  incident: "border-amber-200 bg-amber-50",
  maintenance: "border-sky-200 bg-sky-50",
  informational: "border-slate-200 bg-slate-50",
};

function formatStatusLabel(value: string) {
  return value.replaceAll("_", " ");
}

export function StatusNoticeList({
  title,
  description,
  notices,
  emptyTitle,
}: {
  title: string;
  description: string;
  notices: PublicStatusNoticeRead[];
  emptyTitle: string;
}) {
  return (
    <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">{title}</h2>
        <p className="mt-2 text-sm text-slate-600">{description}</p>
      </div>
      {notices.length ? (
        <div className="mt-5 space-y-4">
          {notices.map((notice) => (
            <article key={notice.id} className={`rounded-3xl border p-5 ${NOTICE_STYLE[notice.notice_type] || NOTICE_STYLE.informational}`}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">{notice.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-700">{notice.summary}</p>
                </div>
                <div className="text-right text-xs text-slate-500">
                  <div>{formatStatusLabel(notice.public_status)}</div>
                  <div className="mt-1">{new Date(notice.starts_at).toLocaleString()}</div>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <span className="rounded-full bg-white/80 px-3 py-1 text-xs font-medium text-slate-700">{notice.notice_type}</span>
                {notice.component_key ? (
                  <span className="rounded-full bg-white/80 px-3 py-1 text-xs font-medium text-slate-700">{notice.component_key}</span>
                ) : null}
                {notice.ends_at ? (
                  <span className="rounded-full bg-white/80 px-3 py-1 text-xs font-medium text-slate-700">
                    Ends {new Date(notice.ends_at).toLocaleString()}
                  </span>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="mt-5 rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-600">
          {emptyTitle}
        </div>
      )}
    </section>
  );
}
