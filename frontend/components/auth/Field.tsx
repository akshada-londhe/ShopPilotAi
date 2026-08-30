import { Eye, EyeOff, LockKeyhole, Mail, UserRound } from "lucide-react";
import { InputHTMLAttributes, useState } from "react";

export function Field({ type, icon, ...props }: InputHTMLAttributes<HTMLInputElement> & { icon: "mail" | "lock" | "user" }) {
  const [show, setShow] = useState(false);
  const password = type === "password";
  const Icon = icon === "mail" ? Mail : icon === "user" ? UserRound : LockKeyhole;
  return (
    <div className="relative">
      <Icon size={19} className="absolute left-4 top-1/2 -translate-y-1/2 text-[#7b8197]" />
      <input
        {...props}
        type={password ? (show ? "text" : "password") : type}
        className="sp-focus h-14 w-full rounded-xl border border-[#dbdce8] bg-white pl-12 pr-12 text-[15px] text-[#17203e] outline-none placeholder:text-[#969bad] focus:border-[#a48cff]"
      />
      {password && (
        <button type="button" aria-label={show ? "Hide password" : "Show password"} className="absolute right-4 top-1/2 -translate-y-1/2 text-[#7b8197]" onClick={() => setShow((v) => !v)}>
          {show ? <EyeOff size={18} /> : <Eye size={18} />}
        </button>
      )}
    </div>
  );
}