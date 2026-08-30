import type { ProductResult } from "./types";

// A view model that exposes ONLY data the pipeline actually extracted.
// Anything the backend didn't provide stays null/undefined so the UI can
// hide it rather than fabricate a value (PRD FR7: literal extraction only,
// no inferred fields; Goal 1: never fabricated).
export type ProductViewModel = ProductResult & {
  imageUrl: string | null;
  rating: number | null;
  ratingCount: string | null;
  merchant: string | null;
  sourceUrl: string | null;
  highlights: string[];
};

function fieldValue(product: ProductResult, key: string): string | number | boolean | undefined {
  return product.fields?.[key]?.value;
}

function firstSourceUrl(product: ProductResult): string | null {
  const named = product.fields?.name?.source_url;
  if (named) return String(named);
  for (const f of Object.values(product.fields ?? {})) {
    if (f?.source_url) return String(f.source_url);
  }
  return null;
}

function realImage(product: ProductResult): string | null {
  const raw = String(fieldValue(product, "image_url") ?? fieldValue(product, "image") ?? "");
  // Only trust a real, non-placeholder http image the extractor captured.
  if (raw.startsWith("http") && !raw.includes("placeholder")) return raw;
  return null;
}

function realRating(product: ProductResult): number | null {
  const raw = fieldValue(product, "rating");
  if (raw == null) return null;
  const n = Number(raw);
  return Number.isFinite(n) && n > 0 && n <= 5 ? n : null;
}

function realRatingCount(product: ProductResult): string | null {
  const raw = fieldValue(product, "rating_count");
  return raw != null && String(raw).trim() ? String(raw) : null;
}

function realMerchant(product: ProductResult): string | null {
  const raw = fieldValue(product, "merchant") ?? fieldValue(product, "store");
  if (raw && String(raw).trim()) return String(raw);
  // Derive from the source domain if we have a URL (this is real, not invented).
  const url = firstSourceUrl(product);
  if (url) {
    try {
      const host = new URL(url).hostname.replace(/^www\./, "");
      if (host.includes("amazon")) return "Amazon";
      if (host.includes("flipkart")) return "Flipkart";
      if (host.includes("croma")) return "Croma";
      return host;
    } catch {
      return null;
    }
  }
  return null;
}

export function toProductViewModel(product: ProductResult): ProductViewModel {
  return {
    ...product,
    imageUrl: realImage(product),
    rating: realRating(product),
    ratingCount: realRatingCount(product),
    merchant: realMerchant(product),
    sourceUrl: firstSourceUrl(product),
    // Highlights are only the real matched hard constraints. If none matched,
    // show nothing rather than invent "Best Value / High Rated".
    highlights: product.matched_constraints ?? [],
  };
}
