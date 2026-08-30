import { ReactNode } from "react";
import { SiteHeader } from "./SiteHeader";
import { AppSidebar } from "./AppSidebar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    // Exactly one viewport tall. The header is fixed height; the row below
    // fills the rest. Only <main> scrolls (and only if content truly overflows
    // on very short screens), so the page itself never scrolls.
    <div className="flex h-dvh flex-col overflow-hidden bg-white text-[#12183f]">
      <SiteHeader />
      <div className="flex min-h-0 flex-1">
        <AppSidebar />
        <main className="min-w-0 flex-1 overflow-y-auto bg-white">{children}</main>
      </div>
    </div>
  );
}
