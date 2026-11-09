"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { type ActionCard, ApiError, type ChatEvent, type MessageOut, type OrderSummary } from "@/lib/api";
import { useSignedIn } from "@/lib/auth";
import { useLatestConversation } from "@/lib/queries";
import { streamChat } from "@/lib/sse";

export type ChatItem =
  | { kind: "customer"; key: string; text: string; at: string }
  | {
      kind: "assistant";
      key: string;
      text: string;
      at: string;
      steps: string[];
      orders: OrderSummary[];
      actions: ActionCard[];
    }
  | { kind: "system"; key: string; text: string; at: string };

export type ChatProblem = { message: string; retryText: string | null };

type Pending = { steps: string[]; orders: OrderSummary[]; actions: ActionCard[] };

function fromHistory(m: MessageOut): ChatItem {
  const key = `m${m.id}`;
  if (m.role === "customer") return { kind: "customer", key, text: m.content, at: m.created_at };
  if (m.role === "system") return { kind: "system", key, text: m.content, at: m.created_at };
  // order and action cards persisted with the message (built on the server from tool data and gateway
  // outcomes, never from the reply text)
  return { kind: "assistant", key, text: m.content, at: m.created_at, steps: [], orders: m.orders ?? [], actions: m.actions ?? [] };
}

/**
 * One customer's support chat. Progress steps and order cards arrive live; the reply text arrives
 * once, already claim-checked by the server (DECISIONS C1). Nothing here persists outside memory.
 */
export function useChat(orderContext: OrderSummary | null) {
  const { token } = useSignedIn();
  const latest = useLatestConversation();
  const [items, setItems] = useState<ChatItem[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [pending, setPending] = useState<Pending | null>(null);
  const [problem, setProblem] = useState<ChatProblem | null>(null);
  const abort = useRef<AbortController | null>(null);
  const seeded = useRef<string | null>(null);

  // Resume the latest conversation, unless the chat was opened for a different order:
  // then start fresh so the new conversation carries that order as context.
  useEffect(() => {
    if (!latest.isSuccess) return;
    const marker = `${orderContext?.id ?? ""}|${latest.data?.id ?? ""}`;
    if (seeded.current === marker) return;
    seeded.current = marker;
    const resume = latest.data && (orderContext === null || latest.data.order_id === orderContext.id);
    setItems(resume && latest.data ? latest.data.messages.map(fromHistory) : []);
    setConversationId(resume && latest.data ? latest.data.id : null);
    setProblem(null);
  }, [latest.isSuccess, latest.data, orderContext]);

  const streaming = pending !== null;

  const send = useCallback(
    async (raw: string) => {
      const text = raw.trim();
      if (!text || abort.current) return;
      const controller = new AbortController();
      abort.current = controller;
      setProblem(null);
      setItems((prev) => [...prev, { kind: "customer", key: crypto.randomUUID(), text, at: new Date().toISOString() }]);
      const live: Pending = { steps: [], orders: [], actions: [] };
      setPending({ ...live });
      try {
        const body = {
          client_message_id: crypto.randomUUID(),
          message: text,
          conversation_id: conversationId,
          order_id: conversationId ? null : (orderContext?.id ?? null),
        };
        for await (const ev of streamChat(body, token, controller.signal)) {
          handle(ev, live, text);
        }
      } catch (err) {
        if (controller.signal.aborted) {
          setItems((prev) => [...prev, { kind: "system", key: crypto.randomUUID(), text: "Stopped. Nothing was changed.", at: new Date().toISOString() }]);
        } else if (err instanceof ApiError && err.status === 404) {
          setConversationId(null); // the conversation is gone; the next message starts a new one
          setProblem({ message: "This conversation is no longer available. Send your message again to start a new one.", retryText: text });
        } else if (err instanceof ApiError && err.status === 401) {
          setProblem({ message: "Your session has ended. Sign in again to keep chatting.", retryText: null });
        } else {
          setProblem({ message: "The message didn't go through. Check your connection and try again.", retryText: text });
        }
      } finally {
        abort.current = null;
        setPending(null);
      }

      function handle(ev: ChatEvent, acc: Pending, sent: string) {
        switch (ev.type) {
          case "turn_started":
            setConversationId(ev.conversation_id);
            break;
          case "progress":
            acc.steps.push(ev.label);
            setPending({ steps: [...acc.steps], orders: [...acc.orders], actions: [...acc.actions] });
            break;
          case "order_ref":
            acc.orders.push(ev.order);
            setPending({ steps: [...acc.steps], orders: [...acc.orders], actions: [...acc.actions] });
            break;
          case "action":
            // Shown as soon as the gateway decides: it is a fact, not model text (C1).
            acc.actions.push(ev.card);
            setPending({ steps: [...acc.steps], orders: [...acc.orders], actions: [...acc.actions] });
            break;
          case "reply":
            setItems((prev) => [
              ...prev,
              { kind: "assistant", key: `m${ev.message_id}`, text: ev.text, at: ev.created_at, steps: [...acc.steps], orders: [...acc.orders], actions: [...acc.actions] },
            ]);
            break;
          case "error":
            setProblem({
              message: ev.message,
              retryText: ev.code === "duplicate_in_progress" ? null : sent,
            });
            break;
          case "done":
            break;
        }
      }
    },
    [conversationId, orderContext, token],
  );

  const stop = useCallback(() => abort.current?.abort(), []);

  return {
    items,
    pending,
    problem,
    streaming,
    loading: latest.isPending,
    loadError: latest.isError,
    reload: () => void latest.refetch(),
    send,
    stop,
  };
}
