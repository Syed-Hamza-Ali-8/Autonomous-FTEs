"use client";

import { ArrowUp, Check, Headset, RotateCw, Square } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { ActionCard } from "@/components/chat/action-card";
import { suggestionsFor } from "@/components/chat/suggestions";
import type { ChatItem, useChat } from "@/components/chat/use-chat";
import { StatusBadge } from "@/components/store/status";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import type { ActionCard as ActionCardData, OrderSummary } from "@/lib/api";
import { formatMoney, formatTime } from "@/lib/format";
import { cn } from "@/lib/utils";

type Chat = ReturnType<typeof useChat>;

export function ChatPanel({
  chat,
  orderContext = null,
  autoFocus = false,
}: {
  chat: Chat;
  orderContext?: OrderSummary | null;
  autoFocus?: boolean;
}) {
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => {
    end.current?.scrollIntoView({ block: "end" });
  }, [chat.items.length, chat.pending?.steps.length, chat.pending?.orders.length, chat.pending?.actions.length, chat.problem]);

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {orderContext && (
        <div className="border-b px-4 py-3">
          <OrderCard order={orderContext} />
        </div>
      )}
      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-4" aria-live="polite" aria-relevant="additions">
        {chat.loading ? (
          <div className="flex flex-col gap-3" aria-label="Loading conversation">
            <Skeleton className="h-10 w-3/4" />
            <Skeleton className="ml-auto h-10 w-1/2" />
            <Skeleton className="h-16 w-4/5" />
          </div>
        ) : chat.loadError ? (
          <div className="flex flex-col items-start gap-3 text-sm">
            <p>Your earlier messages couldn&apos;t be loaded.</p>
            <Button variant="outline" size="sm" onClick={chat.reload}>
              <RotateCw aria-hidden="true" /> Try again
            </Button>
          </div>
        ) : chat.items.length === 0 && !chat.pending ? (
          <EmptyState chips={suggestionsFor(orderContext)} onPick={(text) => void chat.send(text)} />
        ) : (
          <ol className="flex flex-col gap-5">
            {chat.items.map((item) => (
              <Message key={item.key} item={item} />
            ))}
            {chat.pending && <Working steps={chat.pending.steps} orders={chat.pending.orders} actions={chat.pending.actions} />}
          </ol>
        )}
        {chat.problem && (
          <div role="alert" className="mt-4 flex flex-col items-start gap-2 rounded-xl border px-3 py-2.5 text-sm">
            <p>{chat.problem.message}</p>
            {chat.problem.retryText && (
              <Button variant="outline" size="sm" onClick={() => void chat.send(chat.problem!.retryText!)}>
                <RotateCw aria-hidden="true" /> Retry
              </Button>
            )}
          </div>
        )}
        <div ref={end} />
      </div>
      <Composer chat={chat} autoFocus={autoFocus} />
    </div>
  );
}

function EmptyState({ chips, onPick }: { chips: string[]; onPick: (text: string) => void }) {
  return (
    <div className="flex h-full flex-col justify-end gap-4 pb-2">
      <div className="flex flex-col gap-1">
        <p className="text-base font-medium">How can we help?</p>
        <p className="text-sm text-muted-foreground">Ask about an order, its delivery, a refund or a change.</p>
      </div>
      <div className="flex flex-wrap gap-2">
        {chips.map((s) => (
          <Button key={s} variant="outline" size="sm" className="rounded-full" onClick={() => onPick(s)}>
            {s}
          </Button>
        ))}
      </div>
    </div>
  );
}

function AssistantLabel({ at, showTime }: { at?: string; showTime: boolean }) {
  return (
    <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
      <span aria-hidden="true" className="grid size-5 place-items-center rounded-full bg-primary text-primary-foreground">
        <Headset className="size-3" />
      </span>
      <span className="font-medium text-foreground">Northwind Assistant</span>
      {at && (
        <time
          dateTime={at}
          className={cn("tabular-nums transition-opacity", showTime ? "opacity-100" : "opacity-0 group-hover:opacity-100 group-focus-within:opacity-100")}
        >
          {formatTime(at)}
        </time>
      )}
    </p>
  );
}

