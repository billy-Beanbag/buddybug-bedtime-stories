"use client";

import { useParams } from "next/navigation";

import { DraftReviewEditor } from "@/components/admin/DraftReviewEditor";
import { useAuth } from "@/context/AuthContext";

export default function AdminDraftDetailPage() {
  const params = useParams<{ draftId: string }>();
  const { token } = useAuth();
  const draftId = Number(params.draftId);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Draft review detail</h2>
        <p className="mt-1 text-sm text-slate-600">
          Review, edit, approve, reject, or send this draft back for revision.
        </p>
      </div>
      <DraftReviewEditor draftId={draftId} token={token} />
    </div>
  );
}
