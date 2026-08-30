"use client";

import { ArrowLeft, Heart, Link as LinkIcon, Search, Sparkles } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { streamSearch } from "../../lib/sse-client";
import type { ClarificationContext, SearchResultPayload, SSEEvent } from "../../lib/types";
import { toProductViewModel, type ProductViewModel } from "../../lib/product-view";
import { authHeaders } from "../../lib/auth-client";
import { useAuth } from "../../lib/auth-context";
import { BestMatchCard } from "./BestMatchCard";
import { AlternativeRail } from "./AlternativeRail";
import { ClarificationPrompt } from "../ClarificationPrompt";

// Story-based progress steps matching reference design
const STORY_STEPS = [
  {
    step: 1,
    title: "1. Understanding your need",
    subtitle: "Our AI is reading your query and extracting requirements",
    icon: "🤖",
    bgMsg: "Analyzing your query and extracting key requirements...",
    caption: "AI understands the user's query and extracts key intents & constraints.",
  },
  {
    step: 2,
    title: "2. Searching the web",
    subtitle: "Finding relevant products from top online stores",
    icon: "🌐",
    bgMsg: "Searching multiple stores for best matching products...",
    caption: "We explore multiple stores to discover the most relevant products.",
  },
  {
    step: 3,
    title: "3. Extracting product details",
    subtitle: "Collecting & extracting price, specs and reviews",
    icon: "📦",
    bgMsg: "Extracting product details, price, ratings, features & more...",
    caption: "Our AI extracts key information like price, ratings, features & availability.",
  },
  {
    step: 4,
    title: "4. Filtering & validating",
    subtitle: "Applying budget & constraints to remove irrelevant items",
    icon: "⚡",
    bgMsg: "Applying your budget, preferences and removing irrelevant items...",
    caption: "We filter out products that don't match your requirements and budget.",
  },
  {
    step: 5,
    title: "5. Ranking the best matches",
    subtitle: "Scoring products based on value and user satisfaction",
    icon: "🏆",
    bgMsg: "Ranking products based on relevance, value & user satisfaction...",
    caption: "Products are scored and ranked to find the absolute best match for you.",
  },
  {
    step: 6,
    title: "6. Preparing your results",
    subtitle: "Almost done! Crafting recommendations",
    icon: "✨",
    bgMsg: "Finalizing results and preparing a personalized shopping summary...",
    caption: "We are preparing your personalized results with top recommendations.",
  },
];

function stageToStep(progressMsg: string, stage?: string): number {
  if (stage === "normalizing" || stage === "pipeline_started") return 1;
  if (stage === "retrying" || stage === "generating" || stage === "searching" || stage === "cache_check") return 2;
  if (stage === "extracting" || stage === "sanitizing" || stage === "cache_hit") return 3;
  if (stage === "matching" || stage === "filter") return 4;
  if (stage === "critiquing" || stage === "critic") return 5;
  if (stage === "synthesizing" || stage === "done" || stage === "result") return 6;

  const lower = progressMsg.toLowerCase();
  if (lower.includes("synthesiz") || lower.includes("finaliz") || lower.includes("result") || lower.includes("preparing")) return 6;
  if (lower.includes("critiq") || lower.includes("rank") || lower.includes("score") || lower.includes("judg")) return 5;
  if (lower.includes("constraint") || lower.includes("filtering products") || lower.includes("matching constraint") || lower.includes("satisfying budget")) return 4;
  if (lower.includes("extract") || lower.includes("specs") || lower.includes("parsing")) return 3;
  if (lower.includes("searching stores") || lower.includes("tavily") || lower.includes("generat") || lower.includes("web") || lower.includes("scrap")) return 2;
  return 1;
}

