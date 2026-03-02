import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from "react";
import { createElement } from "react";
import type { AuthState } from "@/types";

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [apiKey, setApiKey] = useState<string | null>(() => {
    return localStorage.getItem("api_key");
  });

  const isAuthenticated = apiKey !== null && apiKey.length > 0;

  const login = useCallback((key: string) => {
    localStorage.setItem("api_key", key);
    setApiKey(key);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("api_key");
    setApiKey(null);
  }, []);

  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === "api_key") {
        setApiKey(e.newValue);
      }
    };
    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  return createElement(
    AuthContext.Provider,
    { value: { apiKey, isAuthenticated, login, logout } },
    children
  );
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

export { AuthContext };
