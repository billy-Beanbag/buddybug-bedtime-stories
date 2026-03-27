import { DeliveryType, Prisma, SubscriberStatus } from "@/generated/prisma/client";

import { prisma } from "@/lib/db";
import { sendStoryDeliveryEmail } from "@/lib/email";
import { STORY_TOKEN_TTL_DAYS } from "@/lib/prelaunch/config";
import type { SignupInput } from "@/lib/prelaunch/validation";
import { generateSecureToken } from "@/lib/security";
import { pickRandomEligibleStory } from "@/lib/story-selection";

type PreparedDelivery =
  | { kind: "exhausted" }
  | {
      kind: "ready";
      delivery: Prisma.StoryDeliveryGetPayload<{
        include: {
          story: true;
          subscriber: true;
        };
      }>;
      created: boolean;
    };

function normalizeEmail(email: string) {
  return email.trim().toLowerCase();
}

function getExpiryDate() {
  if (STORY_TOKEN_TTL_DAYS <= 0) {
    return null;
  }
  return new Date(Date.now() + STORY_TOKEN_TTL_DAYS * 24 * 60 * 60 * 1000);
}

function getIsoWeekKey(date: Date) {
  const utcDate = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
  const day = utcDate.getUTCDay() || 7;
  utcDate.setUTCDate(utcDate.getUTCDate() + 4 - day);
  const yearStart = new Date(Date.UTC(utcDate.getUTCFullYear(), 0, 1));
  const week = Math.ceil((((utcDate.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);
  return `${utcDate.getUTCFullYear()}-W${String(week).padStart(2, "0")}`;
}

async function prepareDelivery(
  tx: Prisma.TransactionClient,
  subscriberId: string,
  deliveryType: DeliveryType,
  deliveryKey: string,
): Promise<PreparedDelivery> {
  const existing = await tx.storyDelivery.findUnique({
    where: { deliveryKey },
    include: {
      story: true,
      subscriber: true,
    },
  });

  if (existing) {
    return { kind: "ready", delivery: existing, created: false };
  }

  const subscriber = await tx.subscriber.findUnique({
    where: { id: subscriberId },
    select: {
      id: true,
      childAge: true,
    },
  });

  if (!subscriber) {
    throw new Error("Subscriber not found.");
  }

  const story = await pickRandomEligibleStory(tx, subscriber);
  if (!story) {
    await tx.subscriber.update({
      where: { id: subscriberId },
      data: {
        storyPoolExhaustedAt: new Date(),
      },
    });
    return { kind: "exhausted" };
  }

  let delivery: Prisma.StoryDeliveryGetPayload<{
    include: {
      story: true;
      subscriber: true;
    };
  }>;

  try {
    delivery = await tx.storyDelivery.create({
      data: {
        subscriberId,
        storyId: story.id,
        deliveryType,
        deliveryKey,
        secureToken: generateSecureToken(),
        expiresAt: getExpiryDate(),
      },
      include: {
        story: true,
        subscriber: true,
      },
    });
  } catch (error) {
    if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === "P2002") {
      const existingDelivery = await tx.storyDelivery.findUnique({
        where: { deliveryKey },
        include: {
          story: true,
          subscriber: true,
        },
      });
      if (existingDelivery) {
        return { kind: "ready", delivery: existingDelivery, created: false };
      }
    }
    throw error;
  }

  return { kind: "ready", delivery, created: true };
}

async function sendPreparedDelivery(
  delivery: Prisma.StoryDeliveryGetPayload<{
    include: {
      story: true;
      subscriber: true;
    };
  }>,
) {
  if (delivery.sentAt) {
    return delivery;
  }

  const emailMessageId = await sendStoryDeliveryEmail({
    parentEmail: delivery.subscriber.email,
    childFirstName: delivery.subscriber.childFirstName,
    storyTitle: delivery.story.title,
    secureToken: delivery.secureToken,
    unsubscribeToken: delivery.subscriber.unsubscribeToken,
    deliveryType: delivery.deliveryType,
  });

  return prisma.storyDelivery.update({
    where: { id: delivery.id },
    data: {
      sentAt: new Date(),
      emailMessageId,
    },
    include: {
      story: true,
      subscriber: true,
    },
  });
}

export async function createOrRefreshSubscriber(input: SignupInput) {
  const email = normalizeEmail(input.parentEmail);
  const subscriber = await prisma.subscriber.upsert({
    where: { email },
    update: {
      childFirstName: input.childFirstName.trim(),
      childAge: input.childAge,
      consentToEmails: true,
      marketingAttribution: input.marketingAttribution?.trim() || null,
      status: SubscriberStatus.ACTIVE,
      storyPoolExhaustedAt: null,
    },
    create: {
      email,
      childFirstName: input.childFirstName.trim(),
      childAge: input.childAge,
      consentToEmails: true,
      marketingAttribution: input.marketingAttribution?.trim() || null,
      status: SubscriberStatus.ACTIVE,
      unsubscribeToken: generateSecureToken(24),
    },
  });

  return subscriber;
}

export async function deliverWelcomeStory(subscriberId: string) {
  const prepared = await prisma.$transaction((tx) =>
    prepareDelivery(tx, subscriberId, DeliveryType.WELCOME, `welcome:${subscriberId}`),
  );

  if (prepared.kind === "exhausted") {
    return {
      status: "exhausted" as const,
      message: "You are signed up, but there are no active bedtime stories available for that age just yet.",
    };
  }

  await sendPreparedDelivery(prepared.delivery);
  return {
    status: prepared.created ? ("sent" as const) : ("existing" as const),
    deliveryId: prepared.delivery.id,
  };
}

export async function processWeeklyStoryCron(runAt = new Date()) {
  const subscribers = await prisma.subscriber.findMany({
    where: {
      status: SubscriberStatus.ACTIVE,
      consentToEmails: true,
      storyPoolExhaustedAt: null,
    },
    select: {
      id: true,
    },
  });

  const weekKey = getIsoWeekKey(runAt);
  const summary = {
    scanned: subscribers.length,
    sent: 0,
    exhausted: 0,
    skipped: 0,
    failed: 0,
  };

  for (const subscriber of subscribers) {
    try {
      const prepared = await prisma.$transaction((tx) =>
        prepareDelivery(tx, subscriber.id, DeliveryType.WEEKLY, `weekly:${weekKey}:${subscriber.id}`),
      );

      if (prepared.kind === "exhausted") {
        summary.exhausted += 1;
        console.info("[buddybug-cron] subscriber exhausted", { subscriberId: subscriber.id, weekKey });
        continue;
      }

      if (prepared.delivery.sentAt) {
        summary.skipped += 1;
        continue;
      }

      await sendPreparedDelivery(prepared.delivery);
      summary.sent += 1;
      console.info("[buddybug-cron] weekly story sent", {
        subscriberId: subscriber.id,
        deliveryId: prepared.delivery.id,
        weekKey,
      });
    } catch (error) {
      summary.failed += 1;
      console.error("[buddybug-cron] failed subscriber", { subscriberId: subscriber.id, error });
    }
  }

  return summary;
}

export async function getStoryDeliveryByToken(token: string) {
  return prisma.storyDelivery.findUnique({
    where: { secureToken: token },
    include: {
      story: true,
      subscriber: true,
    },
  });
}

export async function markStoryDeliveryOpened(deliveryId: string) {
  const existing = await prisma.storyDelivery.findUnique({
    where: { id: deliveryId },
    select: {
      openedAt: true,
    },
  });

  if (!existing || existing.openedAt) {
    return;
  }

  await prisma.storyDelivery.update({
    where: { id: deliveryId },
    data: {
      openedAt: new Date(),
    },
  });
}

export async function unsubscribeSubscriberByToken(token: string) {
  const subscriber = await prisma.subscriber.findUnique({
    where: { unsubscribeToken: token },
  });

  if (!subscriber) {
    return null;
  }

  return prisma.subscriber.update({
    where: { id: subscriber.id },
    data: {
      status: SubscriberStatus.UNSUBSCRIBED,
      consentToEmails: false,
    },
  });
}

export async function queueLaunchGiftForSubscriber(subscriberId: string) {
  return prisma.personalizedGift.create({
    data: {
      subscriberId,
    },
  });
}
