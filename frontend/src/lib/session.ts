"use client";

import { create } from "zustand";
import type { LocaleCode, Principal } from "./api";
import { fetchMe, getToken, setToken } from "./api";

type SessionState = {
  user: Principal | null;
  booting: boolean;
  locale: LocaleCode;
  setUser: (user: Principal | null) => void;
  setLocale: (locale: LocaleCode) => void;
  logout: () => void;
  bootstrap: () => Promise<void>;
};

export const useSession = create<SessionState>((set, get) => ({
  user: null,
  booting: true,
  locale: "en",
  setUser: (user) => set({ user, locale: user?.preferred_locale ?? "en" }),
  setLocale: (locale) => set({ locale }),
  logout: () => {
    setToken(null);
    set({ user: null });
  },
  bootstrap: async () => {
    if (!getToken()) {
      set({ user: null, booting: false });
      return;
    }
    try {
      const me = await fetchMe();
      set({ user: me, locale: me.preferred_locale, booting: false });
    } catch {
      setToken(null);
      set({ user: null, booting: false });
    }
  },
}));
