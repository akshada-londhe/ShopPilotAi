"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthShell } from "../../components/shell/AuthShell";
import { Field } from "../../components/auth/Field";
import { signUp } from "../../lib/auth-client";
import { useAuth } from "../../lib/auth-context";

export default function SignUpPage() {
  const router = useRouter();
  const { refresh } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const name = (form.elements.namedItem("name") as HTMLInputElement).value;
    const email = (form.elements.namedItem("email") as HTMLInputElement).value;
    const password = (form.elements.namedItem("password") as HTMLInputElement).value;
    const confirm = (form.elements.namedItem("confirm") as HTMLInputElement).value;

    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await signUp(name, email, password);
      await refresh();
      router.push("/dashboard");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Sign up failed. Please try again.";
      if (msg.toLowerCase().includes("already exists") || msg.toLowerCase().includes("already registered")) {
        setError("An account with this email already exists. Try signing in instead.");
      } else if (msg.toLowerCase().includes("password") || msg.toLowerCase().includes("72")) {
        setError("Password must be between 8 and 72 characters.");
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell title="Create your account!" mode="signup">
      <div>
        <h1 className="text-[28px] font-semibold tracking-[-.04em]">Sign up</h1>
        <p className="mt-1 text-[15px] text-[#777e94]">Create your account to get started.</p>
      </div>
      <form onSubmit={submit} className="mt-6 space-y-3.5">
        <label className="block text-[13px] font-medium text-[#27304f]">
          Full name
          <div className="mt-1.5">
            <Field name="name" type="text" icon="user" placeholder="Enter your full name" required />
          </div>
        </label>
        <label className="block text-[13px] font-medium text-[#27304f]">
          Email address
          <div className="mt-1.5">
            <Field name="email" type="email" icon="mail" placeholder="Enter your email" required />
          </div>
        </label>
        <label className="block text-[13px] font-medium text-[#27304f]">
          Password
          <div className="mt-1.5">
            <Field name="password" type="password" icon="lock" placeholder="Create a password" minLength={8} required />
          </div>
        </label>
        <label className="block text-[13px] font-medium text-[#27304f]">
          Confirm password
          <div className="mt-1.5">
            <Field name="confirm" type="password" icon="lock" placeholder="Confirm your password" minLength={8} required />
          </div>
        </label>
        <p className="text-[12px] text-[#888ea2]">Password must be at least 8 characters long.</p>

        {error && (
          <div className="rounded-xl border border-[#f4d0d4] bg-[#fff6f7] px-4 py-2.5 text-[13px] text-[#c0354a]">
            {error}
            {error.toLowerCase().includes("already exists") && (
              <Link href="/signin" className="ml-1 font-semibold underline">
                Sign in →
              </Link>
            )}
          </div>
        )}

        <button
          className="sp-gradient-btn h-12 w-full text-[15px] font-semibold border border-[#704ef0]/40 shadow-md transition-all hover:border-[#6547ee] disabled:opacity-60"
          disabled={loading}
        >
          {loading ? "Creating account…" : "Create account"}
        </button>
        <p className="pt-3 text-center text-[15px] text-[#767d93]">
          Already have an account?{" "}
          <Link href="/signin" className="font-medium text-[#704ef0]">
            Sign in
          </Link>
        </p>
      </form>
    </AuthShell>
  );
}