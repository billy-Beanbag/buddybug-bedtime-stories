import type { ReactNode } from "react";

export default function LoginLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-[calc(100vh-8rem)] flex-col items-center justify-center overflow-hidden">
      {children}
    </div>
  );
}
