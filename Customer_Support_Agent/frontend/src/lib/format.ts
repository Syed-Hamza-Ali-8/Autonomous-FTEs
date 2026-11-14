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

/** "17:00" for today, "9 Nov, 17:00" otherwise; the viewer's local clock, like message times. */
export function formatWhen(iso: string, now: Date = new Date()): string {
  const d = new Date(iso);
  const sameDay = d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth() && d.getDate() === now.getDate();
  return sameDay ? formatTime(iso) : `${d.getDate()} ${MONTHS[d.getMonth()]}, ${formatTime(iso)}`;
}

/**
 * Staff console and audit log (DECISIONS F2, amended): the instant with an EXPLICIT timezone, "7 Nov 2026,
 * 12:00 UTC", so staff in different places read the same time. Customer-facing times use formatWhen.
 */
export function formatStaffTimestamp(iso: string): string {
  const d = new Date(iso);
  const hh = String(d.getUTCHours()).padStart(2, "0");
  const mm = String(d.getUTCMinutes()).padStart(2, "0");
  return `${formatDate(iso)}, ${hh}:${mm} UTC`;
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

/**
 * Staff queue urgency (spec 13.4): time left before an approval expires, in whole hours ("47h"), in minutes in
 * the final hour ("35m"), and "Expired" once it has. Rounded DOWN, so it never promises more time than is left.
 */
export function timeLeft(expiresIso: string, now: Date = new Date()): string {
  const minutes = Math.floor((new Date(expiresIso).getTime() - now.getTime()) / 60_000);
  if (minutes <= 0) return "Expired";
  return minutes < 60 ? `Expires in ${minutes}m` : `Expires in ${Math.floor(minutes / 60)}h`;
}

/** Two-letter tile text for a product name, e.g. "Electric Kettle 1.7L" -> "EK". */
export function initials(name: string): string {
  const words = name.replace(/\(.*?\)/g, "").split(/\s+/).filter((w) => /^[A-Za-z]/.test(w));
  return (words[0]?.[0] ?? "?").toUpperCase() + (words[1]?.[0] ?? "").toUpperCase();
}
