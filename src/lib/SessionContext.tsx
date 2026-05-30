"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { UserOut, api, getToken, clearToken } from "./api";
import { useRouter } from "next/navigation";

type SessionContextType = {
  user: UserOut | null;
  loading: boolean;
  loginSession: (token: string, user: UserOut) => void;
  logoutSession: () => void;
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
        } catch (e) {
          sessionStorage.removeItem(USER_KEY);
        }
      }

      if (token) {
        try {
          const fetchedUser = await api.getMe();
          sessionStorage.setItem(USER_KEY, JSON.stringify(fetchedUser));
          setUser(fetchedUser);
        } catch (err) {
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

  const loginSession = (token: string, user: UserOut) => {
    sessionStorage.setItem(USER_KEY, JSON.stringify(user));
    setUser(user);
  };

  const logoutSession = () => {
    clearToken();
    sessionStorage.removeItem(USER_KEY);
    setUser(null);
    router.push("/");
  };

  const refreshUser = async () => {
    try {
      const fetchedUser = await api.getMe();
      sessionStorage.setItem(USER_KEY, JSON.stringify(fetchedUser));
      setUser(fetchedUser);
    } catch (err) {
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
