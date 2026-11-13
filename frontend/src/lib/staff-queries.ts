"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  type ApprovalDetail,
  type ApprovalQueue,
  type AuditPage,
  type DecisionOut,
  type StaffProfile,
  type Transcript,
  apiGet,
  apiPost,
} from "@/lib/api";
import { useSignedIn } from "@/lib/auth";

// Staff data, fetched with the signed-in user's token. Every key starts with the user id (CLAUDE.md security
// rules), and the whole cache is cleared on sign-out or user change (lib/auth.tsx).

export function useStaffProfile() {
  const { userId, token } = useSignedIn();
  return useQuery({
    queryKey: [userId, "staff", "me"],
    queryFn: () => apiGet<StaffProfile>("/v1/staff/me", token),
    retry: false,
  });
}

/** The pending queue. Polls, so new requests and expiries (J8) show without a reload. */
export function useApprovalQueue() {
  const { userId, token } = useSignedIn();
  return useQuery({
    queryKey: [userId, "staff", "approvals"],
    queryFn: () => apiGet<ApprovalQueue>("/v1/staff/approvals", token),
    refetchInterval: 15_000,
  });
}

export function useApprovalDetail(reference: string | null) {
  const { userId, token } = useSignedIn();
  return useQuery({
    queryKey: [userId, "staff", "approval", reference],
    queryFn: () => apiGet<ApprovalDetail>(`/v1/staff/approvals/${encodeURIComponent(reference!)}`, token),
    enabled: reference !== null,
  });
}

export function useConversation(id: string | null) {
  const { userId, token } = useSignedIn();
  return useQuery({
    queryKey: [userId, "staff", "conversation", id],
    queryFn: () => apiGet<Transcript>(`/v1/staff/conversations/${encodeURIComponent(id!)}`, token),
    enabled: id !== null,
  });
}

export type AuditFilters = {
  decision: "ALLOW" | "NEEDS_APPROVAL" | "DENY" | null;
  action: string | null;
  customer: string;
  from: string; // yyyy-mm-dd, UTC day start
  to: string; // yyyy-mm-dd, inclusive
  page: number;
};

export const PAGE_SIZE = 25;

export function auditQuery(f: AuditFilters): string {
  const qs = new URLSearchParams({ page: String(f.page), page_size: String(PAGE_SIZE) });
  if (f.decision) qs.set("decision", f.decision);
  if (f.action) qs.set("action", f.action);
  if (f.customer.trim()) qs.set("customer", f.customer.trim().toUpperCase());
  if (f.from) qs.set("from", `${f.from}T00:00:00Z`);
  if (f.to) {
    const end = new Date(`${f.to}T00:00:00Z`);
    end.setUTCDate(end.getUTCDate() + 1); // the "to" day is included
    qs.set("to", end.toISOString());
  }
  return qs.toString();
}

export function useAudit(filters: AuditFilters) {
  const { userId, token } = useSignedIn();
  const qs = auditQuery(filters);
  return useQuery({
    queryKey: [userId, "staff", "audit", qs],
    queryFn: () => apiGet<AuditPage>(`/v1/staff/audit?${qs}`, token),
    placeholderData: (previous) => previous,
  });
}

type Decide =
  | { kind: "approve"; reference: string; amount_cents: number | null; currency: "USD" | "PKR" | null }
  | { kind: "reject"; reference: string; note: string };

/** Approve or reject. Not optimistic (spec 13.4): the UI changes only after the server confirms. */
export function useDecide() {
  const { userId, token } = useSignedIn();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (d: Decide) =>
      d.kind === "approve"
        ? apiPost<DecisionOut>(`/v1/staff/approvals/${encodeURIComponent(d.reference)}/approve`, token, {
            amount_cents: d.amount_cents,
            currency: d.currency,
          })
        : apiPost<DecisionOut>(`/v1/staff/approvals/${encodeURIComponent(d.reference)}/reject`, token, { note: d.note }),
    onSettled: () => queryClient.invalidateQueries({ queryKey: [userId, "staff"] }),
  });
}
