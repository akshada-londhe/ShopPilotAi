"use client";

import { useEffect } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Replace with real error reporting (Sentry, etc.) before shipping.
    console.error(error);
  }, [error]);

  return (
    <div className="flex h-screen w-full flex-col items-center justify-center gap-3 bg-background p-6 text-center text-foreground">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-destructive/10 text-destructive">
        <AlertTriangle className="h-5 w-5" />
      </div>
      <div>
        <h1 className="text-sm font-semibold">Something went wrong</h1>
        <p className="mt-1 max-w-sm text-xs text-muted-foreground">
          An unexpected error interrupted the page. You can try again, or start a new search.
        </p>
      </div>
      <Button size="sm" variant="outline" className="gap-1.5" onClick={() => reset()}>
        <RotateCcw className="h-3.5 w-3.5" />
        Try again
      </Button>
    </div>
  );
}