"use client";

import type { components } from "@/types/api";

export type Schemas = components["schemas"];
export type OrderSummary = Schemas["OrderSummary"];
export type OrderDetail = Schemas["OrderDetail"];
export type OrderStatus = OrderSummary["status"];
export type CustomerProfile = Schemas["CustomerProfile"];
export type ConversationOut = Schemas["ConversationOut"];
export type MessageOut = Schemas["MessageOut"];
export type ChatEvent =
  | Schemas["TurnStarted"]
  | Schemas["Progress"]
  | Schemas["OrderRef"]
  | Schemas["Reply"]
  | Schemas["ChatError"]
  | Schemas["Done"];

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
  ) {
    super(`API ${status}: ${code}`);
  }
}

export function apiUrl(path: string): string {
  const base = process.env.NEXT_PUBLIC_API_URL;
  if (!base) throw new Error("NEXT_PUBLIC_API_URL is not set");
  return `${base.replace(/\/$/, "")}${path}`;
}

/** Typed GET against the FastAPI API with the user's access token. Never cached (no-store). */
export async function apiGet<T>(path: string, token: string): Promise<T> {
  const res = await fetch(apiUrl(path), {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as { error?: string };
    throw new ApiError(res.status, body.error ?? "error");
  }
  return (await res.json()) as T;
}
