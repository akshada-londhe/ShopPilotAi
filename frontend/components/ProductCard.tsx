"use client";

import { ExternalLink, CheckCircle2, Star, ShoppingCart } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatINR } from "@/lib/utils";
import type { ProductResult } from "@/lib/types";

interface ProductCardProps {
  product: ProductResult;
}

function isDirectAmazonUrl(url: string): boolean {
  const lower = url.toLowerCase();
  if (!lower.includes("amazon.in")) return false;
  if (lower.includes("/s?") || lower.includes("/s/") || lower.includes("/gp/browse") || lower.includes("/b?")) {
    return false;
  }
  return (
    lower.includes("/dp/") ||
    lower.includes("/gp/product/") ||
    lower.includes("/product/") ||
    lower.includes("/d/") ||
    /\/(?:dp|gp\/product|product|d)\/[a-z0-9]+/i.test(lower)
  );
}

function isDirectFlipkartUrl(url: string): boolean {
  const lower = url.toLowerCase();
  if (!lower.includes("flipkart.com")) return false;
  if (lower.includes("/search?") || lower.includes("/pr?sid=")) {
    return false;
  }
  return (
    lower.includes("/p/") ||
    lower.includes("/product/") ||
    lower.includes("pid=") ||
    /\/p\/[a-z0-9]+/i.test(lower)
  );
}

function cleanProductName(name: string): string {
  if (!name) return "";
  let cleaned = name
    .replace(/\(.*?\)/g, "")
    .replace(/\[.*?\]/g, "")
    .replace(/(?:₹|Rs\.?|INR)\s*[\d,]+/gi, "")
    .replace(/[,|]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  const keywords = [
    " with ",
    " featuring ",
    " dual ",
    " triple-mode",
    " adjustable ",
    " hot-swappable",
    " pixart",
    " 12000 dpi",
    " lightweight",
    " 80hrs",
  ];
  const lower = cleaned.toLowerCase();
  let cutoff = cleaned.length;
  for (const kw of keywords) {
    const idx = lower.indexOf(kw);
    if (idx !== -1 && idx > 4 && idx < cutoff) {
      cutoff = idx;
    }
  }
  cleaned = cleaned.substring(0, cutoff).trim();

  const words = cleaned.split(/\s+/).filter(Boolean);
  if (words.length > 7) {
    cleaned = words.slice(0, 7).join(" ");
  }

  return cleaned || name;
}

function safeUrl(url: string | undefined): string | null {
  if (!url) return null;
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== "https:" && parsed.protocol !== "http:") return null;
    return parsed.toString();
  } catch {
    return null;
  }
}

function getDirectStoreUrls(product: ProductResult) {
  const fields = Object.values(product.fields);
  const rawUrls = fields.map((f) => safeUrl(f.source_url)).filter((u): u is string => Boolean(u));

  const cleanName = cleanProductName(product.name);
  const encodedName = encodeURIComponent(cleanName || product.name);

  const amazonDirect = rawUrls.find((url) => isDirectAmazonUrl(url));
  const flipkartDirect = rawUrls.find((url) => isDirectFlipkartUrl(url));

  const amazonBuyUrl = amazonDirect || `https://www.amazon.in/s?k=${encodedName}`;
  const flipkartBuyUrl = flipkartDirect || `https://www.flipkart.com/search?q=${encodedName}`;

  let primaryUrl = amazonBuyUrl;
  if (amazonDirect) {
    primaryUrl = amazonDirect;
  } else if (flipkartDirect) {
    primaryUrl = flipkartDirect;
  } else if (rawUrls.some((u) => u.toLowerCase().includes("flipkart.com"))) {
    primaryUrl = flipkartBuyUrl;
  }

  return { amazonBuyUrl, flipkartBuyUrl, primaryUrl };
}

