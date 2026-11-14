"use client";

import { useQueryClient } from "@tanstack/react-query";
import type { Session } from "@supabase/supabase-js";
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

import { supabase } from "@/lib/supabase";

type AuthState =
  | { status: "loading" }
  | { status: "signed_out" }
  | { status: "signed_in"; userId: string; token: string };

type AuthContextValue = AuthState & {
  signIn: (email: string, password: string) => Promise<{ error: string | null }>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function toState(session: Session | null): AuthState {
  return session ? { status: "signed_in", userId: session.user.id, token: session.access_token } : { status: "signed_out" };
}

/**
 * Session state from Supabase Auth. Per-user data lives only in the TanStack cache, keyed by user id,
 * and the whole cache is cleared on sign-out AND whenever the signed-in user changes, so nothing one
 * customer loaded can be shown to the next person on the same browser (CLAUDE.md security rules).
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [state, setState] = useState<AuthState>({ status: "loading" });
  const lastUser = useRef<string | null>(null);

  const apply = useCallback(
    (session: Session | null) => {
      const next = session?.user.id ?? null;
      if (next !== lastUser.current) {
        queryClient.clear();
        lastUser.current = next;
      }
      setState(toState(session));
    },
    [queryClient],
  );

  useEffect(() => {
    const auth = supabase().auth;
    void auth.getSession().then(({ data }) => apply(data.session));
    const { data } = auth.onAuthStateChange((_event, session) => apply(session));
    return () => data.subscription.unsubscribe();
  }, [apply]);

  const signIn = useCallback(async (email: string, password: string) => {
    const { error } = await supabase().auth.signInWithPassword({ email, password });
    return { error: error ? error.message : null };
  }, []);

  const signOut = useCallback(async () => {
    queryClient.clear();
    await supabase().auth.signOut();
  }, [queryClient]);

  return <AuthContext.Provider value={{ ...state, signIn, signOut }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}

/** The signed-in user's id and token, for query keys and API calls. Throws if used while signed out. */
export function useSignedIn(): { userId: string; token: string } {
  const auth = useAuth();
  if (auth.status !== "signed_in") throw new Error("useSignedIn requires a signed-in user");
  return { userId: auth.userId, token: auth.token };
}
