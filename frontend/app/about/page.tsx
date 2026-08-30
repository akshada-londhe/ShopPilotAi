import Link from "next/link";
import { SiteHeader } from "../../components/shell/SiteHeader";

// Each pipeline stage explained for a non-technical person
const stages = [
  {
    number: "01",
    icon: "🗣️",
    title: "You ask in plain English",
    description:
      "Type exactly what you want — \"wireless headphones under ₹3000 with good bass\" — no special format needed. ShopPilot AI reads your words and extracts what matters: your budget, must-have features, and preferences.",
    tech: "Normalizer agent (LLM)",
  },
  {
    number: "02",
    icon: "🔍",
    title: "AI generates smart searches",
    description:
      "Instead of one keyword search, the AI creates several intelligent queries that cover what you asked from different angles. This is like having a research expert who knows exactly how stores list products.",
    tech: "Query Generator agent",
  },
  {
    number: "03",
    icon: "🌐",
    title: "Real products are fetched",
    description:
      "The AI searches the web in real-time using a specialised tool called Tavily, pulling actual product listings from Amazon, Flipkart, and other stores — not old cached data.",
    tech: "Tavily web search",
  },
  {
    number: "04",
    icon: "🧠",
    title: "Products are remembered",
    description:
      "Every product found is saved in a smart memory called ChromaDB, a vector database. Think of it as a super-organised filing cabinet that understands meaning, not just keywords. If you search for something similar soon after, results arrive instantly from memory.",
    tech: "ChromaDB vector database",
  },
  {
    number: "05",
    icon: "⚖️",
    title: "AI ranks the best match",
    description:
      "A Matcher agent compares every product against your exact requirements — budget, features, ratings, delivery options. It scores each product and puts the best one first.",
    tech: "Matcher agent (LLM)",
  },
  {
    number: "06",
    icon: "🕵️",
    title: "A second AI checks the work",
    description:
      "A Critic agent reviews the top result like a quality inspector. If it doesn't meet a certain standard, the whole process restarts with refined searches. This is why results are trustworthy, not just fast.",
    tech: "Critic agent (LLM)",
  },
  {
    number: "07",
    icon: "✍️",
    title: "You get a clear explanation",
    description:
      "A final Synthesizer agent writes the \"Why this is best for you\" section you see on the results page — no AI jargon, just honest reasons in plain English.",
    tech: "Synthesizer agent (LLM)",
  },
];

const values = [
  {
    emoji: "🚫",
    title: "No ads. No sponsored rankings.",
    description: "Results are ranked purely by how well they match what you asked.",
  },
  {
    emoji: "🔄",
    title: "Real-time, not outdated",
    description: "We fetch live listings, not cached data from months ago.",
  },
  {
    emoji: "🤔",
    title: "Self-checking AI",
    description:
      "Our Critic agent rejects poor results and retries — so you only see confident recommendations.",
  },
  {
    emoji: "🔒",
    title: "Your searches stay private",
    description: "We don't sell your data or use it to serve you ads.",
  },
];

export default function AboutPage() {
  return (
    <div className="min-h-dvh bg-white">
      <SiteHeader />

      <main>
        {/* ── Hero ── */}
        <section className="sp-container max-w-[1100px] pt-16 pb-10">
          <div className="max-w-[720px]">
            <p className="text-sm font-semibold uppercase tracking-widest text-[#6a4def]">
              About ShopPilot AI
            </p>
            <h1 className="mt-3 text-[46px] font-semibold leading-[1.1] tracking-[-.05em]">
              How ShopPilot AI finds<br />
              the <span className="sp-gradient-text">right product for you</span>
            </h1>
            <p className="mt-5 text-[18px] leading-8 text-[#6f7790]">
              Behind every recommendation is a team of AI agents working together —
              each with one job to do. Here&apos;s exactly what happens when you hit Search.
            </p>
          </div>
        </section>

        {/* ── Pipeline stages ── */}
        <section className="sp-container max-w-[1100px] pb-16">
          <div className="relative">
            {/* Vertical connector line */}
            <div className="absolute left-[27px] top-8 bottom-8 w-[2px] bg-gradient-to-b from-[#d4caf8] via-[#b8a8f0] to-[#d4caf8] md:left-[35px]" />

            <div className="space-y-8">
              {stages.map((stage) => (
                <div key={stage.number} className="relative flex items-start gap-6 md:gap-8">
                  {/* Step circle */}
                  <div className="relative z-10 grid h-14 w-14 shrink-0 place-items-center rounded-full bg-white border-2 border-[#c5b8f5] shadow-[0_4px_16px_rgba(100,78,220,.12)] text-2xl">
                    {stage.icon}
                  </div>

                  {/* Content card */}
                  <div className="flex-1 rounded-2xl border border-[#ede9fa] bg-white p-6 shadow-[0_6px_24px_rgba(60,44,140,.05)] transition-all hover:-translate-y-1 hover:shadow-[0_12px_36px_rgba(60,44,140,.11)]">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <span className="text-[11px] font-bold uppercase tracking-widest text-[#9b8fcc]">
                          Step {stage.number}
                        </span>
                        <h2 className="mt-1 text-[20px] font-semibold text-[#1a2045]">
                          {stage.title}
                        </h2>
                        <p className="mt-3 text-[15px] leading-7 text-[#5d6480]">
                          {stage.description}
                        </p>
                      </div>
                    </div>
                    {/* Tech badge */}
                    <div className="mt-4">
                      <span className="inline-flex items-center gap-1.5 rounded-full border border-[#e8e3f9] bg-[#f5f2ff] px-3 py-1 text-[12px] font-medium text-[#6b4de0]">
                        <span className="text-[10px]">⚙️</span> {stage.tech}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Why trust us ── */}
        <section className="border-t border-[#f0edf9] bg-[#faf8ff] py-16">
          <div className="sp-container max-w-[1100px]">
            <h2 className="text-[32px] font-semibold tracking-tight text-[#1a2045]">
              Why ShopPilot AI is different
            </h2>
            <div className="mt-8 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
              {values.map((v) => (
                <div
                  key={v.title}
                  className="rounded-2xl border border-[#ede9fa] bg-white p-6 shadow-[0_4px_18px_rgba(60,44,140,.05)]"
                >
                  <div className="text-[32px]">{v.emoji}</div>
                  <h3 className="mt-4 text-[16px] font-semibold text-[#1a2045]">{v.title}</h3>
                  <p className="mt-2 text-[14px] leading-6 text-[#6b7290]">{v.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── CTA ── */}
        <section className="py-16">
          <div className="sp-container max-w-[1100px] text-center">
            <h2 className="text-[28px] font-semibold text-[#1a2045]">Ready to shop smarter?</h2>
            <p className="mt-3 text-[16px] text-[#6b7290]">
              Type what you&apos;re looking for and let the agents do the work.
            </p>
            <Link href="/" className="sp-gradient-btn mt-8 inline-flex items-center gap-2 px-8 py-4 text-[15px] font-semibold">
              🛍️ Start searching
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}