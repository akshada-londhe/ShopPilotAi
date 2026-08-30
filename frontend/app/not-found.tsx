import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex h-screen w-full flex-col items-center justify-center gap-3 bg-background p-6 text-center text-foreground">
      <h1 className="text-sm font-semibold">Page not found</h1>
      <p className="max-w-sm text-xs text-muted-foreground">
        The page you&rsquo;re looking for doesn&rsquo;t exist.
      </p>
      <Button asChild size="sm">
        <Link href="/">Back to search</Link>
      </Button>
    </div>
  );
}