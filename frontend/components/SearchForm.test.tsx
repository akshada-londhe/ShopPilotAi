import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SearchForm } from "./SearchForm";

describe("SearchForm", () => {
  it("calls onSubmit with the typed query when the form is submitted", async () => {
    const handleSubmit = vi.fn();
    render(<SearchForm onSubmit={handleSubmit} disabled={false} />);

    const input = screen.getByRole("textbox", { name: /search query/i });
    await userEvent.type(input, "gaming mouse under 2000");
    await userEvent.click(screen.getByRole("button", { name: /search/i }));

    expect(handleSubmit).toHaveBeenCalledWith("gaming mouse under 2000");
  });

  it("does not call onSubmit for an empty query", async () => {
    const handleSubmit = vi.fn();
    render(<SearchForm onSubmit={handleSubmit} disabled={false} />);

    await userEvent.click(screen.getByRole("button", { name: /search/i }));

    expect(handleSubmit).not.toHaveBeenCalled();
  });

  it("disables the input and button when disabled prop is true", () => {
    render(<SearchForm onSubmit={vi.fn()} disabled={true} />);

    expect(screen.getByRole("textbox", { name: /search query/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /search/i })).toBeDisabled();
  });
});