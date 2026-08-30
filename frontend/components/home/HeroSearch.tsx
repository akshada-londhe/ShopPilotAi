"use client";

import { ArrowRight, Search } from "lucide-react";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { ShopPilotLogo } from "../brand/ShopPilotLogo";

const examples = [
  "Wireless headphones",
  "Gaming laptop",
  "Skincare for dry skin",
  "Home gym setup",
];

export function HeroSearch() {
  const router = useRouter();
  const [query, setQuery] = useState("");

  function runSearch(raw: string) {
    const q = raw.trim();
    if (!q) return;
    router.push(`/search?q=${encodeURIComponent(q)}`);
  }

  function submit(e: FormEvent) {
    e.preventDefault();
    runSearch(query);
  }

  return (
    <div className="relative z-10 mx-auto flex w-full max-w-[820px] flex-col items-center">
      {/* Brand */}
      <div className="mb-5 flex flex-col items-center text-center">
        <div className="scale-125 pb-2">
          <ShopPilotLogo />
        </div>
        <p className="mt-2 text-[18px] text-[#727993]">Your AI shopping assistant for smarter choices</p>
      </div>

      {/* Search bar — no mic, no camera */}
      <form onSubmit={submit} className="mt-6 w-full">
        <div className="flex h-[76px] items-center rounded-full border-2 border-[#d9d2f6] bg-white px-7 shadow-[0_8px_32px_rgba(94,79,190,.14)] transition-all hover:border-[#b8a9f2] hover:shadow-[0_12px_40px_rgba(94,79,190,.22)] focus-within:border-[#8e78ee] focus-within:shadow-[0_10px_40px_rgba(94,79,190,.28)]">
          <Search className="mr-5 shrink-0 text-[#5f667f]" size={28} strokeWidth={1.7} />
          <input
            aria-label="Search for products"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search for products, categories, brands and more..."
            className="min-w-0 flex-1 bg-transparent text-[17px] text-[#17203e] outline-none ring-0 focus:outline-none focus:ring-0 placeholder:text-[#8a90a5]"
          />
          <button
            type="submit"
            aria-label="Search"
            className="ml-3 grid h-11 w-11 shrink-0 place-items-center rounded-full bg-gradient-to-r from-[#4f79ff] to-[#8e4ce6] text-white shadow-[0_6px_18px_rgba(100,75,220,.25)] transition-transform hover:scale-105"
          >
            <ArrowRight size={20} />
          </button>
        </div>

        {/* Example chips */}
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <span className="mr-1 text-[13px] text-[#737b94]">Try searching for</span>
          {examples.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => {
                setQuery(item);
                runSearch(item);
              }}
              className="sp-chip sp-focus px-4 py-2 text-[13px]"
            >
              {item}
            </button>
          ))}
        </div>
      </form>

      {/* Tagline */}
      <div className="mt-8 text-center">
        <p className="text-[17px] font-medium">
          <span className="text-[#6179e9]">Discover</span>
          <span className="mx-2 text-[#b2b5c3]">•</span>
          <span className="text-[#8556eb]">Compare</span>
          <span className="mx-2 text-[#b2b5c3]">•</span>
          <span className="text-[#c15bda]">Decide</span>
        </p>
        <p className="mt-1.5 text-[15px] text-[#7d8398]">Trusted recommendations. Smarter shopping.</p>
      </div>
    </div>
  );
}