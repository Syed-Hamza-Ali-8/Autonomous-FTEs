"use client";

import { CircleCheck, CircleMinus, CircleX, Clock, MessageSquareText } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { DecisionPill } from "@/components/decision-pill";
import { APPROVAL_PILL, CHECK_LABEL, type CheckState, approvalTitle } from "@/components/staff/staff-meta";
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { ApprovalDetail } from "@/lib/api";
import { formatMoney, formatStaffTimestamp } from "@/lib/format";
import { cn } from "@/lib/utils";

const CHECK_ICON: Record<CheckState, { icon: typeof CircleCheck; className: string }> = {
  pass: { icon: CircleCheck, className: "text-success" },
  fail: { icon: CircleX, className: "text-danger" },
  needs_approval: { icon: Clock, className: "text-warning" },
  not_reached: { icon: CircleMinus, className: "text-muted-foreground" },
};

export type DialogKind = "approve" | "reject" | null;

/**
 * Decision panel (spec 13.4): order summary, captured vs refunded, the policy checklist (each rule with its
 * value and how this request fares on it NOW; staff only, tier C), then Approve and Reject behind confirm
 * dialogs showing the exact amount. The dialogs stay open until the server answers: nothing is optimistic.
 */
export function DecisionPanel({
  detail,
  dialog,
  onDialog,
  busy,
  onApprove,
  onReject,
}: {
  detail: ApprovalDetail;
  dialog: DialogKind;
  onDialog: (d: DialogKind) => void;
  busy: boolean;
  onApprove: () => void;
  onReject: (note: string) => void;
}) {
  const a = detail.approval;
  const pending = a.state === "pending";
  const amount = a.amount ? formatMoney(a.amount) : null;
  const title = approvalTitle(a.action, a.order_id);
  const refuses = detail.checklist.some((c) => c.state === "fail");
  const pill = APPROVAL_PILL[a.state];
  return (
    <section aria-label="Decision" className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
          <h2 className="min-w-0 flex-auto text-base font-semibold">{title}</h2>
          <DecisionPill decision={pill.decision} label={pill.label} className="shrink-0" />
        </div>
        <p className="text-sm text-muted-foreground">
          {a.customer_name} <span className="font-mono text-xs">{a.customer_id}</span> · <span className="font-mono text-xs">{a.reference}</span>
        </p>
        {amount && <p className="text-2xl font-semibold tabular-nums">{amount}</p>}
        <p className="text-xs text-muted-foreground tabular-nums">
          Queued {formatStaffTimestamp(a.queued_at)}
          {pending && <> · expires {formatStaffTimestamp(a.expires_at)}</>}
        </p>
      </div>

      {detail.order && (
        <dl aria-label="Order summary" className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 rounded-xl border px-3 py-2.5 text-sm">
          <dt className="text-muted-foreground">Order status</dt>
          <dd>{detail.order.status.replace("_", " ")}</dd>
          <dt className="text-muted-foreground">Order total</dt>
          <dd className="tabular-nums">{formatMoney(detail.order.total)}</dd>
          <dt className="text-muted-foreground">Captured</dt>
          <dd className="tabular-nums">{formatMoney(detail.order.captured)}</dd>
          <dt className="text-muted-foreground">Refunded so far</dt>
          <dd className="tabular-nums">{formatMoney(detail.order.refunded)}</dd>
          {detail.order.items.length > 0 && (
            <>
              <dt className="text-muted-foreground">Items</dt>
              <dd className="min-w-0 break-words">{detail.order.items.join(", ")}</dd>
            </>
          )}
        </dl>
      )}

      <div className="flex flex-col gap-2">
        <h3 className="text-sm font-medium">Policy checklist {pending ? "(checked now)" : "(at decision time)"}</h3>
        <ul className="flex flex-col gap-1.5" aria-label="Policy checklist">
          {detail.checklist.map((c) => {
            const { icon: Icon, className } = CHECK_ICON[c.state];
            return (
              <li key={c.code} className="flex gap-2 text-sm">
                <Icon aria-hidden="true" className={cn("mt-0.5 size-4 shrink-0", className)} />
                <div className="flex min-w-0 flex-col">
                  <span>
                    <span className="sr-only">{CHECK_LABEL[c.state]}: </span>
                    {c.label}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {CHECK_LABEL[c.state]}
                    {c.detail && <> · {c.detail}</>} · <span className="font-mono">{c.code}</span>
                  </span>
                </div>
              </li>
            );
          })}
        </ul>
      </div>

      {detail.decision && (
        <div className="rounded-xl border px-3 py-2.5 text-sm">
          <p className="font-medium">
            {APPROVAL_PILL[detail.decision.decision].label}
            {detail.decision.decided_by ? ` by ${detail.decision.decided_by}` : ""}
          </p>
          <p className="text-xs text-muted-foreground tabular-nums">{formatStaffTimestamp(detail.decision.decided_at)}</p>
          {detail.decision.note && <p className="mt-1 whitespace-pre-wrap">{detail.decision.note}</p>}
        </div>
      )}

      {pending && (
        // Below 1280px the decision stays within reach: the bar sticks to the bottom of the screen while the
        // checklist scrolls under it. Both buttons still open the confirm dialogs.
        <div
          role="group"
          aria-label="Decide"
          className="sticky bottom-0 z-10 -mx-4 flex flex-col gap-2 border-t bg-background px-4 py-3 xl:static xl:mx-0 xl:border-t-0 xl:bg-transparent xl:p-0"
        >
          {refuses && (
            <p className="text-sm text-muted-foreground">
              A rule now refuses this request. Approving it records &ldquo;couldn&apos;t complete&rdquo; and changes nothing.
            </p>
          )}
          <div className="flex gap-2">
            <Button className="flex-1 xl:flex-none" onClick={() => onDialog("approve")} aria-keyshortcuts="A">
              Approve <kbd className="ml-1 hidden rounded border border-primary-foreground/40 px-1 font-mono text-xs xl:inline">A</kbd>
            </Button>
            <Button className="flex-1 xl:flex-none" variant="outline" onClick={() => onDialog("reject")} aria-keyshortcuts="R">
              Reject <kbd className="ml-1 hidden rounded border px-1 font-mono text-xs xl:inline">R</kbd>
            </Button>
          </div>
        </div>
      )}

      {a.conversation_id && (
        <Link
          href={`/console/conversations/${a.conversation_id}`}
          className="inline-flex items-center gap-1.5 self-start rounded-lg text-sm text-primary underline-offset-4 outline-none hover:underline focus-visible:ring-3 focus-visible:ring-ring/50"
        >
          <MessageSquareText aria-hidden="true" className="size-4" /> Open conversation
        </Link>
      )}

      <AlertDialog open={dialog === "approve"} onOpenChange={(o) => !busy && onDialog(o ? "approve" : null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Approve {title}?</AlertDialogTitle>
            <AlertDialogDescription>
              {amount ? (
                <>
                  This pays out exactly <strong className="text-foreground tabular-nums">{amount}</strong> to {a.customer_name}.
                </>
              ) : (
                <>This carries out the request for {a.customer_name}.</>
              )}{" "}
              Policy is checked again on the order as it is now; if a rule refuses it, nothing changes.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={busy}>Cancel</AlertDialogCancel>
            <Button onClick={onApprove} disabled={busy}>
              {busy ? "Approving…" : amount ? `Approve ${amount}` : "Approve"}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <RejectDialog open={dialog === "reject"} onOpenChange={(o) => !busy && onDialog(o ? "reject" : null)} busy={busy} amount={amount} title={title} onReject={onReject} />
    </section>
  );
}

function RejectDialog({
  open,
  onOpenChange,
  busy,
  amount,
  title,
  onReject,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  busy: boolean;
  amount: string | null;
  title: string;
  onReject: (note: string) => void;
}) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        {/* The form lives inside the content, which unmounts on close: every opening starts empty. */}
        <RejectForm busy={busy} amount={amount} title={title} onReject={onReject} />
      </AlertDialogContent>
    </AlertDialog>
  );
}

