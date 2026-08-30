// Server-only proxy for the backend's /api/v1/saved endpoints (GET/POST/DELETE).
// The real backend API key lives in SHOPPILOT_API_KEY (no NEXT_PUBLIC_ prefix)
// so it is never shipped to the browser. The browser calls this same-origin
// route, which attaches the key server-side and forwards the user's token.
import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const getBackendUrl = () => {
  if (process.env.SHOPPILOT_BACKEND_URL) return process.env.SHOPPILOT_BACKEND_URL;
  if (process.env.VERCEL_URL) return `https://${process.env.VERCEL_URL}`;
  return "http://localhost:8000";
};
const BACKEND_URL = getBackendUrl();
const API_KEY = process.env.SHOPPILOT_API_KEY ?? "";

function headers(req: NextRequest, json = false): Record<string, string> {
  const auth = req.headers.get("Authorization");
  return {
    ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
    ...(auth ? { Authorization: auth } : {}),
    ...(json ? { "Content-Type": "application/json" } : {}),
  };
}

export async function GET(req: NextRequest) {
  try {
    const upstream = await fetch(`${BACKEND_URL}/api/v1/saved`, {
      headers: headers(req),
    });
    const data = await upstream.json().catch(() => ({ products: [], count: 0 }));
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json(
      { products: [], count: 0, detail: "Could not reach the server." },
      { status: 502 }
    );
  }
}

export async function POST(req: NextRequest) {
  const body = await req.text();
  try {
    const upstream = await fetch(`${BACKEND_URL}/api/v1/saved`, {
      method: "POST",
      headers: headers(req, true),
      body,
    });
    const data = await upstream.json().catch(() => ({}));
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json(
      { detail: "Could not reach the server." },
      { status: 502 }
    );
  }
}

export async function DELETE(req: NextRequest) {
  const body = await req.text();
  try {
    const upstream = await fetch(`${BACKEND_URL}/api/v1/saved`, {
      method: "DELETE",
      headers: headers(req, true),
      body,
    });
    const data = await upstream.json().catch(() => ({}));
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json(
      { detail: "Could not reach the server." },
      { status: 502 }
    );
  }
}
