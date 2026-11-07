import type { components } from "@/types/api";

export type Money = components["schemas"]["Money"];

const SYMBOL: Record<Money["currency"], string> = { USD: "$", PKR: "Rs " };
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/**
 * The ONE money formatter, from integer minor units (PKR = paisa); integer maths only.
 * USD always shows cents ($32.00). PKR drops ".00" when the paisa part is zero (Rs 26,495) and shows
 * it otherwise (Rs 26,495.50). backend/tollgate/domain/money.py applies the same rule for the model.
 */
export function formatMoney({ amount_cents, currency }: Money): string {
  const sign = amount_cents < 0 ? "-" : "";
  const abs = Math.abs(amount_cents);
  const major = Math.floor(abs / 100).toLocaleString("en-US");
  const minor = abs % 100;
  const cents = currency === "PKR" && minor === 0 ? "" : `.${String(minor).padStart(2, "0")}`;
  return `${sign}${SYMBOL[currency]}${major}${cents}`;
}

/** "21 Aug 2026", in UTC so it always matches the dates the assistant quotes. */
export function formatDate(iso: string): string {
  const d = new Date(iso);
  return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

const timeFmt = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit" });

export function formatTime(iso: string): string {
  return timeFmt.format(new Date(iso));
}

const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });

export function relativeTime(iso: string, now: Date = new Date()): string {
  const seconds = Math.round((new Date(iso).getTime() - now.getTime()) / 1000);
  const units: [Intl.RelativeTimeFormatUnit, number][] = [
    ["day", 86400],
    ["hour", 3600],
    ["minute", 60],
  ];
  for (const [unit, size] of units) {
    if (Math.abs(seconds) >= size) return rtf.format(Math.round(seconds / size), unit);
  }
  return "just now";
}

/** Two-letter tile text for a product name, e.g. "Electric Kettle 1.7L" -> "EK". */
export function initials(name: string): string {
  const words = name.replace(/\(.*?\)/g, "").split(/\s+/).filter((w) => /^[A-Za-z]/.test(w));
  return (words[0]?.[0] ?? "?").toUpperCase() + (words[1]?.[0] ?? "").toUpperCase();
}
