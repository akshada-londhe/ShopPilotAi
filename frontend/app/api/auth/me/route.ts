// Next.js API route — proxy /auth/me to FastAPI backend
import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.SHOPPILOT_BACKEND_URL ?? "http://localhost:8000";

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
