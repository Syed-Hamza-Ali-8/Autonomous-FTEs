import { initials } from "@/lib/format";
import { cn } from "@/lib/utils";

/** Neutral generated thumbnail: the product's initials on a muted tile (no stock photos). */
export function ProductTile({ name, size = "md", className }: { name: string; size?: "sm" | "md"; className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "grid shrink-0 place-items-center rounded-lg border bg-muted font-medium text-muted-foreground",
        size === "md" ? "size-12 text-sm" : "size-9 text-xs",
        className,
      )}
    >
      {initials(name)}
    </div>
  );
}
