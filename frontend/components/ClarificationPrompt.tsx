"use client";

import { useState, type FormEvent } from "react";
import { HelpCircle, SendHorizonal } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface ClarificationPromptProps {
  question: string;
  onAnswer: (answer: string) => void;
  quickReplies?: string[];
  onSkip?: () => void;
}

export function ClarificationPrompt({ question, onAnswer, quickReplies, onSkip }: ClarificationPromptProps) {
  const [answer, setAnswer] = useState("");

  const defaultReplies = quickReplies ?? ["Yes", "No", "Not sure", "Skip this"];

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedAnswer = answer.trim();
    if (trimmedAnswer) onAnswer(trimmedAnswer);
  }

  return (
    <Card className="w-full animate-[fade-in-up_0.25s_ease-out_both] border-[#8561f3]/40 bg-gradient-to-b from-[#fbf9ff] to-[#f4efff] shadow-[0_10px_30px_rgba(118,80,235,.12)]">
      <CardHeader className="pb-3">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#8561f3]/15 text-[#6547e4]">
            <HelpCircle className="h-5 w-5" />
          </div>
          <div className="flex-1 text-left">
            <CardTitle className="text-[15px] font-semibold text-[#1d2444]">
              Clarification Needed
            </CardTitle>
            <CardDescription className="mt-1 text-[14px] font-medium text-[#4a516d]">
              {question}
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        <form className="flex gap-2" onSubmit={handleSubmit}>
          <Input
            type="text"
            value={answer}
            onChange={(event) => setAnswer(event.target.value)}
            aria-label="Your answer"
            placeholder="Type budget, brand, or feature requirements..."
            className="flex-1 h-10 rounded-xl border-[#dcd4f5] bg-white px-3.5 text-[13px] text-[#1d2444] placeholder:text-[#979eb3] focus-visible:ring-2 focus-visible:ring-[#8561f3]"
            autoFocus
          />
          <Button
            type="submit"
            disabled={!answer.trim()}
            size="default"
            className="h-10 gap-1.5 rounded-xl bg-gradient-to-r from-[#4e78fb] via-[#7f51ef] to-[#cd51da] px-4 text-[13px] font-semibold text-white shadow-sm hover:opacity-95"
          >
            <SendHorizonal className="h-4 w-4" />
            Submit
          </Button>
        </form>

        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          <span className="text-[11px] font-medium uppercase tracking-wider text-[#797f97]">
            Quick options:
          </span>
          {defaultReplies.map((reply) => (
            <Button
              key={reply}
              type="button"
              variant="outline"
              size="sm"
              className="h-7 rounded-full border-[#dcd5f5] bg-white px-3 text-[12px] font-medium text-[#5a43b5] hover:border-[#8561f3] hover:bg-[#f0ebff]"
              onClick={() => onAnswer(reply)}
            >
              {reply}
            </Button>
          ))}
          {onSkip && (
            <button
              type="button"
              onClick={onSkip}
              className="ml-auto text-[12px] font-medium text-[#797f97] underline decoration-dashed underline-offset-4 hover:text-[#5a43b5]"
            >
              Skip & search as-is
            </button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}