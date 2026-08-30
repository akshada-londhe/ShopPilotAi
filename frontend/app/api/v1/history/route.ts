// Server-only proxy for the backend's GET /api/v1/history endpoint.
// Attaches the backend API key server-side and forwards the user's token so
// the backend returns that user's search history.
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

export async function GET(req: NextRequest) {
  const auth = req.headers.get("Authorization");
  try {
    const upstream = await fetch(`${BACKEND_URL}/api/v1/history`, {
      headers: {
        ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
        ...(auth ? { Authorization: auth } : {}),
      },
    });
    const data = await upstream.json().catch(() => ({ searches: [], count: 0 }));
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json(
      { searches: [], count: 0, detail: "Could not reach the server." },
      { status: 502 }
    );
  }
}
