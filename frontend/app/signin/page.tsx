"use client";

import Link from "next/link";
import { FormEvent, Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AuthShell } from "../../components/shell/AuthShell";
import { Field } from "../../components/auth/Field";
import { signIn } from "../../lib/auth-client";
import { useAuth } from "../../lib/auth-context";

function SignInInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next");
  const { refresh } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const email = (form.elements.namedItem("email") as HTMLInputElement).value;
    const password = (form.elements.namedItem("password") as HTMLInputElement).value;

    setLoading(true);
    setError(null);
    try {
      await signIn(email, password);
      await refresh();
      // Return to where the user came from (e.g. their search), else dashboard.
      router.push(next && next.startsWith("/") ? next : "/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell title="Welcome back!" mode="signin">
      <div>
        <h1 className="text-[31px] font-semibold tracking-[-.04em]">Sign in</h1>
        <p className="mt-2 text-[16px] text-[#777e94]">Welcome back! Please enter your details.</p>
      </div>
      <form onSubmit={submit} className="mt-9 space-y-5">
        <label className="block text-[14px] font-medium text-[#27304f]">
          Email address
          <div className="mt-2">
            <Field name="email" type="email" icon="mail" placeholder="Enter your email" required />
          </div>
        </label>
        <label className="block text-[14px] font-medium text-[#27304f]">
          Password
          <div className="mt-2">
            <Field name="password" type="password" icon="lock" placeholder="Enter your password" required />
          </div>
        </label>
        <div className="flex justify-end">
          <Link href="/forgot-password" className="text-[13px] font-medium text-[#704ef0]">
            Forgot password?
          </Link>
        </div>

        {error && (
          <div className="rounded-xl border border-[#f4d0d4] bg-[#fff6f7] px-4 py-3 text-[13px] text-[#c0354a]">
            {error}
          </div>
        )}

        <button
          className="sp-gradient-btn h-12 w-full text-[15px] font-semibold border border-[#704ef0]/40 shadow-md transition-all hover:border-[#6547ee] disabled:opacity-60"
          disabled={loading}
        >
          {loading ? "Signing in…" : "Sign in"}
        </button>
        <p className="pt-5 text-center text-[15px] text-[#767d93]">
          Don&apos;t have an account?{" "}
          <Link href="/signup" className="font-medium text-[#704ef0]">
            Sign up
          </Link>
        </p>
      </form>
    </AuthShell>
  );
}

export default function SignInPage() {
  return (
    <Suspense fallback={null}>
      <SignInInner />
    </Suspense>
  );
}