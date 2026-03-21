import type { SupportTicketRead } from "@/lib/types";

export function SupportTicketList({
  tickets,
  admin = false,
}: {
  tickets: SupportTicketRead[];
  admin?: boolean;
}) {
  if (!tickets.length) {
    return null;
  }

  return (
    <div className="grid gap-3">
      {tickets.map((ticket) => (
        <div
          key={ticket.id}
          className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="font-semibold text-slate-900">{ticket.subject}</h3>
              <p className="mt-1 text-sm text-slate-600">{ticket.category}</p>
            </div>
            <div className="flex flex-col items-end gap-2">
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">{ticket.status}</span>
              <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">{ticket.priority}</span>
            </div>
          </div>
          <p className="mt-3 line-clamp-2 text-sm text-slate-600">{ticket.message}</p>
          <p className="mt-3 text-xs text-slate-500">{new Date(ticket.updated_at).toLocaleString()}</p>
        </div>
      ))}
    </div>
  );
}
