"use client";

import { apiUrl, ApiError, type ChatEvent, type Schemas } from "@/lib/api";

export type ChatRequest = Schemas["ChatRequest"];

/**
 * POST /v1/chat and yield each server-sent event. EventSource can't POST or send headers, so the
 * stream is read with fetch. Abort the signal to stop (the server then stores no reply).
 */
export async function* streamChat(
  body: ChatRequest,
  token: string,
  signal: AbortSignal,
): AsyncGenerator<ChatEvent> {
  const res = await fetch(apiUrl("/v1/chat"), {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(body),
    cache: "no-store",
    signal,
  });
  if (!res.ok || !res.body) {
    const err = (await res.json().catch(() => ({}))) as { error?: string };
    throw new ApiError(res.status, err.error ?? "error");
  }
  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += value;
    let split: number;
    while ((split = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, split);
      buffer = buffer.slice(split + 2);
      const data = frame
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trimStart())
        .join("\n");
      if (data) yield JSON.parse(data) as ChatEvent;
    }
  }
}
