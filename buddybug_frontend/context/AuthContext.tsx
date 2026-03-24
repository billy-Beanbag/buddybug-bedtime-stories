"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { apiGet, apiPost } from "@/lib/api";
import {
  clearStoredAuth,
  getStoredToken,
  getStoredUser,
  setStoredToken,
  setStoredUser,
} from "@/lib/auth";
import type { BillingStatusResponse, SubscriptionStatusRead, TokenResponse, User } from "@/lib/types";

interface LoginInput {
  email: string;
  password: string;
}

interface RegisterInput extends LoginInput {
  display_name?: string;
  country?: string;
  language?: string;
  accept_terms?: boolean;
  accept_privacy?: boolean;
  referral_code?: string;
}

interface AuthContextValue {
  user: User | null;
  token: string | null;
  subscription: SubscriptionStatusRead | null;
  billing: BillingStatusResponse | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isEditor: boolean;
  isEducator: boolean;
  hasPremiumAccess: boolean;
  isLoading: boolean;
  login: (input: LoginInput) => Promise<void>;
  register: (input: RegisterInput) => Promise<void>;
  logout: () => void;
  refreshMe: () => Promise<void>;
  refreshSubscription: () => Promise<void>;
  refreshBilling: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function persistAuth(token: string, user: User) {
  setStoredToken(token);
  setStoredUser(user);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionStatusRead | null>(null);
  const [billing, setBilling] = useState<BillingStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const clearAuth = useCallback(() => {
    clearStoredAuth();
    setToken(null);
    setUser(null);
    setSubscription(null);
    setBilling(null);
  }, []);

  const refreshSubscription = useCallback(async (activeToken: string) => {
    try {
      const currentSubscription = await apiGet<SubscriptionStatusRead>("/subscriptions/me", {
        token: activeToken,
        timeoutMs: 60_000,
      });
      setSubscription(currentSubscription);
    } catch {
      setSubscription(null);
    }
  }, []);

  const refreshSubscriptionState = useCallback(async () => {
    const activeToken = token || getStoredToken();
    if (!activeToken) {
      setSubscription(null);
      return;
    }
    await refreshSubscription(activeToken);
  }, [refreshSubscription, token]);

  const refreshBilling = useCallback(async (activeToken: string) => {
    try {
      const currentBilling = await apiGet<BillingStatusResponse>("/billing/me", {
        token: activeToken,
        timeoutMs: 60_000,
      });
      setBilling(currentBilling);
    } catch {
      setBilling(null);
    }
  }, []);

  const refreshBillingState = useCallback(async () => {
    const activeToken = token || getStoredToken();
    if (!activeToken) {
      setBilling(null);
      return;
    }
    await refreshBilling(activeToken);
  }, [refreshBilling, token]);

  const refreshMe = useCallback(async () => {
    const activeToken = token || getStoredToken();
    if (!activeToken) {
      clearAuth();
      return;
    }

    try {
      const currentUser = await apiGet<User>("/users/me", { token: activeToken, timeoutMs: 60_000 });
      persistAuth(activeToken, currentUser);
      setToken(activeToken);
      setUser(currentUser);
      await Promise.all([refreshSubscription(activeToken), refreshBilling(activeToken)]);
    } catch {
      clearAuth();
    }
  }, [clearAuth, refreshBilling, refreshSubscription, token]);

  useEffect(() => {
    const storedToken = getStoredToken();
    const storedUser = getStoredUser();
    if (storedToken) {
      setToken(storedToken);
    }
    if (storedUser) {
      setUser(storedUser);
    }

    if (storedToken) {
      const timeoutId = setTimeout(() => setIsLoading(false), 10000);
      void refreshMe()
        .catch(() => clearAuth())
        .finally(() => {
          clearTimeout(timeoutId);
          setIsLoading(false);
        });
      return;
    }

    setIsLoading(false);
  }, [refreshMe]);

  const handleAuthSuccess = useCallback(async (response: TokenResponse) => {
    persistAuth(response.access_token, response.user);
    setToken(response.access_token);
    setUser(response.user);
    await Promise.all([refreshSubscription(response.access_token), refreshBilling(response.access_token)]);
  }, [refreshBilling, refreshSubscription]);

  const login = useCallback(
    async (input: LoginInput) => {
      // Backend cold starts (e.g. Render) often exceed the default 15s client timeout.
      const response = await apiPost<TokenResponse>("/users/login", input, { timeoutMs: 180_000 });
      await handleAuthSuccess(response);
    },
    [handleAuthSuccess],
  );

  const register = useCallback(
    async (input: RegisterInput) => {
      const response = await apiPost<TokenResponse>("/users/register", {
        email: input.email,
        password: input.password,
        display_name: input.display_name || null,
        country: input.country || null,
        language: input.language || "en",
        accept_terms: input.accept_terms ?? true,
        accept_privacy: input.accept_privacy ?? true,
        referral_code: input.referral_code || null,
      }, { timeoutMs: 180_000 });
      await handleAuthSuccess(response);
    },
    [handleAuthSuccess],
  );

  const logout = useCallback(() => {
    clearAuth();
  }, [clearAuth]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      subscription,
      billing,
      isAuthenticated: Boolean(user && token),
      isAdmin: Boolean(user?.is_admin),
      isEditor: Boolean(user?.is_admin || user?.is_editor),
      isEducator: Boolean(user?.is_admin || user?.is_educator),
      hasPremiumAccess: Boolean(billing?.has_premium_access || subscription?.has_premium_access || user?.is_admin),
      isLoading,
      login,
      register,
      logout,
      refreshMe,
      refreshSubscription: refreshSubscriptionState,
      refreshBilling: refreshBillingState,
    }),
    [
      user,
      token,
      subscription,
      billing,
      isLoading,
      login,
      register,
      logout,
      refreshMe,
      refreshSubscriptionState,
      refreshBillingState,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
