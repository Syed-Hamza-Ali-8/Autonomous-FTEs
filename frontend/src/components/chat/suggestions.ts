import type { OrderStatus } from "@/lib/api";

const GENERAL = ["Where is my order?", "I want a refund", "Change my delivery address"];

/**
 * Suggestion chips for the chat (spec 13.3; owner UI review item 15). When the chat was opened from
 * an order, the chips follow that order's status. An address change is only offered while the order
 * hasn't left the warehouse.
 */
export function suggestionsFor(order: { id: string; status: OrderStatus; item_count: number } | null): string[] {
  if (!order) return GENERAL;
  const { id, status, item_count } = order;
  switch (status) {
    case "pending":
    case "paid":
    case "packed":
      return [`Where is ${id}?`, "Change my delivery address", "Cancel this order"];
    case "shipped":
      return [`Where is ${id}?`, "When will it arrive?", "Something's wrong with it"];
    case "delivered":
      return [`Where is ${id}?`, "Refund an item", "Something's wrong with it"];
    case "partially_refunded":
      // "another item" only makes sense when there is another item to refund
      return item_count > 1
        ? [`What was refunded on ${id}?`, "Refund another item", "Something's wrong with it"]
        : [`What was refunded on ${id}?`, "Something's wrong with it"];
    case "refunded":
      return [`Where is my refund for ${id}?`, "Something's wrong with it"];
    case "cancelled":
      return [`Why was ${id} cancelled?`, "Was I charged for it?"];
  }
}
