import { Heart, Star } from "lucide-react";
import type { ProductViewModel } from "../../lib/product-view";

export function AlternativeRail({
  products,
  onSave,
  isSaved,
}: {
  products: ProductViewModel[];
  onSave?: (product: ProductViewModel) => void;
  isSaved?: (product: ProductViewModel) => boolean;
}) {
  if (products.length === 0) return null;
  return (
    <section className="mt-7">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-[20px] font-semibold">Other great alternatives</h2>
          <p className="mt-1 text-[14px] text-[#737b94]">Top picks that also match your search</p>
        </div>
      </div>
      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {products.slice(0, 3).map((product, i) => {
          const specs = Object.entries(product.fields ?? {})
            .filter(([k]) => k.startsWith("spec_"))
            .map(([, f]) => String(f.value))
            .filter(Boolean)
            .slice(0, 3);
          return (
            <article key={`${product.name}-${i}`} className="sp-product-card relative flex flex-col p-4">
              <button
                aria-label={isSaved?.(product) ? `${product.name} saved` : `Save ${product.name}`}
                aria-pressed={isSaved?.(product) ?? false}
                onClick={() => onSave?.(product)}
                className={`sp-btn-icon absolute right-4 top-4 h-8 w-8 ${
                  isSaved?.(product) ? "border-[#f2c2ce] bg-[#fdf1f4] text-[#e5557a]" : "text-[#737a91]"
                }`}
              >
                <Heart size={16} fill={isSaved?.(product) ? "currentColor" : "none"} />
              </button>
              <h3 className="pr-8 text-[14px] font-semibold leading-5 text-[#1b2242]">{product.name}</h3>
              {product.rating != null && (
                <div className="mt-2 flex items-center gap-1 text-[12px]">
                  <Star size={13} fill="#f4aa24" className="text-[#f4aa24]" /> {product.rating}
                  {product.ratingCount && <span className="text-[#80869a]">({product.ratingCount})</span>}
                </div>
              )}
              <div className="mt-2 text-[18px] font-semibold">
                {product.price == null ? "Price unavailable" : `₹${product.price.toLocaleString("en-IN")}`}
              </div>
              {product.matched_constraints.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {product.matched_constraints.slice(0, 3).map((c) => (
                    <span key={c} className="rounded-full bg-[#eff9f4] px-2 py-0.5 text-[11px] text-[#25825e]">✓ {c}</span>
                  ))}
                </div>
              )}
              {specs.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {specs.map((s, j) => (
                    <span key={`${s}-${j}`} className="rounded-md bg-[#f2f0fb] px-2 py-0.5 text-[11px] text-[#4a5170]">{s}</span>
                  ))}
                </div>
              )}
              {(product.merchant || product.sourceUrl) && (
                <div className="mt-auto flex items-center justify-between border-t border-[#f0eef5] pt-3 text-[12px] text-[#6d7489]">
                  <span>{product.merchant ?? "Source"}</span>
                  {product.sourceUrl && (
                    <a href={product.sourceUrl} target="_blank" rel="noreferrer" className="font-medium text-[#6348ef]">View</a>
                  )}
                </div>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}
