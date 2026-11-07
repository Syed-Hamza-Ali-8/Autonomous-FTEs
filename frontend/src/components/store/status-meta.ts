import {
  CircleCheck,
  CircleDashed,
  CircleX,
  CreditCard,
  Package,
  RotateCcw,
  Truck,
  type LucideIcon,
} from "lucide-react";

import type { OrderStatus } from "@/lib/api";

// Owner UI review item 7: only a successful end state may use a check-style icon.
export const ORDER_STATUS: Record<OrderStatus, { label: string; icon: LucideIcon; success: boolean }> = {
  pending: { label: "Awaiting payment", icon: CircleDashed, success: false },
  paid: { label: "Paid", icon: CreditCard, success: false },
  packed: { label: "Packed", icon: Package, success: false },
  shipped: { label: "On its way", icon: Truck, success: false },
  delivered: { label: "Delivered", icon: CircleCheck, success: true },
  cancelled: { label: "Cancelled", icon: CircleX, success: false },
  refunded: { label: "Refunded", icon: RotateCcw, success: false },
  partially_refunded: { label: "Partly refunded", icon: RotateCcw, success: false },
};

/** Order-list filter groups (owner UI review item 8). */
export const FILTER_GROUPS = {
  all: { label: "All", statuses: null },
  in_progress: { label: "In progress", statuses: ["pending", "paid", "packed", "shipped"] },
  delivered: { label: "Delivered", statuses: ["delivered"] },
  refunded: { label: "Refunded", statuses: ["refunded", "partially_refunded"] },
  cancelled: { label: "Cancelled", statuses: ["cancelled"] },
} as const satisfies Record<string, { label: string; statuses: readonly OrderStatus[] | null }>;

export type FilterGroup = keyof typeof FILTER_GROUPS;
