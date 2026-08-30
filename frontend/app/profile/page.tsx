"use client";

import { CalendarDays, Mail, UserRound, Globe } from "lucide-react";
import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { AppShell } from "../../components/shell/AppShell";
import { ProfileHeader } from "../../components/profile/ProfileHeader";
import { useAuth } from "../../lib/auth-context";

function joinedDate(createdAt?: string | null): string | null {
  if (!createdAt) return null;
  const d = new Date(createdAt);
  if (isNaN(d.getTime())) return null;
  return d.toLocaleDateString("en-US", { day: "numeric", month: "long", year: "numeric" });
}

function timeZone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "—";
  } catch {
    return "—";
  }
}

export default function ProfilePage() {
  const { user, loading } = useAuth();

  const rows: { label: string; value: string; Icon: LucideIcon }[] = user
    ? [
        { label: "Full Name", value: user.name, Icon: UserRound },
        { label: "Email Address", value: user.email, Icon: Mail },
        ...(joinedDate(user.created_at)
          ? [{ label: "Date Joined", value: joinedDate(user.created_at)!, Icon: CalendarDays }]
          : []),
        { label: "Time Zone", value: timeZone(), Icon: Globe },
      ]
    : [];

  return (
    <AppShell>
      <div className="sp-app-container flex min-h-full flex-col py-8">
        <h1 className="text-[30px] font-semibold">Profile</h1>
        <p className="mt-1 text-[15px] text-[#777e94]">Manage your account information.</p>

        {loading ? (
          <div className="mt-10 flex flex-1 items-center justify-center text-[15px] text-[#8a90a8]">
            Loading your profile…
          </div>
        ) : !user ? (
          <div className="mt-10 flex flex-1 flex-col items-center justify-center text-center text-[#8a90a8]">
            <div className="grid h-16 w-16 place-items-center rounded-2xl bg-[#f5f2ff] text-[28px]">👤</div>
            <p className="mt-4 text-[15px] font-medium text-[#444c6a]">You&apos;re not signed in</p>
            <p className="mt-2 max-w-[360px] text-[13px] leading-6 text-[#9099b4]">
              Sign in to view your account details.
            </p>
            <Link
              href="/signin"
              className="sp-gradient-btn mt-6 inline-flex items-center px-6 py-2.5 text-[13px] font-semibold"
            >
              Sign in
            </Link>
          </div>
        ) : (
          <>
            <div className="mt-7">
              <ProfileHeader user={user} />
            </div>
            <section className="sp-card mt-6 p-6 md:p-7">
              <div>
                <h2 className="text-[18px] font-semibold">Personal Information</h2>
                <p className="mt-1 text-[13px] text-[#767d92]">Your account details</p>
              </div>
              <div className="mt-6">
                {rows.map(({ label, value, Icon }) => (
                  <div
                    key={label}
                    className="grid grid-cols-[34px_180px_1fr] items-center gap-4 border-b border-[#f0eef5] py-5 last:border-0"
                  >
                    <div className="grid h-9 w-9 place-items-center rounded-xl bg-[#f3efff] text-[#6c4ef0]">
                      <Icon size={17} />
                    </div>
                    <div className="text-[13px] font-medium text-[#424a64]">{label}</div>
                    <div className="text-[14px] text-[#1d2441]">{value}</div>
                  </div>
                ))}
              </div>
            </section>
          </>
        )}
      </div>
    </AppShell>
  );
}
