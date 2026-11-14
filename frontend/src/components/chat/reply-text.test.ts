import assert from "node:assert/strict";
import { test } from "node:test";

import { inlineSegments } from "./reply-text.ts";

// The chat renders reply text from these segments as React text nodes: no HTML is ever parsed (owner,
// 2026-11-14: model output is not trusted). Only **bold** and *italic* become elements.

test("bold and italic become segments; the markers are removed", () => {
  assert.deepEqual(inlineSegments("**ORD-1148** has *shipped*."), [
    { kind: "strong", text: "ORD-1148" },
    { kind: "text", text: " has " },
    { kind: "em", text: "shipped" },
    { kind: "text", text: "." },
  ]);
});

test("HTML stays plain text, whatever it contains", () => {
  const html = '<img src=x onerror="alert(1)"><b>x</b><script>alert(2)</script>';
  assert.deepEqual(inlineSegments(html), [{ kind: "text", text: html }]);
  assert.deepEqual(inlineSegments(`**${html}**`), [{ kind: "strong", text: html }]);
});

test("unmatched or empty markers, and snake_case, are left as they are", () => {
  for (const s of ["5 * 3 = 15", "a ** b", "****", "order_id and refund_reason", "*", "**open"]) {
    assert.deepEqual(inlineSegments(s), [{ kind: "text", text: s }], s);
  }
});

test("line breaks and list dashes survive (whitespace is rendered as is)", () => {
  assert.deepEqual(inlineSegments("- **ORD-1148** shipped\n- ORD-1061"), [
    { kind: "text", text: "- " },
    { kind: "strong", text: "ORD-1148" },
    { kind: "text", text: " shipped\n- ORD-1061" },
  ]);
});
