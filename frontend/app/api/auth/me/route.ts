// Next.js API route — proxy /auth/me to FastAPI backend
import { NextRequest, NextResponse } from "next/server";

const getBackendUrl = () => {
  if (process.env.SHOPPILOT_BACKEND_URL) return process.env.SHOPPILOT_BACKEND_URL;
  if (process.env.VERCEL_URL) return `https://${process.env.VERCEL_URL}`;
  return "http://localhost:8000";
};
const BACKEND_URL = getBackendUrl();

export async function GET(req: NextRequest) {
  const authHeader = req.headers.get("Authorization") ?? "";
  if (!authHeader.startsWith("Bearer ")) {
    return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${BACKEND_URL}/auth/me`, {
      headers: { Authorization: authHeader },
    });
  } catch {
    return NextResponse.json(
      { detail: "Could not reach the server." },
      { status: 502 }
    );
  }

  const data = await upstream.json().catch(() => ({}));
  return NextResponse.json(data, { status: upstream.status });
}
