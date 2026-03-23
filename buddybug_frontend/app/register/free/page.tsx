import { Suspense } from "react";
import { RegisterPageContent } from "@/components/register/RegisterPageContent";

export default function FreeRegisterPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center">Loading...</div>}>
      <RegisterPageContent plan="free" />
    </Suspense>
  );
}
