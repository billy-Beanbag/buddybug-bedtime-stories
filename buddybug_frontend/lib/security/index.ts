import { createHash, randomBytes } from "crypto";

export function generateSecureToken(bytes = 32) {
  return randomBytes(bytes).toString("hex");
}

export function sha256(value: string) {
  return createHash("sha256").update(value).digest("hex");
}

export function safeCompareBearerToken(headerValue: string | null, expectedSecret: string) {
  if (!headerValue) {
    return false;
  }
  return headerValue === `Bearer ${expectedSecret}`;
}
