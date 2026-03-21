import type { ReactNode } from "react";

import { AdminGuard } from "@/components/admin/AdminGuard";
import { AdminShell } from "@/components/admin/AdminShell";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <AdminGuard>
      <AdminShell
        title="Internal Dashboard"
        description="Manage the Buddybug story pipeline from ideas through books and audio."
      >
        {children}
      </AdminShell>
    </AdminGuard>
  );
}
