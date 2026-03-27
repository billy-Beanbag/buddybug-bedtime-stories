import type { Prisma, Story, Subscriber } from "@/generated/prisma/client";

export async function pickRandomEligibleStory(
  tx: Prisma.TransactionClient,
  subscriber: Pick<Subscriber, "id" | "childAge">,
): Promise<Story | null> {
  const candidates = await tx.story.findMany({
    where: {
      isActive: true,
      ageMin: {
        lte: subscriber.childAge,
      },
      ageMax: {
        gte: subscriber.childAge,
      },
      deliveries: {
        none: {
          subscriberId: subscriber.id,
        },
      },
    },
    select: {
      id: true,
      slug: true,
      title: true,
      ageMin: true,
      ageMax: true,
      contentHtml: true,
      contentJson: true,
      pdfUrl: true,
      isActive: true,
      createdAt: true,
      updatedAt: true,
    },
  });

  if (!candidates.length) {
    return null;
  }

  const randomIndex = Math.floor(Math.random() * candidates.length);
  return candidates[randomIndex] ?? null;
}
