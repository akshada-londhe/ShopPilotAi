"use client";

import { Search } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AppShell } from "../../components/shell/AppShell";
import { authHeaders } from "../../lib/auth-client";
import { useAuth } from "../../lib/auth-context";
import type { SearchHistoryItem } from "../../lib/types";

function formatWhen(iso: string): string {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "";
  return d.toLocaleString("en-US", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function HistoryPage() {
  const { user, loading: authLoading } = useAuth();
  const [rows, setRows] = useState<SearchHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/v1/history", { headers: authHeaders() });
        const data = await res.json();
        if (!cancelled) setRows(res.ok ? data.searches ?? [] : []);
      } catch {
        if (!cancelled) setRows([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [user, authLoading]);

  const filtered = useMemo(
    () => rows.filter((x) => x.query.toLowerCase().includes(filter.toLowerCase())),
    [rows, filter]
  );

  return (
    <AppShell>
      <div className="sp-app-container py-8">
        <h1 className="text-[30px] font-semibold">Search History</h1>
        <p className="mt-1 text-[15px] text-[#777e94]">Everything you have asked ShopPilot AI to find.</p>

        {authLoading || loading ? (
          <div className="mt-16 text-center text-[15px] text-[#8a90a8]">Loading your history…</div>
        ) : !user ? (
          <EmptyState
            emoji="🔒"
            title="Sign in to see your history"
            body="Your searches are saved to your account."
            cta={{ href: "/signin", label: "Sign in" }}
          />
        ) : rows.length === 0 ? (
          <EmptyState
            emoji="🔍"
            title="No searches yet"
            body="Your search history will appear here once you start searching for products."
            cta={{ href: "/", label: "Try a search" }}
          />
        ) : (
          <>
            <div className="mt-7 flex h-12 items-center rounded-xl border border-[#dddbea] bg-white px-4">
              <Search size={19} className="text-[#7c8296]" />
              <input
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                placeholder="Search your history"
                className="ml-3 flex-1 outline-none"
              />
            </div>
            <div className="sp-card mt-5 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[760px] text-left">
                  <thead className="border-b border-[#eceaf3] bg-[#fbfaff] text-[12px] text-[#767d93]">
                    <tr>
                      <th className="px-5 py-4">Search</th>
                      <th className="px-5 py-4">Best match</th>
                      <th className="px-5 py-4">Price</th>
                      <th className="px-5 py-4">Searched on</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((x, i) => (
                      <tr key={`${x.query}-${i}`} className="border-b border-[#f0eef5] last:border-0">
                        <td className="px-5 py-4 text-[13px] text-[#343b56]">
                          {x.best_match_url ? (
                            <a href={x.best_match_url} target="_blank" rel="noreferrer" className="hover:text-[#5f42ef]">
                              {x.query}
                            </a>
                          ) : (
                            x.query
                          )}
                        </td>
                        <td className="px-5 py-4 text-[13px] font-semibold">{x.best_match_name ?? "—"}</td>
                        <td className="px-5 py-4 text-[13px]">
                          {x.best_match_price != null ? `₹${x.best_match_price.toLocaleString("en-IN")}` : "—"}
                        </td>
                        <td className="px-5 py-4 text-[12px] text-[#777e94]">{formatWhen(x.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}

function EmptyState({
  emoji,
  title,
  body,
  cta,
}: {
  emoji: string;
  title: string;
  body: string;
  cta: { href: string; label: string };
}) {
  return (
    <div className="mt-16 flex flex-col items-center text-center text-[#8a90a8]">
      <div className="grid h-16 w-16 place-items-center rounded-2xl bg-[#f5f2ff] text-[28px]">{emoji}</div>
      <p className="mt-4 text-[15px] font-medium text-[#444c6a]">{title}</p>
      <p className="mt-2 max-w-[380px] text-[13px] leading-6 text-[#9099b4]">{body}</p>
      <Link href={cta.href} className="sp-gradient-btn mt-6 inline-flex items-center px-6 py-2.5 text-[13px] font-semibold">
        {cta.label}
      </Link>
    </div>
  );
}
