import { CircleCheck, CircleX, Clock, Info, type LucideIcon } from "lucide-react";

import { Button } from "@/components/ui/button";

// Phase 0 design-token preview. Replaced by the storefront routes in Phase 1.

type Decision = {
  label: string;
  icon: LucideIcon;
  className: string;
};

const decisions: Decision[] = [
  {
    label: "Completed",
    icon: CircleCheck,
    className: "bg-success-muted text-success-foreground border-success-border [&_svg]:text-success",
  },
  {
    label: "Waiting for staff approval",
    icon: Clock,
    className: "bg-warning-muted text-warning-foreground border-warning-border [&_svg]:text-warning",
  },
  {
    label: "Not allowed",
    icon: CircleX,
    className: "bg-danger-muted text-danger-foreground border-danger-border [&_svg]:text-danger",
  },
  {
    label: "Informational",
    icon: Info,
    className: "bg-info-muted text-info-foreground border-info-border [&_svg]:text-info",
  },
];

export default function TokenPreview() {
  return (
    <main className="px-gutter mx-auto flex w-full max-w-3xl flex-col gap-8 py-12">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight">Tollgate design tokens</h1>
        <p className="text-muted-foreground text-sm">
          Phase 0 preview of Section 13.2: surfaces, accent, decision colours, type and radius.
        </p>
      </header>

      <section aria-labelledby="decisions" className="flex flex-col gap-3">
        <h2 id="decisions" className="text-base font-medium">
          Decision states
        </h2>
        <ul className="flex flex-wrap gap-2">
          {decisions.map(({ label, icon: Icon, className }) => (
            <li
              key={label}
              className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-sm font-medium ${className}`}
            >
              <Icon aria-hidden="true" className="size-4" />
              {label}
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="controls" className="flex flex-col gap-3">
        <h2 id="controls" className="text-base font-medium">
          Controls
        </h2>
        <div className="flex flex-wrap gap-2">
          <Button>Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="destructive">Reject</Button>
          <Button variant="link">Link</Button>
        </div>
      </section>

      <section aria-labelledby="card" className="bg-card text-card-foreground flex flex-col gap-2 rounded-xl border p-6">
        <h2 id="card" className="text-base font-medium">
          Refund · <span className="font-mono">ORD-1042</span>
        </h2>
        <p className="text-muted-foreground text-sm">Card surface, 12px radius, 1px border, no shadow.</p>
        <p className="text-3xl font-semibold tabular-nums">$32.00</p>
      </section>
    </main>
  );
}
