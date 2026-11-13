"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { use } from "react";

import { TranscriptView } from "@/components/staff/transcript-view";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api";
import { useConversation } from "@/lib/staff-queries";

/** Read-only conversation with its tool trace (spec 13.4), linked from the inbox and the audit log. */
export default function ConversationPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const conversation = useConversation(id);
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-4">
      <Link
        href="/console/audit"
        className="inline-flex items-center gap-1.5 self-start rounded-lg text-sm text-muted-foreground outline-none hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50"
      >
        <ArrowLeft aria-hidden="true" className="size-4" /> Audit log
      </Link>
      <h1 className="text-xl font-semibold">
        Conversation{conversation.data ? <span className="font-normal text-muted-foreground"> · {conversation.data.customer_id}</span> : null}
      </h1>
      {conversation.isPending ? (
        <div className="flex flex-col gap-2" aria-busy="true" aria-label="Loading the conversation">
          <Skeleton className="h-16 w-2/3" />
          <Skeleton className="h-16 w-1/2" />
        </div>
      ) : conversation.error instanceof ApiError && conversation.error.status === 404 ? (
        <p className="text-sm text-muted-foreground">No conversation with that id.</p>
      ) : conversation.error ? (
        <div role="alert" className="flex flex-col items-start gap-2">
          <p className="text-sm font-medium">Couldn&apos;t load the conversation.</p>
          <Button variant="outline" size="sm" onClick={() => void conversation.refetch()}>
            Try again
          </Button>
        </div>
      ) : (
        <TranscriptView transcript={conversation.data} />
      )}
    </div>
  );
}
