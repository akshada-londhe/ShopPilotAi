"use client";

import { useState, type FormEvent } from "react";
import { Search, Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface SearchFormProps {
  onSubmit: (query: string) => void;
  disabled: boolean;
}

const EXAMPLE_CHIPS = [
  "Gaming mouse under ₹2000 with low latency",
  "Wireless earbuds under ₹3000 with ANC",
  "Laptop under ₹80,000 for coding",
  "Noise cancelling headphones under ₹5000",
];

export function SearchForm({ onSubmit, disabled }: SearchFormProps) {
  const [query, setQuery] = useState("");

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
  }

  function handleChipClick(chip: string) {
    if (disabled) return;
    setQuery(chip);
  }

  return (
    <div className="w-full max-w-2xl space-y-1.5">
      <form onSubmit={handleSubmit} className="flex items-center gap-1.5">
        <div className="group relative flex-1">
          <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground transition-colors group-focus-within:text-primary" />
          <Input
            type="text"
            aria-label="search query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={disabled}
            placeholder="e.g. best wireless earbuds under ₹3000 with noise cancellation..."
            className="h-9 rounded-xl border-border/80 bg-card/80 pl-9 pr-3 text-xs shadow-xs backdrop-blur-sm transition-all focus-visible:ring-1 focus-visible:ring-primary/50 sm:text-sm"
          />
        </div>
        <Button
          type="submit"
          disabled={disabled || !query.trim()}
          size="sm"
          className="h-9 shrink-0 gap-1.5 rounded-xl px-4 text-xs font-semibold shadow-xs transition-all"
        >
          {disabled ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
          {disabled ? "Searching" : "Search"}
        </Button>
      </form>

      <div className="no-scrollbar flex flex-wrap items-center gap-1.5 py-0.5">
        <span className="mr-0.5 shrink-0 text-[10px] font-bold uppercase tracking-wider text-muted-foreground/70">
          Try:
        </span>
        {EXAMPLE_CHIPS.map((chip) => (
          <button
            key={chip}
            type="button"
            onClick={() => handleChipClick(chip)}
            disabled={disabled}
            className="rounded-full border border-border/60 bg-secondary/50 px-2.5 py-0.5 text-[10.5px] text-muted-foreground transition-all duration-150 hover:border-primary/40 hover:bg-secondary hover:text-foreground disabled:cursor-not-allowed disabled:opacity-40"
          >
            {chip}
          </button>
        ))}
      </div>
    </div>
  );
}