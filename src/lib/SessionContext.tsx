"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { UserOut, api, getToken, clearToken } from "./api";
import { useRouter } from "next/navigation";

type SessionContextType = {
  user: UserOut | null;
  loading: boolean;
  loginSession: (user: UserOut) => void;
  logoutSession: () => Promise<void>;
  refreshUser: () => Promise<void>;
};

const SessionContext = createContext<SessionContextType | undefined>(undefined);

const USER_KEY = "parallax.user";

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    async function initSession() {
      if (typeof window === "undefined") return;

      const savedUser = sessionStorage.getItem(USER_KEY);
      const token = getToken();

      if (savedUser) {
        try {
          setUser(JSON.parse(savedUser));
        } catch {
          sessionStorage.removeItem(USER_KEY);
        }
      }

      if (token) {
        try {
          const fetchedUser = await api.getMe();
          sessionStorage.setItem(USER_KEY, JSON.stringify(fetchedUser));
          setUser(fetchedUser);
        } catch {
          clearToken();
          sessionStorage.removeItem(USER_KEY);
          setUser(null);
        }
      } else {
        sessionStorage.removeItem(USER_KEY);
        setUser(null);
      }
      setLoading(false);
    }

    initSession();
  }, []);

  const loginSession = (user: UserOut) => {
    sessionStorage.setItem(USER_KEY, JSON.stringify(user));
    setUser(user);
  };

  const logoutSession = async () => {
    try {
      await fetch("/api/session/logout", { method: "POST", credentials: "same-origin" });
    } finally {
      clearToken();
      sessionStorage.removeItem(USER_KEY);
      setUser(null);
      router.push("/");
    }
  };

  const refreshUser = async () => {
    try {
      const fetchedUser = await api.getMe();
      sessionStorage.setItem(USER_KEY, JSON.stringify(fetchedUser));
      setUser(fetchedUser);
    } catch {
      // ignore or handle
    }
  };

  return (
    <SessionContext.Provider
      value={{
        user,
        loading,
        loginSession,
        logoutSession,
        refreshUser,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error("useSession must be used within a SessionProvider");
  }
  return context;
}