function Message({ item }: { item: ChatItem }) {
  // Timestamps: hover or keyboard focus on desktop, tap to toggle on touch screens.
  const [showTime, setShowTime] = useState(false);
  if (item.kind === "system") {
    return <li className="text-center text-xs text-muted-foreground">{item.text}</li>;
  }
  if (item.kind === "customer") {
    return (
      <li className="group flex flex-col items-end gap-1">
        <p
          tabIndex={0}
          onClick={() => setShowTime((v) => !v)}
          className="max-w-[85%] rounded-xl bg-primary px-3 py-2 text-sm leading-relaxed whitespace-pre-wrap text-primary-foreground outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
        >
          <span className="sr-only">You: </span>
          {item.text}
        </p>
        <time
          dateTime={item.at}
          className={cn("text-xs text-muted-foreground tabular-nums transition-opacity", showTime ? "opacity-100" : "opacity-0 group-hover:opacity-100 group-focus-within:opacity-100")}
        >
          {formatTime(item.at)}
        </time>
      </li>
    );
  }
  return (
    <li className="group flex flex-col items-start gap-2" onClick={() => setShowTime((v) => !v)}>
      <AssistantLabel at={item.at} showTime={showTime} />
      {item.steps.length > 0 && <Checked steps={item.steps} />}
      {item.orders.map((o) => (
        <OrderCard key={o.id} order={o} />
      ))}
      {item.actions.map((a, i) => (
        <ActionCard key={`${a.reference ?? a.action}-${i}`} card={a} />
      ))}
      <p tabIndex={0} className="max-w-prose rounded-lg text-sm leading-relaxed whitespace-pre-wrap outline-none focus-visible:ring-3 focus-visible:ring-ring/50">
        <span className="sr-only">Support: </span>
        {item.text}
      </p>
    </li>
  );
}

/** What the assistant looked up before answering: the safety story, visible (Section 13.1). */
function Checked({ steps }: { steps: string[] }) {
  const unique = [...new Set(steps)];
  return (
    <ul aria-label="What was checked" className="flex flex-col gap-0.5 text-xs text-muted-foreground">
      {unique.map((s) => (
        <li key={s} className="flex items-center gap-1.5">
          <Check aria-hidden="true" className="size-3.5" />
          {s.replace(/\.\.\.$/, "")}
        </li>
      ))}
    </ul>
  );
}

function Working({ steps, orders, actions }: { steps: string[]; orders: OrderSummary[]; actions: ActionCardData[] }) {
  const current = steps.at(-1) ?? "Reading your message...";
  return (
    <li className="flex flex-col items-start gap-2">
      <AssistantLabel showTime={false} />
      {steps.length > 1 && <Checked steps={steps.slice(0, -1)} />}
      {orders.map((o) => (
        <OrderCard key={o.id} order={o} />
      ))}
      {actions.map((a, i) => (
        <ActionCard key={`${a.reference ?? a.action}-${i}`} card={a} />
      ))}
      <p className="flex items-center gap-2 text-sm text-muted-foreground">
        <span aria-hidden="true" className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="size-1.5 animate-pulse rounded-full bg-muted-foreground motion-reduce:animate-none"
              style={{ animationDelay: `${i * 150}ms` }}
            />
          ))}
        </span>
        {current}
      </p>
    </li>
  );
}

/** Compact order card (13.3): ID, status pill, total, link. Always from the customer's own data. */
export function OrderCard({ order }: { order: OrderSummary }) {
  return (
    <Link
      href={`/orders/${order.id}`}
      className="flex w-full max-w-sm items-center justify-between gap-3 rounded-xl border bg-card px-3 py-2 outline-none hover:bg-muted/60 focus-visible:ring-3 focus-visible:ring-ring/50"
    >
      <div className="min-w-0">
        <p className="font-mono text-sm">{order.id}</p>
        <p className="truncate text-xs text-muted-foreground">{order.first_item_name}</p>
      </div>
      <div className="flex shrink-0 flex-col items-end gap-1">
        <span className="text-sm tabular-nums">{formatMoney(order.total)}</span>
        <StatusBadge status={order.status} />
      </div>
    </Link>
  );
}

function Composer({ chat, autoFocus }: { chat: Chat; autoFocus: boolean }) {
  const [text, setText] = useState("");
  const submit = () => {
    if (!text.trim() || chat.streaming) return;
    void chat.send(text);
    setText("");
  };
  return (
    <div className="border-t bg-background px-3 pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
      <form
        className="flex items-end gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <label htmlFor="chat-message" className="sr-only">
          Message
        </label>
        <Textarea
          id="chat-message"
          autoFocus={autoFocus}
          rows={1}
          maxLength={2000}
          placeholder={chat.streaming ? "Waiting for the reply..." : "Write a message"}
          disabled={chat.streaming}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault();
              submit();
            }
          }}
          className="max-h-40 min-h-9 resize-none"
        />
        {chat.streaming ? (
          <Button type="button" size="icon" variant="outline" aria-label="Stop" onClick={chat.stop}>
            <Square aria-hidden="true" />
          </Button>
        ) : (
          <Button type="submit" size="icon" aria-label="Send message" disabled={!text.trim()}>
            <ArrowUp aria-hidden="true" />
          </Button>
        )}
      </form>
      <p className="mt-2 text-xs text-muted-foreground">
        AI assistant · Refunds and order changes are checked against store policy before they happen.
      </p>
    </div>
  );
}
