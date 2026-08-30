import type { ClarificationContext, SSEEvent } from "./types";

/**
 * Opens a POST request to our own Next.js API route (/api/search), which
 * proxies to the FastAPI backend and holds the real API key server-side.
 * The browser never sees the backend URL or key.
 *
 * The browser's native EventSource API can't be used here because it only
 * supports GET requests with no custom body — but we need a POST with a
 * JSON body (the query). So this reads the raw streaming response body
 * with fetch + ReadableStream and parses the "data: {...}\n\n" SSE wire
 * format by hand.
 */
export async function* streamSearch(
  query: string,
  clarificationContext?: ClarificationContext,
  signal?: AbortSignal
): AsyncGenerator<SSEEvent> {
  let response: Response;
  try {
    let token: string | null = null;
    try {
      token = typeof window !== "undefined" ? window.localStorage.getItem("sp_token") : null;
    } catch {
      token = null;
    }
    response = await fetch("/api/search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        query,
        clarification_context: clarificationContext ?? null,
      }),
      signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      return;
    }
    yield {
      event: "error",
      payload: {
        code: "network_error",
        message: "Unable to reach the server. Check your connection and try again.",
        details: null,
      },
    };
    return;
  }

  if (!response.ok || !response.body) {
    const errorBody = await response.json().catch(() => ({}));
    yield {
      event: "error",
      payload: {
        code: errorBody?.error?.code ?? "internal_error",
        message: errorBody?.error?.message ?? `Request failed with status ${response.status}`,
        details: null,
      },
    };
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE events are separated by a blank line ("\n\n"). Process every
      // complete event in the buffer, keep any trailing partial event for
      // the next chunk.
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith("data:")) continue;
        const jsonText = line.slice("data:".length).trim();
        if (!jsonText) continue;
        try {
          yield JSON.parse(jsonText) as SSEEvent;
        } catch {
          // Malformed event line — skip it rather than crashing the stream.
          continue;
        }
      }
    }
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      return;
    }
    yield {
      event: "error",
      payload: {
        code: "stream_interrupted",
        message: "The connection was interrupted before the search finished.",
        details: null,
      },
    };
  } finally {
    reader.releaseLock();
  }
}