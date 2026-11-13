"use client";

import { actionTitle, statePill } from "@/components/chat/action-meta";
import { DecisionPill } from "@/components/decision-pill";
import type { ActionCard as ActionCardData, ActionRecord } from "@/lib/api";
import { formatMoney, formatWhen } from "@/lib/format";
import { useAction } from "@/lib/queries";

const ADDRESS_LINES: { field: keyof NonNullable<ActionRecord["delivery_address"]>; label: string }[] = [
  { field: "name", label: "Recipient" },
  { field: "line1", label: "Street" },
  { field: "city", label: "City" },
  { field: "postal_code", label: "Postcode" },
  { field: "country", label: "Country" },
];

/**
 * What one write request did (13.3). The live event comes from the Action Gateway's own outcome, never from
 * the assistant's text. Requests with an action record (completed or waiting) also read it (DECISIONS C2):
 * a waiting card updates in place when staff decide (or when it waited too long and closed, DECISIONS J8), with
 * the record's own explanation for its current state, and an address change shows the full resulting address.
 * Nothing here states a policy reason, rule or limit (DECISIONS I15).
 */
export function ActionCard({ card }: { card: ActionCardData }) {
  const record = useAction(card.reference?.startsWith("ACT-") ? card.reference : null).data;
  const state = record?.state ?? card.state;
  const pill = statePill(state, record !== undefined);
  const title = actionTitle(card.action, card.order_id);
  const amount = record?.amount ?? card.amount;
  const explanation = record?.explanation ?? card.explanation;
  const address = record?.delivery_address;
  return (
    <section aria-label={`${title}: ${pill.label}`} className="flex w-full max-w-sm flex-col gap-2 rounded-xl border bg-card px-3 py-3 sm:min-w-[22rem]">
      {/* The pill keeps its full width: when it and the title don't fit comfortably side by side, it wraps
          onto its own line below the title instead of being squeezed. */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
        {/* K2: the title takes its own width (not a fixed basis), so title and pill share a line whenever
            they fit, and the pill wraps only in genuinely narrow cards. */}
        <h3 className="min-w-0 flex-auto text-sm font-medium">{title}</h3>
        <DecisionPill decision={pill.decision} label={pill.label} className="shrink-0" />
      </div>
      {amount && <p className="text-base font-medium tabular-nums">{formatMoney(amount)}</p>}
      {/* K3: once the resulting address is shown, "The delivery address is updated." only repeats the title
          and pill; the field table speaks for itself. */}
      {!address && <p className="text-sm leading-relaxed text-muted-foreground">{explanation}</p>}
      {address && (
        <dl aria-label="Delivery address now" className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 rounded-lg bg-muted/50 px-2.5 py-2 text-sm">
          {ADDRESS_LINES.map(({ field, label }) => (
            <div key={field} className="contents">
              <dt className="text-muted-foreground">{label}</dt>
              <dd className="min-w-0 break-words">
                {address[field]}
                {record?.kept_fields.includes(field) && <span className="ml-1.5 text-xs text-muted-foreground">(unchanged)</span>}
              </dd>
            </div>
          ))}
        </dl>
      )}
      <p className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
        {card.reference && (
          <span>
            Reference <span className="font-mono text-foreground">{card.reference}</span>
          </span>
        )}
        <time dateTime={card.at} title={new Date(card.at).toISOString()} className="tabular-nums">
          {formatWhen(card.at)}
        </time>
      </p>
    </section>
  );
}
