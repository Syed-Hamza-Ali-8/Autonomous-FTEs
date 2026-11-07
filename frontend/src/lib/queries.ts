"use client";

import { useQuery } from "@tanstack/react-query";

import { apiGet, type ConversationOut, type CustomerProfile, type OrderDetail, type OrderStatus, type OrderSummary } from "@/lib/api";
import { useSignedIn } from "@/lib/auth";

// Every key starts with the user id, so two users can never share an entry (CLAUDE.md security rules).

export function useProfile() {
  const { userId, token } = useSignedIn();
  return useQuery({ queryKey: [userId, "me"], queryFn: () => apiGet<CustomerProfile>("/v1/me", token) });
}

export function useOrders(status: OrderStatus | null) {
  const { userId, token } = useSignedIn();
  const qs = status ? `?status=${encodeURIComponent(status)}` : "";
  return useQuery({
    queryKey: [userId, "orders", status ?? "all"],
    queryFn: () => apiGet<OrderSummary[]>(`/v1/orders${qs}`, token),
  });
}

export function useOrder(orderId: string) {
  const { userId, token } = useSignedIn();
  return useQuery({
    queryKey: [userId, "order", orderId],
    queryFn: () => apiGet<OrderDetail>(`/v1/orders/${encodeURIComponent(orderId)}`, token),
  });
}

export function useLatestConversation() {
  const { userId, token } = useSignedIn();
  return useQuery({
    queryKey: [userId, "conversation", "latest"],
    queryFn: () => apiGet<ConversationOut | null>("/v1/conversations/latest", token),
    staleTime: Infinity, // the chat keeps its own live state once loaded
  });
}
