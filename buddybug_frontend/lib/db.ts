import { PrismaPg } from "@prisma/adapter-pg";

import { PrismaClient } from "@/generated/prisma/client";

declare global {
  var __buddybugPrisma: PrismaClient | undefined;
}

const connectionString =
  process.env.DATABASE_URL || process.env.DIRECT_URL || "postgresql://postgres:postgres@127.0.0.1:5432/buddybug";

const adapter = new PrismaPg({
  connectionString,
});

export const prisma =
  global.__buddybugPrisma ??
  new PrismaClient({
    adapter,
    log: process.env.NODE_ENV === "development" ? ["warn", "error"] : ["error"],
  });

if (process.env.NODE_ENV !== "production") {
  global.__buddybugPrisma = prisma;
}
