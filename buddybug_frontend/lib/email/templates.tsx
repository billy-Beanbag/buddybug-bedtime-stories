import * as React from "react";

type StoryEmailTemplateProps = {
  childFirstName: string;
  storyTitle: string;
  storyUrl: string;
  unsubscribeUrl: string;
  previewLine: string;
  subjectLabel: string;
};

export function StoryEmailTemplate({
  childFirstName,
  storyTitle,
  storyUrl,
  unsubscribeUrl,
  previewLine,
  subjectLabel,
}: StoryEmailTemplateProps) {
  return (
    <html>
      <body
        style={{
          margin: 0,
          padding: "32px 16px",
          backgroundColor: "#eef2ff",
          color: "#1e1b4b",
          fontFamily: "Arial, Helvetica, sans-serif",
        }}
      >
        <div
          style={{
            maxWidth: "620px",
            margin: "0 auto",
            borderRadius: "28px",
            overflow: "hidden",
            background: "linear-gradient(180deg, #ffffff 0%, #eef2ff 100%)",
            border: "1px solid rgba(165, 180, 252, 0.45)",
            boxShadow: "0 20px 45px rgba(79, 70, 229, 0.12)",
          }}
        >
          <div
            style={{
              padding: "40px 32px 20px",
              background: "radial-gradient(circle at top, rgba(224, 231, 255, 0.95), rgba(238, 242, 255, 0.75))",
            }}
          >
            <div style={{ fontSize: "13px", letterSpacing: "0.16em", textTransform: "uppercase", color: "#6366f1" }}>
              Buddybug bedtime post
            </div>
            <h1 style={{ margin: "16px 0 12px", fontSize: "34px", lineHeight: 1.1 }}>{subjectLabel}</h1>
            <p style={{ margin: 0, fontSize: "17px", lineHeight: 1.7, color: "#4338ca" }}>{previewLine}</p>
          </div>
          <div style={{ padding: "0 32px 32px" }}>
            <div
              style={{
                marginTop: "24px",
                padding: "24px",
                borderRadius: "24px",
                backgroundColor: "#ffffff",
                border: "1px solid rgba(196, 181, 253, 0.55)",
              }}
            >
              <h2 style={{ margin: "0 0 10px", fontSize: "26px" }}>{storyTitle}</h2>
              <p style={{ margin: "0 0 18px", fontSize: "16px", lineHeight: 1.7 }}>
                Tonight&apos;s link opens a private Buddybug story page made just for quiet evenings with {childFirstName}.
              </p>
              <a
                href={storyUrl}
                style={{
                  display: "inline-block",
                  borderRadius: "999px",
                  padding: "14px 22px",
                  backgroundColor: "#4f46e5",
                  color: "#ffffff",
                  textDecoration: "none",
                  fontWeight: 700,
                }}
              >
                Open tonight&apos;s story
              </a>
            </div>
            <p style={{ margin: "24px 0 0", fontSize: "14px", lineHeight: 1.7, color: "#4b5563" }}>
              You&apos;re receiving this because you asked Buddybug to send calming bedtime stories by email during our
              pre-launch period.
            </p>
            <p style={{ margin: "12px 0 0", fontSize: "14px", lineHeight: 1.7, color: "#4b5563" }}>
              If you&apos;d like to stop receiving them, you can{" "}
              <a href={unsubscribeUrl} style={{ color: "#4338ca" }}>
                unsubscribe here
              </a>
              .
            </p>
          </div>
        </div>
      </body>
    </html>
  );
}
