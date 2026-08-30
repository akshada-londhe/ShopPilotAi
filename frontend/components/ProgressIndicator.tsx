import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { PIPELINE_STAGE_ORDER } from "@/lib/types";

interface ProgressIndicatorProps {
  stage: string;
  message: string;
}

const STAGE_LABELS: Record<string, string> = {
  normalizing: "Intent",
  generating: "Keywords",
  cache_check: "Memory",
  searching: "Web Search",
  sanitizing: "Sanitize",
  extracting: "Extract",
  matching: "Constraints",
  critiquing: "Judge",
  retrying: "Retry",
  synthesizing: "Synthesize",
  done: "Done",
};

const DISPLAY_STAGES = PIPELINE_STAGE_ORDER.filter((s) => s !== "retrying");

export function ProgressIndicator({ stage, message }: ProgressIndicatorProps) {
  const activeIdx = DISPLAY_STAGES.indexOf(stage as (typeof DISPLAY_STAGES)[number]);

  return (
    <div className="w-full animate-[fade-in-up_0.2s_ease-out_both] rounded-xl border border-primary/20 bg-card/90 p-2.5 shadow-xs backdrop-blur-md">
      <div className="flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin text-primary" />
          <p className="truncate text-[11.5px] font-medium text-foreground">{message}</p>
        </div>
        <span className="shrink-0 rounded bg-primary/10 px-2 py-0.5 font-mono text-[10px] font-bold uppercase text-primary">
          {STAGE_LABELS[stage] ?? stage} · {activeIdx >= 0 ? activeIdx + 1 : 1}/{DISPLAY_STAGES.length}
        </span>
      </div>

      <div className="mt-2 flex items-center gap-1">
        {DISPLAY_STAGES.map((s, idx) => {
          const isActive = s === stage;
          const isDone = activeIdx >= 0 && idx < activeIdx;

          return (
            <div
              key={s}
              title={STAGE_LABELS[s]}
              className={cn(
                "h-1 flex-1 rounded-full transition-all duration-300",
                isActive && "bg-primary shadow-[0_0_8px_hsl(var(--glow-active))]",
                isDone && "bg-emerald-500",
                !isActive && !isDone && "bg-secondary"
              )}
            />
          );
        })}
      </div>
    </div>
  );
}