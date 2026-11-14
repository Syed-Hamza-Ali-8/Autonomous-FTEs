"use client";

import { createClient, type SupabaseClient } from "@supabase/supabase-js";

// Browser client for sign-in, sign-out and the session ONLY. All data goes through the FastAPI API;
// the frontend never queries the database (spec Section 2.1, invariant 21).
let client: SupabaseClient | null = null;

export function supabase(): SupabaseClient {
  if (client) return client;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) throw new Error("NEXT_PUBLIC_SUPABASE_URL / NEXT_PUBLIC_SUPABASE_ANON_KEY are not set");
  client = createClient(url, key, { auth: { persistSession: true, autoRefreshToken: true } });
  return client;
}
