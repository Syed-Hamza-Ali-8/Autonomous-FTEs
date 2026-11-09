"use client";

import { DecisionPill } from "@/components/decision-pill";
import { STATE_PILL, actionTitle } from "@/components/chat/action-meta";
import type { ActionCard as ActionCardData } from "@/lib/api";
import { formatMoney, formatTime } from "@/lib/format";

/**
 * What one write request did (13.3). Built by the server from the Action Gateway's own outcome, never
 * from the assistant's text, so it is the source of truth when the two differ.
 */
export function ActionCard({ card }: { card: ActionCardData }) {
  const pill = STATE_PILL[card.state];
  const title = actionTitle(card.action, card.order_id);
  return (
    <section
      aria-label={`${title}: ${pill.label}`}
      className="flex w-full max-w-sm flex-col gap-2 rounded-xl border bg-card px-3 py-3"
    >
      <div className="flex flex-wrap items-start justify-between gap-x-3 gap-y-1.5">
        <h3 className="text-sm font-medium">{title}</h3>
        <DecisionPill decision={pill.decision} label={pill.label} />
      </div>
      {card.amount && <p className="text-base font-medium tabular-nums">{formatMoney(card.amount)}</p>}
      <p className="text-sm leading-relaxed text-muted-foreground">{card.explanation}</p>
      <p className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
        {card.reference && (
          <span>
            Reference <span className="font-mono text-foreground">{card.reference}</span>
          </span>
        )}
        {/* Same convention as message times (local clock); the exact instant on hover. */}
        <time dateTime={card.at} title={new Date(card.at).toISOString()} className="tabular-nums">
          {formatTime(card.at)}
        </time>
      </p>
    </section>
  );
}
