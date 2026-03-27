import { prisma } from "@/lib/db";

const WINDOW_MS = 60 * 60 * 1000;
const MAX_SIGNUPS_PER_WINDOW = 5;

export async function enforceSignupRateLimit(key: string) {
  const now = new Date();
  const windowStart = new Date(now.getTime() - WINDOW_MS);

  await prisma.signupRateLimitEvent.deleteMany({
    where: {
      expiresAt: {
        lt: now,
      },
    },
  });

  const attempts = await prisma.signupRateLimitEvent.count({
    where: {
      key,
      createdAt: {
        gte: windowStart,
      },
    },
  });

  if (attempts >= MAX_SIGNUPS_PER_WINDOW) {
    const retryAt = new Date(now.getTime() + WINDOW_MS);
    const error = new Error("Too many signup attempts. Please try again later.");
    (error as Error & { retryAt?: string }).retryAt = retryAt.toISOString();
    throw error;
  }

  await prisma.signupRateLimitEvent.create({
    data: {
      key,
      expiresAt: new Date(now.getTime() + WINDOW_MS),
    },
  });
}
