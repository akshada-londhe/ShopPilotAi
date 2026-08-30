"use client";

import Link from "next/link";
import { BookOpen, Clock3, Heart, House, UserRound } from "lucide-react";
import { usePathname } from "next/navigation";

const items = [
  { href: "/dashboard", label: "Dashboard", Icon: House },
  { href: "/history", label: "Search History", Icon: Clock3 },
  { href: "/saved", label: "Saved Items", Icon: Heart },
  { href: "/profile", label: "Profile", Icon: UserRound },
];

export function AppSidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden w-[260px] shrink-0 overflow-y-auto border-r border-[#ebeaf3] bg-white lg:block">
      <div className="p-5">
        <nav className="space-y-2">
          {items.map(({ href, label, Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-4 rounded-xl px-4 py-3 text-[15px] font-medium transition ${active ? "bg-[#f2edff] text-[#5f42ef]" : "text-[#17203e] hover:bg-[#faf9ff]"}`}
              >
                <Icon size={21} strokeWidth={active ? 2.2 : 1.9} />
                {label}
              </Link>
            );
          })}
        </nav>
        <div className="my-6 border-t border-[#efedf6]" />
        <Link href="/how-it-works" className="flex items-center gap-4 rounded-xl px-4 py-3 text-[15px] font-medium text-[#17203e] hover:bg-[#faf9ff]">
          <BookOpen size={21} strokeWidth={1.9} />
          How it works
        </Link>
      </div>
    </aside>
  );
}