export function ProductCard({ product }: ProductCardProps) {
  const { amazonBuyUrl, flipkartBuyUrl, primaryUrl } = getDirectStoreUrls(product);

  const specFields = Object.entries(product.fields)
    .filter(([name]) => name.startsWith("spec_"))
    .slice(0, 4);

  return (
    <Card className="group flex h-[300px] flex-col justify-between overflow-hidden rounded-xl border-border/80 bg-card/90 backdrop-blur-xs transition-all duration-200 hover:border-primary/60 hover:shadow-xl hover:shadow-primary/5 animate-[fade-in-up_0.25s_ease-out_both]">
      <div className="flex min-h-0 flex-1 flex-col">
        <CardHeader className="shrink-0 p-3.5 pb-2">
          <div className="flex items-start justify-between gap-2">
            <a
              href={primaryUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 transition-colors hover:text-primary"
              title="Open product page directly"
            >
              <CardTitle className="line-clamp-2 h-9 text-xs font-semibold leading-snug sm:text-sm">
                {product.name}
              </CardTitle>
            </a>
            <a
              href={primaryUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 rounded p-0.5 text-muted-foreground/70 transition-colors hover:text-primary"
              aria-label="Open source page"
            >
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </div>

          <div className="mt-1.5 flex items-center justify-between gap-2 pt-0.5">
            <div>
              {product.price !== null && product.price > 0 ? (
                <span className="text-base font-extrabold tracking-tight text-foreground sm:text-lg">
                  {formatINR(product.price)}
                </span>
              ) : (
                <span className="text-xs italic text-muted-foreground">Not specified</span>
              )}
            </div>

            <div className="flex items-center gap-1 rounded-full border border-primary/20 bg-primary/10 px-2 py-0.5">
              <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
              <span className="text-[11px] font-bold text-primary">
                {product.soft_score.toFixed(1)}
              </span>
            </div>
          </div>
        </CardHeader>

        <CardContent className="flex min-h-0 flex-1 flex-col gap-2 overflow-hidden p-3.5 pt-1">
          {product.matched_constraints.length > 0 && (
            <div className="flex flex-wrap gap-1 overflow-hidden">
              {product.matched_constraints.slice(0, 3).map((c) => (
                <Badge key={c} variant="success" className="gap-1 rounded-md px-1.5 py-0 text-[10px] font-medium">
                  <CheckCircle2 className="h-2.5 w-2.5" />
                  {c}
                </Badge>
              ))}
            </div>
          )}

          {specFields.length > 0 && (
            <div className="border-t border-border/40 pt-1.5">
              <div className="flex flex-wrap gap-1">
                {specFields.map(([name, field]) => (
                  <div
                    key={name}
                    className="inline-flex items-center gap-1 rounded-md border border-border/40 bg-secondary/60 px-2 py-0.5 text-[10.5px] text-foreground/80 transition-colors hover:bg-secondary"
                  >
                    <span className="h-1 w-1 shrink-0 rounded-full bg-primary" />
                    <span className="max-w-[160px] truncate">{String(field.value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </div>

      {/* ── Buy action buttons ── */}
      <div className="mt-2 flex shrink-0 items-center gap-1.5 border-t border-border/40 bg-secondary/25 p-3 pt-2">
        <a
          href={amazonBuyUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex flex-1 items-center justify-center gap-1 rounded-lg border border-amber-500/40 bg-amber-500/15 px-2 py-1.5 text-[11px] font-bold text-amber-700 shadow-2xs transition-all hover:scale-[1.02] hover:bg-amber-500/25 active:scale-[0.98] dark:text-amber-300"
        >
          <ShoppingCart className="h-3 w-3" />
          <span>Amazon</span>
          <ExternalLink className="h-2.5 w-2.5 opacity-75" />
        </a>

        <a
          href={flipkartBuyUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex flex-1 items-center justify-center gap-1 rounded-lg border border-sky-500/40 bg-sky-500/15 px-2 py-1.5 text-[11px] font-bold text-sky-700 shadow-2xs transition-all hover:scale-[1.02] hover:bg-sky-500/25 active:scale-[0.98] dark:text-sky-300"
        >
          <ShoppingCart className="h-3 w-3" />
          <span>Flipkart</span>
          <ExternalLink className="h-2.5 w-2.5 opacity-75" />
        </a>
      </div>
    </Card>
  );
}