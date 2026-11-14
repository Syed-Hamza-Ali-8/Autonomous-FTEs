/**
 * Reply text, split into plain, bold and italic segments (owner, 2026-11-14).
 *
 * Model output is not trusted, so it never goes through a Markdown or HTML renderer: the chat renders these
 * segments as React text nodes, and anything else in the reply, HTML included, stays literal text. Only
 * **bold** and *italic* are recognised; a marker needs non-space text right inside it, so "5 * 3" or a lone
 * "**" is left as written. Underscores are not markers: they appear in identifiers.
 */

export type Segment = { kind: "text" | "strong" | "em"; text: string };

const MARKERS = /\*\*(?!\s)([^*]+?)(?<!\s)\*\*|\*(?!\s)([^*\n]+?)(?<!\s)\*/g;

export function inlineSegments(text: string): Segment[] {
  const out: Segment[] = [];
  const push = (kind: Segment["kind"], s: string) => {
    if (!s) return;
    const last = out[out.length - 1];
    if (kind === "text" && last?.kind === "text") last.text += s;
    else out.push({ kind, text: s });
  };
  let at = 0;
  for (const m of text.matchAll(MARKERS)) {
    push("text", text.slice(at, m.index));
    if (m[1] !== undefined) push("strong", m[1]);
    else push("em", m[2]);
    at = m.index + m[0].length;
  }
  push("text", text.slice(at));
  return out.length ? out : [{ kind: "text", text }];
}
