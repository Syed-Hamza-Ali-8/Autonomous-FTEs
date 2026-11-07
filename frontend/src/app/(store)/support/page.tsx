"use client";

import { ChatPanel } from "@/components/chat/chat-panel";
import { useChatControls } from "@/components/chat/chat-provider";

// Mobile: the chat fills the space under the header edge to edge (no card, no title), composer at
// the bottom. The store layout gives this page a 100dvh column, and the root viewport uses
// interactive-widget=resizes-content, so the composer stays above the on-screen keyboard.
export default function SupportPage() {
  const { chat } = useChatControls();
  return (
    <div className="flex min-h-0 flex-1 flex-col sm:gap-4">
      <div className="hidden flex-col gap-1 sm:flex">
        <h1 className="text-2xl font-semibold tracking-tight">Support</h1>
        <p className="text-sm text-muted-foreground">Ask about an order, its delivery or its refunds.</p>
      </div>
      <h1 className="sr-only sm:hidden">Support</h1>
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden sm:max-h-[720px] sm:rounded-xl sm:border">
        <ChatPanel chat={chat} autoFocus />
      </div>
    </div>
  );
}
