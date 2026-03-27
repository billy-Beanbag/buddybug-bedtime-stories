import { Resend } from "resend";

import { APP_URL, EMAIL_FROM } from "@/lib/prelaunch/config";

const resend = process.env.RESEND_API_KEY ? new Resend(process.env.RESEND_API_KEY) : null;

type DeliveryEmailInput = {
  parentEmail: string;
  childFirstName: string;
  storyTitle: string;
  secureToken: string;
  unsubscribeToken: string;
  deliveryType: "WELCOME" | "WEEKLY" | "LAUNCH_GIFT";
};

function buildSubject(input: DeliveryEmailInput) {
  if (input.deliveryType === "WELCOME") {
    return `A first Buddybug bedtime story for ${input.childFirstName}`;
  }
  if (input.deliveryType === "LAUNCH_GIFT") {
    return `A launch-day Buddybug gift story for ${input.childFirstName}`;
  }
  return `A new Buddybug bedtime story for ${input.childFirstName}`;
}

function escapeHtml(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function buildEmailHtml(input: DeliveryEmailInput) {
  const storyUrl = `${APP_URL}/story/${input.secureToken}`;
  const unsubscribeUrl = `${APP_URL}/api/unsubscribe?token=${input.unsubscribeToken}`;
  const previewLine =
    input.deliveryType === "WELCOME"
      ? "Thank you for joining Buddybug before launch. Your first calming story is ready tonight."
      : input.deliveryType === "LAUNCH_GIFT"
        ? "Buddybug is live, and your child has a special launch-day gift story waiting."
        : "A fresh bedtime story is ready to open whenever your evening settles down.";

  return `
    <html>
      <body style="margin:0;padding:32px 16px;background-color:#eef2ff;color:#1e1b4b;font-family:Arial,Helvetica,sans-serif;">
        <div style="max-width:620px;margin:0 auto;border-radius:28px;overflow:hidden;background:linear-gradient(180deg,#ffffff 0%,#eef2ff 100%);border:1px solid rgba(165,180,252,0.45);box-shadow:0 20px 45px rgba(79,70,229,0.12);">
          <div style="padding:40px 32px 20px;background:radial-gradient(circle at top, rgba(224,231,255,0.95), rgba(238,242,255,0.75));">
            <div style="font-size:13px;letter-spacing:0.16em;text-transform:uppercase;color:#6366f1;">Buddybug bedtime post</div>
            <h1 style="margin:16px 0 12px;font-size:34px;line-height:1.1;">${escapeHtml(buildSubject(input))}</h1>
            <p style="margin:0;font-size:17px;line-height:1.7;color:#4338ca;">${escapeHtml(previewLine)}</p>
          </div>
          <div style="padding:0 32px 32px;">
            <div style="margin-top:24px;padding:24px;border-radius:24px;background-color:#ffffff;border:1px solid rgba(196,181,253,0.55);">
              <h2 style="margin:0 0 10px;font-size:26px;">${escapeHtml(input.storyTitle)}</h2>
              <p style="margin:0 0 18px;font-size:16px;line-height:1.7;">Tonight's link opens a private Buddybug story page made just for quiet evenings with ${escapeHtml(input.childFirstName)}.</p>
              <a href="${storyUrl}" style="display:inline-block;border-radius:999px;padding:14px 22px;background-color:#4f46e5;color:#ffffff;text-decoration:none;font-weight:700;">Open tonight's story</a>
            </div>
            <p style="margin:24px 0 0;font-size:14px;line-height:1.7;color:#4b5563;">You're receiving this because you asked Buddybug to send calming bedtime stories by email during our pre-launch period.</p>
            <p style="margin:12px 0 0;font-size:14px;line-height:1.7;color:#4b5563;">If you'd like to stop receiving them, you can <a href="${unsubscribeUrl}" style="color:#4338ca;">unsubscribe here</a>.</p>
          </div>
        </div>
      </body>
    </html>
  `;
}

export async function sendStoryDeliveryEmail(input: DeliveryEmailInput) {
  if (!resend) {
    throw new Error("RESEND_API_KEY is not configured.");
  }

  const subject = buildSubject(input);
  const html = buildEmailHtml(input);

  const response = await resend.emails.send({
    from: EMAIL_FROM,
    to: input.parentEmail,
    subject,
    html,
  });

  return response.data?.id ?? null;
}
