"use client";

import Link from "next/link";
import { Heart, ExternalLink } from "lucide-react";
import { useEffect, useState } from "react";
import { AppShell } from "../../components/shell/AppShell";
import { authHeaders } from "../../lib/auth-client";
import { useAuth } from "../../lib/auth-context";
import type { SavedItem } from "../../lib/types";

export default function SavedPage() {
  const { user, loading: authLoading } = useAuth();
  const [items, setItems] = useState<SavedItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/v1/saved", { headers: authHeaders() });
        const data = await res.json();
        if (!cancelled) setItems(res.ok ? data.products ?? [] : []);
      } catch {
        if (!cancelled) setItems([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [user, authLoading]);

  async function unsave(item: SavedItem) {
    // Optimistic removal.
    const prev = items;
    setItems((list) => list.filter((x) => x.name !== item.name || x.link !== item.link));
    try {
      const res = await fetch("/api/v1/saved", {
        method: "DELETE",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ name: item.name, link: item.link }),
      });
      if (!res.ok) setItems(prev); // restore on failure
    } catch {
      setItems(prev);
    }
  }

  return (
    <AppShell>
      <div className="sp-app-container py-8">
        <div className="flex items-end justify-between">
          <div>
            <h1 className="text-[30px] font-semibold">Saved Items</h1>
            <p className="mt-1 text-[15px] text-[#777e94]">Products you want to come back to.</p>
          </div>
          {user && items.length > 0 && (
            <span className="rounded-full bg-[#f2efff] px-3 py-1.5 text-[12px] font-medium text-[#684cef]">
              {items.length} saved
            </span>
          )}
        </div>

        {authLoading || loading ? (
          <div className="mt-16 text-center text-[15px] text-[#8a90a8]">Loading your saved items…</div>
        ) : !user ? (
          <EmptyState
            emoji="🔒"
            title="Sign in to see saved items"
            body="Save products from any search and find them here."
            cta={{ href: "/signin", label: "Sign in" }}
          />
        ) : items.length === 0 ? (
          <EmptyState
            emoji="🛍️"
            title="Nothing saved yet"
            body="Tap the heart on any product in your search results to save it here."
            cta={{ href: "/", label: "Start a search" }}
          />
        ) : (
          <div className="mt-7 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {items.map((item) => (
              <article
                key={`${item.name}-${item.link}`}
                className="rounded-2xl border border-[#eceaf4] bg-white p-5 shadow-[0_8px_24px_rgba(55,42,137,.04)]"
              >
                <div className="flex items-start justify-between gap-3">
                  <h2 className="text-[16px] font-semibold leading-6">{item.name}</h2>
                  <button
                    aria-label={`Remove ${item.name} from saved`}
                    onClick={() => unsave(item)}
                    className="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-[#e6e3ef] text-[#e5557a] transition hover:bg-[#fdf1f4]"
                  >
                    <Heart size={17} fill="currentColor" />
                  </button>
                </div>
                {item.merchant && <div className="mt-1 text-[12px] text-[#757c91]">{item.merchant}</div>}
                <div className="mt-4 text-[23px] font-semibold">
                  {item.price != null ? `₹${item.price.toLocaleString("en-IN")}` : "Price unavailable"}
                </div>
                {item.link ? (
                  <a
                    href={item.link}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-4 flex h-11 items-center justify-center gap-2 rounded-xl border border-[#dcd8ef] text-[13px] font-medium text-[#6348ef] hover:bg-[#faf8ff]"
                  >
                    View product <ExternalLink size={16} />
                  </a>
                ) : (
                  <div className="mt-4 flex h-11 items-center justify-center rounded-xl bg-[#f2f2f6] text-[13px] font-medium text-[#9099b4]">
                    Link unavailable
                  </div>
                )}
              </article>
            ))}
          </div>
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
