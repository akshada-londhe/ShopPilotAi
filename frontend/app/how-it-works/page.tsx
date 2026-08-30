import { SearchCheck, SlidersHorizontal, Sparkles, BadgeCheck } from "lucide-react";
import { SiteHeader } from "../../components/shell/SiteHeader";

const steps = [
  [SearchCheck, "Tell us what you need", "Use normal language. Include budget, use case, preferred brands or hard constraints."],
  [SlidersHorizontal, "We structure the request", "Your query is normalized into intent, constraints and relevant ranking signals."],
  [Sparkles, "The agent finds the strongest fit", "The search pipeline retrieves candidate products and scores how well they match."],
  [BadgeCheck, "You get a decision-ready answer", "One best match comes first, with a compact set of alternatives and reasons."],
] as const;

export default function HowItWorksPage() {
  return <div className="min-h-dvh bg-white"><SiteHeader /><main className="sp-container max-w-[1050px] py-20"><p className="text-sm font-semibold text-[#6a4def]">HOW IT WORKS</p><h1 className="mt-3 text-[48px] font-semibold tracking-[-.05em]">From &quot;what should I buy?&quot; to a confident choice.</h1><div className="mt-12 space-y-5">{steps.map(([Icon, title, copy], i) => <div key={title} className="sp-card flex gap-6 p-6 md:p-7"><div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-[#f0ecff] text-[#664bed]"><Icon size={22} /></div><div><div className="text-[13px] font-semibold text-[#684cef]">0{i + 1}</div><h2 className="mt-1 text-[20px] font-semibold">{title}</h2><p className="mt-2 max-w-[720px] text-[14px] leading-6 text-[#747b92]">{copy}</p></div></div>)}</div></main></div>;
}