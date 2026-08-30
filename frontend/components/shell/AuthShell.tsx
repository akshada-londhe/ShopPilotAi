import Link from "next/link";
import { ReactNode } from "react";
import { ShopPilotLogo } from "../brand/ShopPilotLogo";

export function AuthShell({ title, children, mode }: { title: string; children: ReactNode; mode: "signin" | "signup" }) {
  return (
    <div className="flex h-dvh flex-col overflow-hidden bg-[radial-gradient(circle_at_8%_12%,rgba(139,76,255,.10),transparent_20rem),radial-gradient(circle_at_94%_86%,rgba(71,120,255,.10),transparent_22rem),#fff]">
      {/* Top Header — Logo and Tagline on the Left */}
      <header className="sp-container flex h-16 shrink-0 items-center justify-between pt-4">
        <div className="flex items-baseline gap-3">
          <ShopPilotLogo />
          <span className="hidden text-[13px] text-[#7a8095] sm:inline">• Smarter choices. Better shopping.</span>
        </div>
      </header>

      {/* Main content centered in available height */}
      <main className="sp-container flex flex-1 items-center justify-center overflow-hidden py-2">
        <div className="mx-auto grid w-full max-w-[960px] overflow-hidden rounded-[24px] border border-[#e7e3f2] bg-white shadow-[0_16px_45px_rgba(55,42,137,.10)] lg:grid-cols-[.9fr_1.1fr]">
          <section className="relative overflow-hidden bg-gradient-to-br from-[#fbf8ff] via-[#f7f4ff] to-[#fff] p-8 lg:p-10">
            <div className="absolute left-10 top-16 h-48 w-48 rounded-full bg-[#eee6ff] opacity-70 blur-3xl" />
            <div className="relative">
              <h2 className="text-[28px] font-semibold tracking-[-.04em] lg:text-[32px]">{title}</h2>
              <p className="mt-2 max-w-[320px] text-[15px] leading-6 text-[#737992]">
                Join ShopPilot AI and make faster, more confident product decisions.
              </p>
              <div className="my-6 grid place-items-center lg:my-8">
                <div className="grid h-32 w-32 place-items-center rounded-[28px] bg-gradient-to-br from-[#4e78fb] via-[#7f51ef] to-[#cd51da] text-[54px] text-white shadow-[0_16px_40px_rgba(118,80,235,.28)]">✦</div>
              </div>
              <div className="space-y-3 text-[13px]">
                <div><b className="text-[#6547ee]">Discover</b><p className="mt-0.5 text-[#737992]">Find the best-fit products</p></div>
                <div><b className="text-[#6547ee]">Compare</b><p className="mt-0.5 text-[#737992]">See meaningful differences</p></div>
                <div><b className="text-[#6547ee]">Decide</b><p className="mt-0.5 text-[#737992]">Shop with confidence</p></div>
              </div>
            </div>
          </section>

          <section className="p-6 md:p-8 lg:p-9">{children}</section>
        </div>
      </main>

      {/* Footer pinned */}
      <footer className="shrink-0 pb-3 text-center text-[12px] text-[#7f8599]">
        By {mode === "signin" ? "signing in" : "signing up"}, you agree to our <Link href="/terms" className="text-[#6b4eea]">Terms of Use</Link> and <Link href="/privacy" className="text-[#6b4eea]">Privacy Policy</Link>.
      </footer>
    </div>
  );
}