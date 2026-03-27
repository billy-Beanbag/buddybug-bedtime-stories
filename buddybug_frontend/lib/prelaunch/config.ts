const publicPrelaunchMode = process.env.NEXT_PUBLIC_PRELAUNCH_MODE === "true";
const PRELAUNCH_STAFF_ACCESS_KEY = process.env.PRELAUNCH_STAFF_ACCESS_KEY || "";

export const PRELAUNCH_MODE_ENABLED = publicPrelaunchMode;
export const APP_URL = (process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000").replace(/\/$/, "");
export const EMAIL_FROM = process.env.EMAIL_FROM || "Buddybug <stories@updates.buddybug.app>";
export const SUPPORT_EMAIL = process.env.SUPPORT_EMAIL || "support@buddybug.app";
export const STORY_TOKEN_TTL_DAYS = Number(process.env.STORY_TOKEN_TTL_DAYS || "365");
export const PRELAUNCH_STAFF_ACCESS_COOKIE = "buddybug_prelaunch_staff_access";

const PUBLIC_FILE_PATTERN = /\.[a-zA-Z0-9]+$/;

export function isPrelaunchModeEnabled() {
  return PRELAUNCH_MODE_ENABLED;
}

export function isPrelaunchPublicPath(pathname: string) {
  return pathname === "/" || pathname === "/privacy" || pathname === "/terms" || pathname.startsWith("/story/");
}

export function isAllowedPrelaunchPath(pathname: string) {
  if (!PRELAUNCH_MODE_ENABLED) {
    return true;
  }
  if (
    isPrelaunchPublicPath(pathname) ||
    pathname === "/access" ||
    pathname === "/access/exit" ||
    pathname === "/login" ||
    pathname.startsWith("/admin") ||
    pathname.startsWith("/api/signup") ||
    pathname.startsWith("/api/unsubscribe") ||
    pathname.startsWith("/api/cron/weekly-stories") ||
    pathname.startsWith("/_next/") ||
    pathname.startsWith("/icons/")
  ) {
    return true;
  }
  if (pathname === "/favicon.ico" || pathname === "/manifest.json" || pathname === "/robots.txt" || pathname === "/sitemap.xml") {
    return true;
  }
  return PUBLIC_FILE_PATTERN.test(pathname);
}

export function hasValidPrelaunchStaffAccess(cookieValue: string | undefined) {
  if (!PRELAUNCH_MODE_ENABLED || !PRELAUNCH_STAFF_ACCESS_KEY) {
    return false;
  }
  return cookieValue === PRELAUNCH_STAFF_ACCESS_KEY;
}

export function getPrelaunchStaffAccessCookieValue() {
  return PRELAUNCH_STAFF_ACCESS_KEY;
}
