"use client";

import type { components } from "@/types/api";

export type Schemas = components["schemas"];
export type OrderSummary = Schemas["OrderSummary"];
export type OrderDetail = Schemas["OrderDetail"];
export type OrderStatus = OrderSummary["status"];
export type CustomerProfile = Schemas["CustomerProfile"];
export type ConversationOut = Schemas["ConversationOut"];
export type MessageOut = Schemas["MessageOut"];
export type ActionCard = Schemas["ActionCard"];
export type ActionRecord = Schemas["ActionRecord"];
// Staff console (spec 13.4). Tier C (reasons, codes, limits) appears ONLY in these types, never customer ones.
export type StaffProfile = Schemas["StaffProfile"];
export type ApprovalQueue = Schemas["ApprovalQueue"];
export type ApprovalItem = Schemas["ApprovalItem"];
export type ApprovalDetail = Schemas["ApprovalDetail"];
export type ChecklistItem = Schemas["ChecklistItem"];
export type Transcript = Schemas["Transcript"];
export type Dashboard = Schemas["Dashboard"];
export type AuditEntry = Schemas["AuditEntry"];
export type AuditPage = Schemas["AuditPage"];
export type DecisionOut = Schemas["DecisionOut"];
export type ChatEvent =
  | Schemas["TurnStarted"]
  | Schemas["Progress"]
  | Schemas["OrderRef"]
  | Schemas["Action"]
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

/** Typed POST (staff decisions). Never cached, never optimistic: the caller waits for this to resolve. */
export async function apiPost<T>(path: string, token: string, body: unknown): Promise<T> {
  const res = await fetch(apiUrl(path), {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as { error?: string };
    throw new ApiError(res.status, err.error ?? "error");
  }
  return (await res.json()) as T;
}
