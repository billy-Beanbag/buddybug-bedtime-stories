"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { useAuth } from "@/context/AuthContext";
import {
  DEFAULT_LOCALE,
  LOCALE_STORAGE_KEY,
  detectBrowserLocale,
  normalizeLocale,
  translate,
  type Locale,
  type TranslationKey,
} from "@/lib/i18n";

interface LocaleContextValue {
  locale: Locale;
  setLocale: (locale: string) => void;
  t: (key: TranslationKey) => string;
}

const LocaleContext = createContext<LocaleContextValue | undefined>(undefined);

function getStoredLocale(): Locale | null {
  if (typeof window === "undefined") {
    return null;
  }
  const stored = window.localStorage.getItem(LOCALE_STORAGE_KEY);
  return stored ? normalizeLocale(stored) : null;
}

export function LocaleProvider({ children }: { children: ReactNode }) {
  const { user, isAuthenticated } = useAuth();
  const [locale, setLocaleState] = useState<Locale>(DEFAULT_LOCALE);

  useEffect(() => {
    if (isAuthenticated && user?.language) {
      const preferred = normalizeLocale(user.language);
      setLocaleState(preferred);
      if (typeof window !== "undefined") {
        window.localStorage.setItem(LOCALE_STORAGE_KEY, preferred);
      }
      return;
    }

    const storedLocale = getStoredLocale();
    if (storedLocale) {
      setLocaleState(storedLocale);
      return;
    }

    const browserLocale = detectBrowserLocale();
    setLocaleState(browserLocale);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(LOCALE_STORAGE_KEY, browserLocale);
    }
  }, [isAuthenticated, user?.language]);

  const setLocale = (value: string) => {
    const nextLocale = normalizeLocale(value);
    setLocaleState(nextLocale);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(LOCALE_STORAGE_KEY, nextLocale);
    }
  };

  const value = useMemo<LocaleContextValue>(
    () => ({
      locale,
      setLocale,
      t: (key) => translate(locale, key),
    }),
    [locale],
  );

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

export function useLocale() {
  const context = useContext(LocaleContext);
  if (!context) {
    throw new Error("useLocale must be used within LocaleProvider");
  }
  return context;
}
