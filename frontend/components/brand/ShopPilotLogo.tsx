import Link from "next/link";

export function ShopPilotLogo({ compact = false }: { compact?: boolean }) {
  return (
    <Link href="/" aria-label="ShopPilot AI home" className="inline-flex items-center gap-3">
      <span
        className="grid h-11 w-11 shrink-0 place-items-center rounded-[14px] text-white shadow-[0_10px_24px_rgba(100,84,235,.25)]"
        style={{ background: "linear-gradient(135deg,#4b7cff,#7a55ef,#c553dc)" }}
      >
        <span className="relative block h-6 w-6 rounded-[7px] border-2 border-white/85">
          <span className="absolute -top-[8px] left-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-t-full border-2 border-b-0 border-white/90" />
          <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-[14px]">✦</span>
        </span>
      </span>
      {!compact && (
        <span className="text-[25px] font-semibold tracking-[-.04em]">
          <span>Shop</span><span className="sp-gradient-text">Pilot AI</span>
        </span>
      )}
    </Link>
  );
}