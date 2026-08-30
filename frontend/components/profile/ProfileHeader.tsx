import type { AuthUser } from "../../lib/auth-client";

function initial(name: string): string {
  return name.trim().charAt(0).toUpperCase() || "?";
}

function memberSince(createdAt?: string | null): string | null {
  if (!createdAt) return null;
  const d = new Date(createdAt);
  if (isNaN(d.getTime())) return null;
  return d.toLocaleDateString("en-US", { month: "long", year: "numeric" });
}

export function ProfileHeader({ user }: { user: AuthUser }) {
  const since = memberSince(user.created_at);
  return (
    <div className="rounded-[22px] border border-[#ebe8f4] bg-gradient-to-r from-white via-[#fbf9ff] to-[#f7f3ff] p-6 shadow-[0_8px_28px_rgba(54,42,133,.05)] md:p-7">
      <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-5">
          <div className="relative">
            <div className="grid h-28 w-28 place-items-center rounded-full bg-gradient-to-br from-[#5371fe] via-[#7a50ee] to-[#ca50d8] text-[48px] text-white shadow-[0_16px_34px_rgba(111,75,231,.24)]">
              {initial(user.name)}
            </div>
          </div>
          <div>
            <h2 className="text-[27px] font-semibold tracking-[-.03em]">{user.name}</h2>
            <p className="mt-1 text-[15px] text-[#686f87]">{user.email}</p>
            {since && <p className="mt-3 text-[13px] text-[#777e95]">Member since {since}</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
