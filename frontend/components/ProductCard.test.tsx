import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProductCard } from "./ProductCard";
import type { ProductResult } from "@/lib/types";

function makeProduct(overrides: Partial<ProductResult> = {}): ProductResult {
  return {
    name: "Sony WH-1000XM5",
    price: 24999,
    matched_constraints: ["noise cancellation"],
    soft_score: 8,
    fields: {
      name: { value: "Sony WH-1000XM5", source_url: "https://amazon.in/product/1" },
      price: { value: 24999, source_url: "https://amazon.in/product/1" },
    },
    ...overrides,
  };
}

describe("ProductCard", () => {
  it("renders the product name and price", () => {
    render(<ProductCard product={makeProduct()} />);
    expect(screen.getByText("Sony WH-1000XM5")).toBeInTheDocument();
    expect(screen.getByText(/24999|24,999/)).toBeInTheDocument();
  });

  it("renders a source link for every field", () => {
    render(<ProductCard product={makeProduct()} />);
    const links = screen.getAllByRole("link", { name: /source/i });
    expect(links.length).toBeGreaterThan(0);
    expect(links[0]).toHaveAttribute("href", "https://amazon.in/product/1");
  });

  it("shows 'Not specified' when price is null, never a guessed value", () => {
    render(<ProductCard product={makeProduct({ price: null })} />);
    expect(screen.getByText(/not specified/i)).toBeInTheDocument();
  });
});