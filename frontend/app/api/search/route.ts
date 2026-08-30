import { NextRequest } from "next/server";

// This route runs on the server only. It holds the real backend API key
// (SHOPPILOT_API_KEY, no NEXT_PUBLIC_ prefix) and forwards the request to
// the FastAPI backend, streaming the SSE response straight back to the
// browser. The browser never sees the API key.

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const getBackendUrl = () => {
  if (process.env.SHOPPILOT_BACKEND_URL) return process.env.SHOPPILOT_BACKEND_URL;
  if (process.env.VERCEL_URL) return `https://${process.env.VERCEL_URL}`;
  return "http://localhost:8000";
};
const BACKEND_URL = getBackendUrl();
const API_KEY = process.env.SHOPPILOT_API_KEY ?? "";

export async function POST(req: NextRequest) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return Response.json(
      { error: { code: "invalid_body", message: "Request body must be valid JSON." } },
      { status: 400 }
    );
  }

  let upstream: Response;
  try {
    const authHeader = req.headers.get("Authorization");
    upstream = await fetch(`${BACKEND_URL}/api/v1/search`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
        // Forward the signed-in user's token so the backend can attribute
        // this search to them (for search history). Anonymous if absent.
        ...(authHeader ? { Authorization: authHeader } : {}),
      },
      body: JSON.stringify(body),
      // Forward client abort to the upstream request.
      signal: req.signal,
    });
  } catch {
    return Response.json(
      {
        error: {
          code: "upstream_unreachable",
          message: "Could not reach the search backend. Is it running?",
        },
      },
      { status: 502 }
    );
  }

  if (!upstream.ok || !upstream.body) {
    const errorBody = await upstream.json().catch(() => ({}));
    return Response.json(
      {
        error: {
          code: errorBody?.error?.code ?? "upstream_error",
          message: errorBody?.error?.message ?? `Backend responded with ${upstream.status}`,
        },
      },
      { status: upstream.status || 502 }
    );
  }

  // Pass the SSE stream through untouched.
  return new Response(upstream.body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}