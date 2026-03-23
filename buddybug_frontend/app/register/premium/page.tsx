import { Suspense } from "react";
import { RegisterPageContent } from "@/components/register/RegisterPageContent";

export default function PremiumRegisterPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center">Loading...</div>}>
      <RegisterPageContent plan="premium" />
    </Suspense>
  );
}
