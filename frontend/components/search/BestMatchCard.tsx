import { Check, ExternalLink, Heart, Sparkles, Star } from "lucide-react";
import type { ProductViewModel } from "../../lib/product-view";

export function BestMatchCard({
  product,
  onSave,
  saved = false,
  verified = true,
  rationale,
  synthesis,
}: {
  product: ProductViewModel;
  onSave?: () => void;
  saved?: boolean;
  verified?: boolean;
  rationale?: string | null;
  synthesis?: string | null;
}) {
  const hasConstraints = product.highlights.length > 0;
  const specs = Object.entries(product.fields ?? {})
    .filter(([k]) => k.startsWith("spec_"))
    .map(([, f]) => String(f.value))
    .filter(Boolean)
    .slice(0, 6);

  // The agent's reasoning for this pick: prefer the synthesis paragraph,
  // fall back to the critic's rationale. Both are real model output.
  const reasoning = (synthesis && synthesis.trim()) || (rationale && rationale.trim()) || null;

  return (
    <article className="overflow-hidden rounded-[22px] border border-[#ebe9f4] bg-white shadow-[0_10px_30px_rgba(61,48,129,.06)]">
      <div className="grid gap-6 p-6 lg:grid-cols-[minmax(0,1fr)_340px] lg:p-7">
        <div className="flex min-w-0 flex-col">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <span
                className={`inline-block rounded-full px-3 py-1 text-[12px] font-semibold text-white ${
                  verified
                    ? "bg-gradient-to-r from-[#5c5af3] to-[#914eed]"
                    : "bg-gradient-to-r from-[#d99717] to-[#e0761d]"
                }`}
              >
                {verified ? "★ Best Match" : "Closest available"}
              </span>
              <h2 className="mt-3 text-[25px] font-semibold tracking-[-.025em] text-[#171d3d]">{product.name}</h2>
            </div>
            <button
              onClick={onSave}
              aria-label={saved ? "Saved" : "Save product"}
              aria-pressed={saved}
              className={`sp-btn-icon h-10 w-10 shrink-0 ${saved ? "border-[#f2c2ce] bg-[#fdf1f4] text-[#e5557a]" : ""}`}
            >
              <Heart size={19} fill={saved ? "currentColor" : "none"} />
            </button>
          </div>

          {/* Rating only if actually extracted. */}
          {product.rating != null && (
            <div className="mt-3 flex items-center gap-2">
              <div className="flex items-center gap-0.5 text-[#f5a724]">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star key={i} size={16} fill={i < Math.round(product.rating!) ? "currentColor" : "none"} />
                ))}
              </div>
              <span className="font-semibold text-[#40475f]">{product.rating}</span>
              {product.ratingCount && <span className="text-[13px] text-[#6f7690]">({product.ratingCount})</span>}
            </div>
          )}

          <div className="mt-4 flex items-end gap-3">
            <span className="text-[28px] font-semibold text-[#141a3c]">
              {product.price == null ? "Price unavailable" : `₹${product.price.toLocaleString("en-IN")}`}
            </span>
            {product.merchant && <span className="pb-1 text-[13px] font-semibold text-[#252b47]">{product.merchant}</span>}
          </div>

          {/* Why the agent chose this — real model reasoning. */}
          <div className="mt-5 rounded-2xl border border-[#eae6f8] bg-[#faf9ff] p-4">
            <div className="flex items-center gap-2 text-[13px] font-semibold text-[#5a3edb]">
              <Sparkles size={15} /> Why the agent chose this
            </div>
            {reasoning ? (
              <p className="mt-2 text-[13px] leading-6 text-[#535a76]">{reasoning}</p>
            ) : (
              <p className="mt-2 text-[13px] leading-6 text-[#8a90a6]">
                Ranked on overall relevance to your query and the evidence available.
              </p>
            )}
          </div>

          {/* Real product info: extracted specs. */}
          {specs.length > 0 && (
            <div className="mt-4">
              <div className="text-[13px] font-semibold text-[#2d3452]">Product details</div>
              <div className="mt-2 flex flex-wrap gap-2">
                {specs.map((s, i) => (
                  <span key={`${s}-${i}`} className="rounded-lg bg-[#f2f0fb] px-2.5 py-1 text-[12px] text-[#4a5170]">{s}</span>
                ))}
              </div>
            </div>
          )}

          <div className="mt-6">
            {product.sourceUrl ? (
              <a href={product.sourceUrl} target="_blank" rel="noreferrer" className="sp-gradient-btn inline-flex h-11 items-center justify-center gap-2 px-6 text-[14px] font-semibold">
                View product <ExternalLink size={16} />
              </a>
            ) : (
              <button disabled className="h-11 rounded-xl bg-[#ececf1] px-6 text-[14px] font-semibold text-[#818697]">Product link unavailable</button>
            )}
          </div>
        </div>

        <div className="rounded-2xl bg-[#fafaff] p-6">
          <h3 className="text-[18px] font-semibold">
            {hasConstraints ? "Requirements it meets" : "Match summary"}
          </h3>
          {hasConstraints ? (
            <div className="mt-5 space-y-4">
              {product.highlights.map((reason) => (
                <div key={reason} className="flex gap-3 text-[14px] leading-6 text-[#555d76]">
                  <Check size={18} className="mt-1 shrink-0 text-[#5d51f4]" />
                  {reason}
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-4 text-[13px] leading-6 text-[#7a8195]">
              No explicit hard constraints were specified, so this is ranked on overall relevance to your query.
            </p>
          )}
          <div className="mt-6 rounded-2xl bg-white p-4 shadow-[0_6px_20px_rgba(50,44,111,.05)]">
            <div className="text-[14px] font-semibold">Match quality</div>
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-[#edeaf8]">
              <div className="h-full rounded-full bg-gradient-to-r from-[#567cff] to-[#bf57dc]" style={{ width: `${Math.min(100, Math.max(8, product.soft_score * 10))}%` }} />
            </div>
            <div className="mt-2 text-[12px] text-[#7a8195]">Score {product.soft_score.toFixed(1)}/10, based on constraints, relevance, and available evidence</div>
          </div>
        </div>
      </div>
    </article>
  );
}
