"use client";

import { Bookmark, ExternalLink, PackageSearch, Search as SearchIcon, Sparkles } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AppShell } from "../../components/shell/AppShell";
import { MetricCard } from "../../components/dashboard/MetricCard";
import { authHeaders } from "../../lib/auth-client";
import { useAuth } from "../../lib/auth-context";
import type { SavedItem, SearchHistoryItem } from "../../lib/types";

function formatWhen(iso: string): string {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "";
  return d.toLocaleString("en-US", {
    day: "numeric",
    month: "short",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);
  const [saved, setSaved] = useState<SavedItem[]>([]);
  const [loading, setLoading] = useState(true);

  const firstName = user?.name?.split(" ")[0] ?? "there";

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const [hRes, sRes] = await Promise.all([
          fetch("/api/v1/history", { headers: authHeaders() }),
          fetch("/api/v1/saved", { headers: authHeaders() }),
        ]);
        const hData = await hRes.json().catch(() => ({}));
        const sData = await sRes.json().catch(() => ({}));
        if (!cancelled) {
          setHistory(hRes.ok ? hData.searches ?? [] : []);
          setSaved(sRes.ok ? sData.products ?? [] : []);
        }
      } catch {
        if (!cancelled) {
          setHistory([]);
          setSaved([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [user, authLoading]);

  const recent = useMemo(() => history.slice(0, 6), [history]);
  // Products analysed: every search that produced a best match counts as at
  // least one product the agent verified for you. Real, not fabricated.
  const productsAnalysed = useMemo(
    () => history.filter((h) => h.best_match_name).length,
    [history]
  );

  const busy = authLoading || loading;

  return (
    <AppShell>
      <div className="sp-app-container flex min-h-full flex-col py-5">
        <header>
          <h1 className="text-[26px] font-semibold tracking-[-.04em]">
            Welcome back, {firstName} 👋
          </h1>
          <p className="mt-0.5 text-[14px] text-[#737b93]">Here&apos;s your shopping intelligence hub</p>
        </header>

        {/* Metrics */}
        <section className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            title="Total Searches"
            value={busy ? "…" : history.length}
            delta={history.length === 0 ? "Start searching!" : "Across your account"}
            Icon={SearchIcon}
          />
          <MetricCard
            title="Products Analysed"
            value={busy ? "…" : productsAnalysed}
            delta={productsAnalysed === 0 ? "Your AI picks will show here" : "Verified best matches"}
            Icon={PackageSearch}
          />
          <MetricCard
            title="Items Saved"
            value={busy ? "…" : saved.length}
            action="View saved"
            Icon={Bookmark}
          />
        </section>

        <section className="mt-5 grid min-h-0 flex-1 gap-5 xl:grid-cols-[minmax(0,1fr)_290px]">
          {/* Recent searches */}
          <div className="sp-card flex min-h-0 flex-col overflow-hidden">
            <div className="flex items-center justify-between border-b border-[#efedf5] px-5 py-4">
              <div className="text-[16px] font-semibold">Recent Searches</div>
              {history.length > 0 && (
                <Link href="/history" className="text-[12px] font-medium text-[#674cf0]">
                  View all
                </Link>
              )}
            </div>

            {busy ? (
              <div className="flex flex-1 items-center justify-center py-12 text-[14px] text-[#8a90a8]">
                Loading your activity…
              </div>
            ) : !user ? (
              <DashEmpty
                emoji="🔒"
                title="Sign in to see your activity"
                body="Your searches and saved items live in your account."
                cta={{ href: "/signin", label: "Sign in" }}
              />
            ) : recent.length === 0 ? (
              <DashEmpty
                emoji="🔍"
                title="No searches yet"
                body="Your search history will appear here once you start searching for products."
                cta={{ href: "/", label: "Try a search" }}
              />
            ) : (
              <ul className="flex-1 divide-y divide-[#f0eef5] overflow-y-auto">
                {recent.map((row, i) => (
                  <li key={`${row.query}-${i}`} className="flex items-center gap-4 px-5 py-3.5">
                    <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#f5f2ff] text-[#6a4cf0]">
                      <SearchIcon size={17} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-[14px] font-medium text-[#28304f]">{row.query}</div>
                      <div className="mt-0.5 truncate text-[12px] text-[#8a90a8]">
                        {row.best_match_name ? `Top match: ${row.best_match_name}` : "No verified match"}
                        {row.created_at ? ` · ${formatWhen(row.created_at)}` : ""}
                      </div>
                    </div>
                    {row.best_match_price != null && (
                      <div className="shrink-0 text-[13px] font-semibold text-[#28304f]">
                        ₹{row.best_match_price.toLocaleString("en-IN")}
                      </div>
                    )}
                    {row.best_match_url && (
                      <a
                        href={row.best_match_url}
                        target="_blank"
                        rel="noreferrer"
                        aria-label={`Open ${row.best_match_name ?? row.query}`}
                        className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-[#6348ef] hover:bg-[#f6f3ff]"
                      >
                        <ExternalLink size={15} />
                      </a>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Right sidebar */}
          <aside className="space-y-5">
            {/* Saved items preview */}
            <div className="sp-card p-5">
              <div className="flex items-center justify-between">
                <h2 className="text-[16px] font-semibold">Saved Items</h2>
                <Link href="/saved" className="text-[12px] font-medium text-[#674cf0]">View all</Link>
              </div>

              {busy ? (
                <p className="mt-4 text-[12px] text-[#8a90a8]">Loading…</p>
              ) : saved.length === 0 ? (
                <div className="mt-5 flex flex-col items-center py-6 text-center text-[#9099b4]">
                  <div className="text-[28px]">🛍️</div>
                  <p className="mt-3 text-[12px] leading-5">
                    Heart a product on any search result to save it here.
                  </p>
                </div>
              ) : (
                <ul className="mt-4 space-y-3">
                  {saved.slice(0, 4).map((item) => (
                    <li key={`${item.name}-${item.link}`} className="flex items-center gap-3">
                      <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-[#f5f2ff] text-[16px]">
                        🛍️
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-[13px] font-medium text-[#28304f]">{item.name}</div>
                        <div className="text-[12px] text-[#8a90a8]">
                          {item.price != null ? `₹${item.price.toLocaleString("en-IN")}` : "Price unavailable"}
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )}

              <Link
                href="/saved"
                className="mt-4 block rounded-xl border border-[#dcd8ef] py-3 text-center text-[13px] font-medium text-[#6348ef]"
              >
                Go to Saved Items →
              </Link>
            </div>
          </aside>
        </section>
      </div>
    </AppShell>
  );
}

function DashEmpty({
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
    <div className="flex flex-1 flex-col items-center justify-center px-8 py-8 text-center text-[#8a90a8]">
      <div className="grid h-16 w-16 place-items-center rounded-2xl bg-[#f5f2ff] text-[28px]">{emoji}</div>
      <p className="mt-4 text-[15px] font-medium text-[#444c6a]">{title}</p>
      <p className="mt-2 max-w-[320px] text-[13px] leading-6 text-[#9099b4]">{body}</p>
      <Link
        href={cta.href}
        className="sp-gradient-btn mt-6 inline-flex items-center gap-2 px-5 py-2.5 text-[13px] font-semibold"
      >
        <Sparkles size={14} /> {cta.label}
      </Link>
    </div>
  );
}
