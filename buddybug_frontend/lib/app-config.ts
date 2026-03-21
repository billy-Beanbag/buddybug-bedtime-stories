export const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || "Buddybug";
export const APP_ENV = process.env.NEXT_PUBLIC_APP_ENV || process.env.NODE_ENV || "development";
export const SUPPORT_EMAIL = process.env.NEXT_PUBLIC_SUPPORT_EMAIL || "support@buddybug.app";
export const APP_VERSION = process.env.NEXT_PUBLIC_APP_VERSION || "0.1.0-dev";

export const IS_WRAPPED_APP = process.env.NEXT_PUBLIC_IS_WRAPPED_APP === "true";
export const ENABLE_INSTALL_PROMPT = process.env.NEXT_PUBLIC_ENABLE_INSTALL_PROMPT
  ? process.env.NEXT_PUBLIC_ENABLE_INSTALL_PROMPT === "true"
  : !IS_WRAPPED_APP;
export const ENABLE_NATIVE_PLACEHOLDERS = process.env.NEXT_PUBLIC_ENABLE_NATIVE_PLACEHOLDERS === "true";

export function getAppRuntimeConfig() {
  return {
    appName: APP_NAME,
    environment: APP_ENV,
    supportEmail: SUPPORT_EMAIL,
    version: APP_VERSION,
    isWrappedApp: IS_WRAPPED_APP,
    enableInstallPrompt: ENABLE_INSTALL_PROMPT,
    enableNativePlaceholders: ENABLE_NATIVE_PLACEHOLDERS,
  };
}
