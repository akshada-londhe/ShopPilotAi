import { LucideIcon } from "lucide-react";

export function MetricCard({ title, value, delta, Icon, action }: { title: string; value: string | number; delta?: string; Icon: LucideIcon; action?: string }) {
  return (
    <div className="sp-card p-5">
      <div className="flex items-start justify-between">
        <div className="grid h-12 w-12 place-items-center rounded-full bg-[#f1efff] text-[#604cf1]"><Icon size={21} /></div>
        <span className="text-[12px] text-[#6e748b]">{action ?? ""}</span>
      </div>
      <div className="mt-5 text-[13px] font-semibold text-[#222949]">{title}</div>
      <div className="mt-1 text-[29px] font-semibold tracking-[-.035em] text-[#12183f]">{value}</div>
      {delta && <div className="mt-2 text-[12px] font-semibold text-[#1caa6c]">{delta}</div>}
    </div>
  );
}