function RejectForm({ busy, amount, title, onReject }: { busy: boolean; amount: string | null; title: string; onReject: (note: string) => void }) {
  const [note, setNote] = useState("");
  const [touched, setTouched] = useState(false);
  const missing = !note.trim();
  return (
    <>
      <AlertDialogHeader>
        <AlertDialogTitle>Reject {title}?</AlertDialogTitle>
        <AlertDialogDescription>
          {amount ? (
            <>
              Nothing is paid. The <strong className="text-foreground tabular-nums">{amount}</strong> held for this request is released.
            </>
          ) : (
            <>Nothing changes on the order.</>
          )}{" "}
          The customer is told the team couldn&apos;t approve it, never why.
        </AlertDialogDescription>
      </AlertDialogHeader>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="reject-note">Note for the audit log (required, staff only)</Label>
        <Textarea
          id="reject-note"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          onBlur={() => setTouched(true)}
          aria-invalid={touched && missing}
          aria-describedby={touched && missing ? "reject-note-error" : undefined}
          rows={3}
        />
        {touched && missing && (
          <p id="reject-note-error" className="text-sm text-danger-foreground">
            Add a note explaining the rejection.
          </p>
        )}
      </div>
      <AlertDialogFooter>
        <AlertDialogCancel disabled={busy}>Cancel</AlertDialogCancel>
        <Button
          variant="destructive"
          disabled={busy}
          onClick={() => {
            setTouched(true);
            if (!missing) onReject(note.trim());
          }}
        >
          {busy ? "Rejecting…" : "Reject"}
        </Button>
      </AlertDialogFooter>
    </>
  );
}
