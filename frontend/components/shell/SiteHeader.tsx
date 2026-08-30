"use client";

import Link from "next/link";
import { Heart, LogOut, Menu, X } from "lucide-react";
import { useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { ShopPilotLogo } from "../brand/ShopPilotLogo";
import { useAuth } from "../../lib/auth-context";

export function SiteHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const { user, loading, signOut } = useAuth();

  const appAuthed = ["/dashboard", "/history", "/saved", "/profile", "/search"].some((p) =>
    pathname.startsWith(p)
  );

  const initial = user?.name?.charAt(0)?.toUpperCase() ?? "?";

  function handleSignOut() {
    signOut();
    setShowUserMenu(false);
    router.push("/");
  }

  return (
    <header className="sticky top-0 z-40 border-b border-[#ecebf4] bg-white/90 backdrop-blur-xl">
      <div className="sp-container flex h-[72px] items-center justify-between">
        <div className="flex items-center gap-9">
          <button
            aria-label="Open navigation"
            className="sp-focus rounded-xl p-2 transition-colors hover:bg-[#f5f2ff] lg:hidden"
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X size={21} /> : <Menu size={21} />}
          </button>
          <ShopPilotLogo />
          {!appAuthed && (
            <nav className="hidden items-center gap-9 lg:flex">
              <Link className="text-[15px] font-medium text-[#141938] transition-colors hover:text-[#5a3edb]" href="/">
                Home
              </Link>
              <Link className="text-[15px] font-medium text-[#141938] transition-colors hover:text-[#5a3edb]" href="/about">
                About Us
              </Link>
            </nav>
          )}
        </div>

        <div className="flex items-center gap-4">
          {appAuthed && (
            <Link
              href="/saved"
              className="sp-focus hidden items-center gap-2 rounded-xl px-3 py-2 text-[14px] font-medium transition-all hover:bg-[#f5f2ff] hover:text-[#5a3edb] md:flex"
            >
              <Heart size={20} strokeWidth={1.9} /> Saved
            </Link>
          )}

          {/* Avatar / user menu (only when logged in) */}
          {!loading && user && (
            <div className="relative">
              <button
                aria-label="Profile menu"
                onClick={() => setShowUserMenu((v) => !v)}
                className="sp-focus grid h-10 w-10 place-items-center rounded-full bg-gradient-to-br from-[#536eff] via-[#7951ee] to-[#ce54d7] text-[17px] font-medium text-white shadow-[0_10px_22px_rgba(118,85,235,.23)] transition-all hover:scale-110 hover:shadow-[0_12px_28px_rgba(118,85,235,.36)] active:scale-100"
              >
                {initial}
              </button>

              {showUserMenu && (
                <div className="absolute right-0 top-12 z-50 w-56 rounded-2xl border border-[#e8e5f5] bg-white p-2 shadow-[0_14px_40px_rgba(60,44,140,.12)]">
                  <div className="border-b border-[#dcd7ef] px-3 py-3">
                    <div className="text-[14px] font-semibold text-[#1b2240]">{user.name}</div>
                    <div className="mt-0.5 truncate text-[12px] text-[#757d96]">{user.email}</div>
                  </div>
                  <Link
                    href="/dashboard"
                    onClick={() => setShowUserMenu(false)}
                    className="mt-1 flex w-full items-center rounded-xl px-3 py-2.5 text-[13px] text-[#2d3453] transition-all hover:translate-x-0.5 hover:bg-[#f6f4ff] hover:text-[#5a3edb]"
                  >
                    Dashboard
                  </Link>
                  <Link
                    href="/profile"
                    onClick={() => setShowUserMenu(false)}
                    className="flex w-full items-center rounded-xl px-3 py-2.5 text-[13px] text-[#2d3453] transition-all hover:translate-x-0.5 hover:bg-[#f6f4ff] hover:text-[#5a3edb]"
                  >
                    My Profile
                  </Link>
                  <div className="mt-1 border-t border-[#dcd7ef]" />
                  <button
                    onClick={handleSignOut}
                    className="mt-1 flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-[13px] text-[#c33] transition-all hover:bg-[#fff5f5] hover:translate-x-0.5"
                  >
                    <LogOut size={15} /> Sign out
                  </button>
                </div>
              )}

              {/* Click-outside dismiss */}
              {showUserMenu && (
                <button
                  className="fixed inset-0 z-40"
                  aria-hidden
                  onClick={() => setShowUserMenu(false)}
                />
              )}
            </div>
          )}

          {/* Not signed in and not loading — show sign in link */}
          {!loading && !user && (
            <Link
              href="/signin"
              className="rounded-xl border border-[#ddd8f0] px-4 py-2 text-[14px] font-medium text-[#4e40bf] transition-all hover:-translate-y-0.5 hover:bg-[#f7f4ff] hover:shadow-[0_4px_14px_rgba(90,62,219,.12)]"
            >
              Sign in
            </Link>
          )}
        </div>
      </div>

      {open && (
        <div className="border-t border-[#ecebf4] bg-white lg:hidden">
          <nav className="sp-container flex flex-col gap-4 py-5 text-[15px] font-medium">
            <Link href="/" onClick={() => setOpen(false)}>
              Home
            </Link>
            <Link href="/about" onClick={() => setOpen(false)}>
              About Us
            </Link>
            {user && (
              <>
                <Link href="/dashboard" onClick={() => setOpen(false)}>
                  Dashboard
                </Link>
                <Link href="/history" onClick={() => setOpen(false)}>
                  Search History
                </Link>
                <Link href="/saved" onClick={() => setOpen(false)}>
                  Saved Items
                </Link>
                <button onClick={handleSignOut} className="text-left text-[#c33]">
                  Sign out
                </button>
              </>
            )}
            {!user && (
              <Link href="/signin" onClick={() => setOpen(false)}>
                Sign in
              </Link>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}