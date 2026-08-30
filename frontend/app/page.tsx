import { DecorativeBackground } from "../components/home/DecorativeBackground";
import { HeroSearch } from "../components/home/HeroSearch";
import { SiteHeader } from "../components/shell/SiteHeader";

export default function HomePage() {
  return (
    // h-dvh + overflow-hidden = exactly one viewport, no scroll ever
    <div className="flex h-dvh flex-col overflow-hidden bg-white text-[#12183f]">
      <SiteHeader />

      <main className="relative flex flex-1 flex-col">
        <DecorativeBackground />

        {/* Hero centred in the remaining viewport */}
        <section className="sp-container flex flex-1 items-center justify-center">
          <HeroSearch />
        </section>

        {/* Footer pinned at the very bottom — never causes scroll */}
        <div className="mx-auto w-[95%] max-w-[1460px] rounded-t-[28px] border border-[#efedf8] bg-white/80 px-8 py-4 shadow-[0_-6px_30px_rgba(90,67,187,.03)] backdrop-blur">
          <div className="flex flex-wrap items-center justify-between gap-4 text-[13px] text-[#646b80]">
            <div className="flex flex-wrap gap-6">
              <a href="/how-it-works" className="hover:text-[#5a43bb]">How it works</a>
              <a href="/about" className="hover:text-[#5a43bb]">About Us</a>
              <a href="/support" className="hover:text-[#5a43bb]">Help Center</a>
            </div>
            <div className="flex flex-wrap gap-6">
              <a href="/privacy" className="hover:text-[#5a43bb]">Privacy Policy</a>
              <a href="/terms" className="hover:text-[#5a43bb]">Terms of Use</a>
              <a href="/contact" className="hover:text-[#5a43bb]">Contact</a>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}