function getQuickReplies(query: string): string[] {
  const lower = query.toLowerCase();
  if (lower.includes("headphone") || lower.includes("earbud") || lower.includes("earphone") || lower.includes("audio")) {
    return ["Under ₹2,000", "Under ₹5,000", "With ANC", "For Gaming"];
  }
  if (lower.includes("laptop") || lower.includes("macbook") || lower.includes("pc")) {
    return ["Under ₹50,000", "Under ₹80,000", "For Coding", "16GB RAM"];
  }
  if (lower.includes("mouse") || lower.includes("keyboard")) {
    return ["Under ₹1,500", "Under ₹3,000", "Wireless", "RGB Gaming"];
  }
  if (lower.includes("phone") || lower.includes("mobile") || lower.includes("smartphone")) {
    return ["Under ₹15,000", "Under ₹30,000", "5G Connectivity", "Best Camera"];
  }
  return ["Under ₹2,000", "Under ₹5,000", "Best Value", "Top Rated"];
}

interface ClarificationScreenProps {
  query: string;
  question: string;
  onAnswer: (answer: string) => void;
  onSkip: () => void;
}

function ClarificationScreen({
  query,
  question,
  onAnswer,
  onSkip,
}: ClarificationScreenProps) {
  const quickReplies = getQuickReplies(query);

  return (
    <div className="mx-auto flex w-full max-w-[620px] flex-col items-center py-6 text-center sm:py-8 animate-[fade-in-up_0.25s_ease-out]">
      {/* Top Header */}
      <div className="shrink-0 px-4">
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-[#f2ecff] to-[#e6daff] border border-[#d6c7ff] text-[#6547e4] shadow-[0_8px_20px_rgba(118,80,235,.15)]">
          <Sparkles className="h-6 w-6" />
        </div>
        <h2 className="text-[22px] font-semibold tracking-tight text-[#161c3d] sm:text-[26px]">
          Before we search...
        </h2>
        <p className="mt-1 text-[13px] text-[#6d748c] sm:text-[14px]">
          We need a bit more detail to find your perfect product
        </p>
        <div className="mt-3 inline-flex items-center gap-2 rounded-full border border-[#e3dcf8] bg-[#f8f5ff] px-4 py-1 text-[13px] font-medium text-[#5e43c5]">
          <span>Searching for &ldquo;{query}&rdquo;</span>
        </div>
      </div>

      {/* Center Clarification Card */}
      <div className="mt-6 w-full overflow-hidden rounded-[24px] border border-[#8561f3]/40 bg-white p-5 sm:p-7 shadow-[0_14px_45px_rgba(118,80,235,.12)] ring-2 ring-[#8561f3]/15">
        <ClarificationPrompt
          question={question}
          onAnswer={onAnswer}
          quickReplies={quickReplies}
          onSkip={onSkip}
        />
      </div>
    </div>
  );
}

interface SearchingScreenProps {
  query: string;
  progress: string;
  stage?: string;
}

function SearchingScreen({ query, progress, stage }: SearchingScreenProps) {
  const [activeStep, setActiveStep] = useState(1);

  // Advance only on real backend stage events. The step never moves backward
  // (a retry loops back to "searching" but the story bar stays monotonic so it
  // doesn't look like it's regressing).
  useEffect(() => {
    const target = stageToStep(progress, stage);
    setActiveStep((prev) => Math.max(prev, target));
  }, [progress, stage]);

  const currentStepIndex = Math.min(Math.max(activeStep, 1), 6) - 1;
  const current = STORY_STEPS[currentStepIndex];

  return (
    <div className="mx-auto flex w-full max-w-[660px] flex-col items-center py-4 text-center sm:py-6">
      {/* Top Header */}
      <div className="shrink-0 px-4">
        <h2 className="text-[22px] font-semibold tracking-tight text-[#161c3d] sm:text-[26px]">
          Shop<span className="sp-gradient-text">Pilot AI</span> – Search in Progress
        </h2>
        <p className="mt-1 text-[13px] text-[#6d748c] sm:text-[14px]">
          We turn your query into the best product recommendations
        </p>
        <div className="mt-2.5 inline-flex items-center gap-2 rounded-full border border-[#e3dcf8] bg-[#f8f5ff] px-4 py-1 text-[13px] font-medium text-[#5e43c5]">
          <span>&ldquo;{query}&rdquo;</span>
        </div>
      </div>

      {/* 6-Step Top Indicator Bar */}
      <div className="my-4 flex shrink-0 items-center justify-center gap-2 sm:gap-3.5">
        {STORY_STEPS.map((s) => {
          const isDone = s.step < activeStep;
          const isActive = s.step === activeStep;
          return (
            <div key={s.step} className="flex items-center gap-1.5 sm:gap-2">
              <button
                type="button"
                onClick={() => setActiveStep(s.step)}
                className={`grid h-7 w-7 sm:h-8 sm:w-8 place-items-center rounded-full text-[12px] font-bold transition-all duration-300 ${
                  isActive
                    ? "bg-gradient-to-br from-[#4e78fb] via-[#7f51ef] to-[#cd51da] text-white shadow-[0_6px_20px_rgba(118,80,235,.40)] scale-110"
                    : isDone
                    ? "bg-[#1aa56b] text-white"
                    : "bg-[#f0ebff] text-[#9a91c7]"
                }`}
              >
                {isDone ? "✓" : s.step}
              </button>
              {s.step < 6 && (
                <div
                  className={`h-0.5 w-4 sm:w-8 rounded-full transition-all duration-500 ${
                    s.step < activeStep ? "bg-[#1aa56b]" : "bg-[#ebe6f8]"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Main Single-Step Focused Story Card */}
      <div className="relative my-2 w-full overflow-hidden rounded-[24px] border border-[#8561f3] bg-white p-5 sm:p-7 shadow-[0_14px_45px_rgba(118,80,235,.15)] ring-2 ring-[#8561f3]/20 transition-all duration-500">
        <div className="flex items-center justify-between border-b border-[#f0ebfb] pb-3">
          <span className="text-[11px] sm:text-[12px] font-bold uppercase tracking-wider text-[#7a55ef]">
            Step {current.step} of 6
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-[#f4efff] px-3 py-0.5 text-[11px] sm:text-[12px] font-medium text-[#6547e4]">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#7a55ef] opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-[#7a55ef]" />
            </span>
            Active Phase
          </span>
        </div>

        {/* Step Title & Subtitle */}
        <div className="mt-3 text-center">
          <h3 className="text-[19px] sm:text-[21px] font-semibold text-[#1d2444]">{current.title}</h3>
          <p className="mt-1 text-[13px] sm:text-[14px] text-[#717892]">{current.subtitle}</p>
        </div>

        {/* Center Icon Graphic Orb */}
        <div className="my-4 flex justify-center">
          <div className="relative grid h-16 w-16 sm:h-20 sm:w-20 place-items-center rounded-2xl bg-gradient-to-br from-[#fcfaff] via-[#f4efff] to-[#eee6ff] border border-[#e5dcfb] shadow-[0_10px_28px_rgba(118,80,235,.12)]">
            <span className="text-[32px] sm:text-[40px] transition-transform duration-300 animate-pulse">
              {current.icon}
            </span>
          </div>
        </div>

        {/* What's happening in the background */}
        <div className="rounded-xl border border-[#ece7f8] bg-[#fbfaff] p-3.5 text-left text-[13px]">
          <div className="font-semibold text-[#5c49b0]">What&apos;s happening in the background?</div>
          <p className="mt-1 text-[#5d6480]">
            {progress || current.bgMsg}
          </p>
        </div>

        {/* Caption */}
        <p className="mt-3 text-[12px] text-[#7b8199]">{current.caption}</p>

        {/* Animated Shimmer Bar inside Card */}
        <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-[#eeeaf9]">
          <div
            className="h-full animate-[shimmer_1.8s_linear_infinite] rounded-full bg-gradient-to-r from-[#4e78fb] via-[#c351da] to-[#4e78fb] bg-[length:200%_100%]"
          />
        </div>
      </div>

      {/* Footer Status Pill */}
      <div className="mt-3 shrink-0 text-center">
        <span className="inline-flex items-center gap-2 rounded-full border border-[#ded5f8] bg-gradient-to-r from-[#f8f5ff] via-[#f3ecff] to-[#f8f5ff] px-5 py-1.5 text-[12px] sm:text-[13px] font-medium text-[#6547e4] shadow-xs">
          <span className="animate-spin text-[14px]">✦</span> Performing real-time product search...
        </span>
      </div>
    </div>
  );
}

export function SearchResultPage({ initialQuery }: { initialQuery: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const urlQuery = (searchParams.get("q") ?? initialQuery ?? "").trim();

  const [query, setQuery] = useState(urlQuery);
  const [loading, setLoading] = useState(!!urlQuery);
  const [progress, setProgress] = useState("Understanding your request…");
  const [progressStage, setProgressStage] = useState("pipeline_started");
  const [result, setResult] = useState<SearchResultPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [savedKeys, setSavedKeys] = useState<Set<string>>(new Set());
  const [showSignInPrompt, setShowSignInPrompt] = useState(false);
  const { user } = useAuth();

  const [clarificationQuestion, setClarificationQuestion] = useState<string | null>(null);
  const [clarificationContext, setClarificationContext] = useState<ClarificationContext | null>(null);

  const runSearch = useCallback(
    async (q: string, contextOverride?: ClarificationContext) => {
      setLoading(true);
      setError(null);
      setResult(null);
      setClarificationQuestion(null);
      setProgress("Understanding your request…");
      setProgressStage("pipeline_started");

      const activeContext = contextOverride ?? clarificationContext ?? undefined;

      try {
        for await (const event of streamSearch(q, activeContext)) {
          const typed = event as SSEEvent;
          if (typed.event === "progress") {
            setProgress(typed.payload.message);
            if (typed.payload.stage) {
              setProgressStage(typed.payload.stage);
            }
          } else if (typed.event === "result") {
            setResult(typed.payload);
            setClarificationQuestion(null);
          } else if (typed.event === "error") {
            setError(typed.payload.message);
          } else if (typed.event === "needs_clarification") {
            setClarificationQuestion(typed.payload.question);
            setClarificationContext({
              round: typed.payload.round,
              previous_questions: [typed.payload.question],
              user_answers: [],
            });
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Search failed. Please try again.");
      } finally {
        setLoading(false);
      }
    },
    [clarificationContext]
  );

  useEffect(() => {
    const activeQ = (urlQuery || initialQuery || query).trim();
    if (activeQ) {
      setQuery(activeQ);
      void runSearch(activeQ);
    }
  }, [urlQuery, initialQuery]);

  const products = useMemo(() => result?.products.map(toProductViewModel) ?? [], [result]);
  const best = products[0];

  // Verified when the critic passed (not a best-available fallback).
  const isVerified = !(result?.metadata?.is_best_available ?? false);

  // Served straight from the semantic memory cache (no live web search).
  const fromMemory = result?.metadata?.from_memory ?? false;
  const memorySimilarityPct =
    typeof result?.metadata?.memory_similarity === "number"
      ? Math.round(result.metadata.memory_similarity * 100)
      : null;

  // Deduped real source links across the shown products (PRD FR11).
  const sources = useMemo(() => {
    const seen = new Set<string>();
    const out: { url: string; label: string }[] = [];
    for (const p of products) {
      if (p.sourceUrl && !seen.has(p.sourceUrl)) {
        seen.add(p.sourceUrl);
        out.push({ url: p.sourceUrl, label: `${p.name}${p.merchant ? ` — ${p.merchant}` : ""}` });
      }
    }
    return out.slice(0, 5);
  }, [products]);

  const saveProduct = useCallback(
    async (p: ProductViewModel) => {
      const link =
        p.sourceUrl ??
        (p.fields?.name?.source_url ? String(p.fields.name.source_url) : "");
      const key = `${p.name}|${link}`;
      if (savedKeys.has(key)) return; // already saved, keep it filled

      // Not signed in: ask to sign in without leaving the page.
      if (!user) {
        setShowSignInPrompt(true);
        return;
      }

      // Optimistically fill the heart.
      setSavedKeys((prev) => new Set(prev).add(key));
      try {
        const res = await fetch("/api/v1/saved", {
          method: "POST",
          headers: { "Content-Type": "application/json", ...authHeaders() },
          body: JSON.stringify({
            name: p.name,
            price: p.price,
            image: p.imageUrl,
            merchant: p.merchant,
            link,
          }),
        });
        if (!res.ok) {
          // Roll back on failure (e.g. not signed in).
          setSavedKeys((prev) => {
            const next = new Set(prev);
            next.delete(key);
            return next;
          });
        }
      } catch {
        setSavedKeys((prev) => {
          const next = new Set(prev);
          next.delete(key);
          return next;
        });
      }
    },
    [savedKeys, user]
  );

  function isSaved(p: ProductViewModel): boolean {
    const link =
      p.sourceUrl ?? (p.fields?.name?.source_url ? String(p.fields.name.source_url) : "");
    return savedKeys.has(`${p.name}|${link}`);
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;
    setClarificationQuestion(null);
    setClarificationContext(null);
    router.replace(`/search?q=${encodeURIComponent(q)}`);
    void runSearch(q, undefined);
  }

  const handleAnswerClarification = useCallback(
    (answer: string) => {
      const nextQuery = `${query} ${answer}`.trim();
      setQuery(nextQuery);
      setClarificationQuestion(null);

      router.replace(`/search?q=${encodeURIComponent(nextQuery)}`);

      const updatedContext: ClarificationContext = {
        round: (clarificationContext?.round ?? 1) + 1,
        previous_questions: clarificationContext?.previous_questions ?? [clarificationQuestion || ""],
        user_answers: [...(clarificationContext?.user_answers ?? []), answer],
      };
      setClarificationContext(updatedContext);

      void runSearch(nextQuery, updatedContext);
    },
    [query, clarificationQuestion, clarificationContext, router, runSearch]
  );

  const handleSkipClarification = useCallback(() => {
    const nextQuery = `${query} top choice`.trim();
    setClarificationQuestion(null);
    void runSearch(nextQuery, clarificationContext ?? undefined);
  }, [query, clarificationContext, runSearch]);

  const isLoadingScreen = loading || clarificationQuestion !== null || (!result && !error);

  return (
    <div className={`sp-container ${isLoadingScreen ? "min-h-[calc(100dvh-80px)] py-4 sm:py-6 flex flex-col justify-between overflow-y-auto" : "py-8 md:py-10"}`}>
      {/* Search bar header row */}
      <div className="flex shrink-0 items-center gap-3">
        <button
          type="button"
          onClick={() => router.push("/")}
          aria-label="Back to home"
          className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl border border-[#e2dcf5] bg-white text-[#565d7a] shadow-xs transition-all hover:border-[#8561f3] hover:text-[#5a43b5]"
        >
          <ArrowLeft size={18} />
        </button>
        <form
          onSubmit={submit}
          className="flex h-12 sm:h-13 flex-1 items-center rounded-full border border-[#ddd8ee] bg-white px-4 sm:px-5 shadow-[0_8px_25px_rgba(68,55,136,.05)] transition-shadow hover:shadow-[0_10px_32px_rgba(68,55,136,.09)]"
        >
          <Search size={19} className="shrink-0 text-[#656c83]" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="mx-3 sm:mx-4 min-w-0 flex-1 border-none bg-transparent text-[14px] sm:text-[15px] font-medium text-[#1c223f] outline-none ring-0 focus:border-none focus:outline-none focus:ring-0 placeholder:text-[#949bb3]"
            aria-label="Search query"
            placeholder="Search for products, categories, specs..."
          />
          <button type="submit" className="sp-gradient-btn h-8.5 w-8.5 shrink-0 rounded-full">
            <Sparkles size={15} />
          </button>
        </form>
      </div>

      <div className={isLoadingScreen ? "flex flex-1 flex-col pt-2" : "mt-8"}>
        {/* ── 1. Clarification needed BEFORE entering loading screen steps ── */}
        {clarificationQuestion ? (
          <ClarificationScreen
            query={query || urlQuery || initialQuery}
            question={clarificationQuestion}
            onAnswer={handleAnswerClarification}
            onSkip={handleSkipClarification}
          />
        ) : (isLoadingScreen && !error) ? (
          /* ── 2. 6-Step Search Progress Screen ── */
          <SearchingScreen
            query={query || urlQuery || initialQuery}
            progress={progress}
            stage={progressStage}
          />
        ) : null}

        {/* ── Error state ── */}
        {error && (
          <div className="mx-auto my-6 max-w-xl rounded-2xl border border-[#f1d7da] bg-[#fffafa] p-5 text-center text-[14px] text-[#9d4855] shadow-xs">
            <p className="font-semibold">{error}</p>
            <button
              type="button"
              onClick={() => runSearch(query)}
              className="mt-3 inline-flex items-center rounded-xl bg-[#9d4855] px-4 py-2 text-[13px] font-medium text-white hover:bg-[#853a46]"
            >
              Try Again
            </button>
          </div>
        )}

        {/* ── No Products Found State ── */}
        {!best && !loading && !clarificationQuestion && result && !error && (
          <div className="mx-auto my-8 max-w-xl rounded-3xl border border-[#e5dcfb] bg-white p-6 sm:p-8 text-center shadow-[0_12px_36px_rgba(118,80,235,.08)]">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#f4efff] text-[#6547e4]">
              <Search size={26} />
            </div>
            <h3 className="text-[20px] font-semibold text-[#181e39]">No exact product matches found</h3>
            <p className="mt-2 text-[14px] text-[#6b728d]">
              We searched live web listings for &ldquo;{query}&rdquo;, but couldn&apos;t find verified products matching all constraints. Try broadening your budget or criteria!
            </p>
            <div className="mt-5 flex justify-center gap-3">
              <button
                type="button"
                onClick={() => {
                  const cleaned = query.replace(/under\s*\S+/gi, "").trim() || "top products";
                  setQuery(cleaned);
                  void runSearch(cleaned);
                }}
                className="sp-gradient-btn px-5 py-2.5 text-[13px] font-semibold"
              >
                Broaden Search & Try Again
              </button>
            </div>
          </div>
        )}

        {/* ── Results ── */}
        {best && !loading && !clarificationQuestion && (
          <>
            <div className="mb-5">
              <h1 className="text-[26px] sm:text-[28px] font-semibold tracking-[-.035em]">
                {isVerified ? (
                  <>Here{"'s"} the <span className="sp-gradient-text">best match</span> for you</>
                ) : (
                  <>The <span className="sp-gradient-text">closest available</span> match</>
                )}
              </h1>
              <p className="mt-1 text-[14px] sm:text-[15px] text-[#717990]">
                {isVerified
                  ? "Verified against your constraints through automated self-critique."
                  : "The critic couldn't fully verify a match, so these are the closest options rather than a guaranteed fit."}
              </p>
            </div>

            {/* Semantic memory recall banner: served from ChromaDB, no live search. */}
            {fromMemory && (
              <div className="mb-5 flex items-start gap-3 rounded-[16px] border border-[#c7e0d0] bg-[#f0faf4] p-4 text-[13px] text-[#1f6b45]">
                <Sparkles size={18} className="mt-0.5 shrink-0 text-[#1aa56b]" />
                <span>
                  <span className="font-semibold">⚡ Answered from memory</span> — no live web
                  search used
                  {memorySimilarityPct !== null
                    ? ` (matched your earlier query at ${memorySimilarityPct}% similarity)`
                    : ""}
                  . The verified answer was recalled instantly from the vector store.
                </span>
              </div>
            )}

            <BestMatchCard
              product={best}
              onSave={() => saveProduct(best)}
              saved={isSaved(best)}
              verified={isVerified}
              rationale={result?.metadata?.verdict?.rationale}
              synthesis={result?.synthesis}
            />

            {/* Sources for the evidence (PRD FR11). The reasoning itself now
                lives on the best-match card, so this block just cites sources. */}
            {sources.length > 0 && (
              <section className="mt-6 rounded-[18px] border border-[#e9e5f7] bg-white p-5 sm:p-6">
                <div className="flex items-center gap-2 text-[15px] font-semibold text-[#1c2344]">
                  <LinkIcon size={16} className="text-[#7050f0]" /> Sources
                </div>
                <ul className="mt-3 space-y-1.5">
                  {sources.map((s) => (
                    <li key={s.url}>
                      <a href={s.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 text-[13px] text-[#6348ef] hover:underline">
                        <LinkIcon size={13} /> {s.label}
                      </a>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            <AlternativeRail products={products.slice(1)} onSave={(p) => saveProduct(p)} isSaved={isSaved} />

            <div className="mt-7 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between rounded-[18px] border border-[#eee8fb] bg-gradient-to-r from-white via-[#fbf8ff] to-[#f8f2ff] p-5">
              <div className="flex items-center gap-3">
                <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-[#efeaff] text-[#6f4def]">
                  <Sparkles size={18} />
                </div>
                <div>
                  <div className="text-[14px] font-semibold">Want something more specific?</div>
                  <div className="text-[12px] text-[#767d93]">
                    Tell the AI agent what to change and refine the results.
                  </div>
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  window.scrollTo({ top: 0, behavior: "smooth" });
                }}
                className="sp-gradient-btn self-start sm:self-auto px-5 py-2.5 text-[13px] font-semibold"
              >
                Refine Search
              </button>
            </div>
            <p className="mt-4 text-[11px] text-[#8a90a2]">
              Prices and availability may change. Results reflect the best available match at search time.
            </p>
          </>
        )}
      </div>

      {/* Sign-in prompt: shown when a signed-out user taps save. Stays on the
          page (an overlay), and offers to go sign in, preserving this search. */}
      {showSignInPrompt && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4"
          onClick={() => setShowSignInPrompt(false)}
        >
          <div
            className="w-full max-w-[380px] rounded-2xl border border-[#e8e5f5] bg-white p-6 text-center shadow-[0_20px_60px_rgba(60,44,140,.22)]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-[#f3efff] text-[#6c4ef0]">
              <Heart size={22} />
            </div>
            <h3 className="mt-4 text-[18px] font-semibold text-[#1b2240]">Sign in to save products</h3>
            <p className="mt-2 text-[13px] leading-6 text-[#767d93]">
              Saved items live in your account so you can come back to them anytime.
            </p>
            <div className="mt-5 flex gap-3">
              <button
                onClick={() => setShowSignInPrompt(false)}
                className="h-11 flex-1 rounded-xl border border-[#dcd8ef] text-[13px] font-medium text-[#5b6177] hover:bg-[#faf8ff]"
              >
                Not now
              </button>
              <button
                onClick={() => router.push(`/signin?next=${encodeURIComponent(`/search?q=${query}`)}`)}
                className="sp-gradient-btn h-11 flex-1 text-[13px] font-semibold"
              >
                Sign in
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}