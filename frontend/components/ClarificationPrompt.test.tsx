import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ClarificationPrompt } from "./ClarificationPrompt";

describe("ClarificationPrompt", () => {
  it("displays the question text", () => {
    render(<ClarificationPrompt question="What's your budget?" onAnswer={vi.fn()} />);
    expect(screen.getByText("What's your budget?")).toBeInTheDocument();
  });

  it("calls onAnswer with the typed response", async () => {
    const handleAnswer = vi.fn();
    render(<ClarificationPrompt question="What's your budget?" onAnswer={handleAnswer} />);

    await userEvent.type(screen.getByRole("textbox"), "around 20000");
    await userEvent.click(screen.getByRole("button", { name: /submit/i }));

    expect(handleAnswer).toHaveBeenCalledWith("around 20000");
  });
});