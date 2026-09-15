import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

import * as authApi from "../services/authApi";
import { setAuthToken } from "../services/apiClient";
import type { AuthUser } from "../services/authApi";

const STORAGE_KEY = "mat.session";

interface StoredSession {
  accessToken: string;
  user: AuthUser;
}

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (employeeMailId: string, password: string, termsAccepted: boolean) => Promise<AuthUser>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function readStoredSession(): StoredSession | null {
  const raw = sessionStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredSession;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<StoredSession | null>(() => {
    const stored = readStoredSession();
    if (stored) {
      setAuthToken(stored.accessToken);
    }
    return stored;
  });

  const value = useMemo<AuthContextValue>(
    () => ({
      user: session?.user ?? null,
      isAuthenticated: session !== null,
      login: async (employeeMailId: string, password: string, termsAccepted: boolean) => {
        const response = await authApi.login(employeeMailId, password, termsAccepted);
        const nextSession: StoredSession = {
          accessToken: response.accessToken,
          user: response.user,
        };
        setAuthToken(nextSession.accessToken);
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(nextSession));
        setSession(nextSession);
        return response.user;
      },
      logout: () => {
        setAuthToken(null);
        sessionStorage.removeItem(STORAGE_KEY);
        setSession(null);
      },
    }),
    [session],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
