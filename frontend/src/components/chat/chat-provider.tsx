"use client";

import { MessageCircle, X } from "lucide-react";
import { usePathname } from "next/navigation";
import { createContext, useCallback, useContext, useState } from "react";
import { Dialog as DialogPrimitive } from "radix-ui";

import { ChatPanel } from "@/components/chat/chat-panel";
import { useChat } from "@/components/chat/use-chat";
import { Button } from "@/components/ui/button";
import type { OrderSummary } from "@/lib/api";

type ChatControls = {
  chat: ReturnType<typeof useChat>;
  orderContext: OrderSummary | null;
  openChat: (order?: OrderSummary) => void;
};

const ChatContext = createContext<ChatControls | null>(null);

/** One chat per signed-in session, shared by the floating panel and the full /support page. */
export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const [orderContext, setOrderContext] = useState<OrderSummary | null>(null);
  const chat = useChat(orderContext);
  const pathname = usePathname();

  const openChat = useCallback((order?: OrderSummary) => {
    if (order) setOrderContext(order);
    setOpen(true);
  }, []);

  const onSupportPage = pathname === "/support";
  // Owner UI review 17-18: no floating launcher below 768px (the header link and the order page's
  // button cover it), and none on pages with their own entry point (/support, order detail).
  const showLauncher = !onSupportPage && !pathname.startsWith("/orders/");

  return (
    <ChatContext.Provider value={{ chat, orderContext, openChat }}>
      {children}
      {!onSupportPage && (
        <DialogPrimitive.Root open={open} onOpenChange={setOpen}>
          {showLauncher && (
            <DialogPrimitive.Trigger asChild>
              <Button
                size="lg"
                className="fixed right-6 bottom-6 z-40 hidden h-12 rounded-full px-4 shadow-lg md:inline-flex"
                aria-label="Open support chat"
              >
                <MessageCircle aria-hidden="true" className="size-5" />
                Support
              </Button>
            </DialogPrimitive.Trigger>
          )}
          <DialogPrimitive.Portal>
            <DialogPrimitive.Content
              aria-describedby={undefined}
              className="fixed inset-0 z-50 flex flex-col bg-popover text-popover-foreground outline-none data-open:animate-in data-open:fade-in-0 data-open:slide-in-from-bottom-4 sm:inset-auto sm:right-6 sm:bottom-6 sm:h-[min(640px,calc(100dvh-3rem))] sm:w-[400px] sm:rounded-xl sm:border sm:shadow-xl"
            >
              <div className="flex items-center justify-between border-b px-4 py-3">
                <div>
                  <DialogPrimitive.Title className="text-base font-medium">Support</DialogPrimitive.Title>
                  <p className="text-xs text-muted-foreground">
                    {orderContext ? "About this order" : "Answers about your orders"}
                  </p>
                </div>
                <DialogPrimitive.Close asChild>
                  <Button variant="ghost" size="icon" aria-label="Close support chat">
                    <X aria-hidden="true" />
                  </Button>
                </DialogPrimitive.Close>
              </div>
              <ChatPanel chat={chat} orderContext={orderContext} autoFocus />
            </DialogPrimitive.Content>
          </DialogPrimitive.Portal>
        </DialogPrimitive.Root>
      )}
    </ChatContext.Provider>
  );
}

export function useChatControls(): ChatControls {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChatControls must be used inside ChatProvider");
  return ctx;
}
