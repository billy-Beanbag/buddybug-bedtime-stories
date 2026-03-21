import type { User } from "@/lib/types";

const AUTH_TOKEN_KEY = "buddybug.auth.token";
const AUTH_USER_KEY = "buddybug.auth.user";
const GUEST_READER_KEY = "buddybug.reader.guest";

function canUseStorage() {
  return typeof window !== "undefined";
}

export function getStoredToken(): string | null {
  if (!canUseStorage()) {
    return null;
  }
  return window.localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setStoredToken(token: string) {
  if (canUseStorage()) {
    window.localStorage.setItem(AUTH_TOKEN_KEY, token);
  }
}

export function clearStoredToken() {
  if (canUseStorage()) {
    window.localStorage.removeItem(AUTH_TOKEN_KEY);
  }
}

export function getStoredUser(): User | null {
  if (!canUseStorage()) {
    return null;
  }

  const raw = window.localStorage.getItem(AUTH_USER_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as User;
  } catch {
    clearStoredUser();
    return null;
  }
}

export function setStoredUser(user: User) {
  if (canUseStorage()) {
    window.localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
  }
}

export function clearStoredUser() {
  if (canUseStorage()) {
    window.localStorage.removeItem(AUTH_USER_KEY);
  }
}

function createGuestReaderIdentifier() {
  const random = Math.random().toString(36).slice(2, 10);
  return `guest:${random}`;
}

export function getGuestReaderIdentifier(): string {
  if (!canUseStorage()) {
    return "guest:server";
  }

  const stored = window.localStorage.getItem(GUEST_READER_KEY);
  if (stored) {
    return stored;
  }

  const guestId = createGuestReaderIdentifier();
  window.localStorage.setItem(GUEST_READER_KEY, guestId);
  return guestId;
}

export function getReaderIdentifier(user?: User | null): string {
  if (user?.id) {
    return `user:${user.id}`;
  }
  return getGuestReaderIdentifier();
}

export function clearStoredAuth() {
  clearStoredToken();
  clearStoredUser();
}
