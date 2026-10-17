"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";

export function Header() {
  const { user, signOut } = useAuth();
  const router = useRouter();

  async function handleLogout() {
    await signOut();
    router.push("/");
  }

  return (
    <header className="flex items-center justify-between px-[5%] py-5">
      <Link href="/" className="text-xl font-extrabold tracking-tight">
        <span className="text-gradient">Resume Ranker</span>
      </Link>
      <nav className="flex items-center gap-6 text-sm">
        <Link href="/#features" className="text-slate-300 transition hover:text-brand">
          Features
        </Link>
        {user ? (
          <div className="flex items-center gap-4">
            <Link
              href="/dashboard"
              className="text-slate-300 transition hover:text-brand"
            >
              Dashboard
            </Link>
            <span className="hidden text-slate-400 sm:inline">{user.email}</span>
            <button
              onClick={handleLogout}
              className="rounded-lg border border-white/15 px-4 py-2 text-slate-200 transition hover:border-brand hover:text-brand"
            >
              Logout
            </button>
          </div>
        ) : (
          <Link
            href="/dashboard"
            className="rounded-lg border border-white/15 px-4 py-2 text-slate-200 transition hover:border-brand hover:text-brand"
          >
            Sign In
          </Link>
        )}
      </nav>
    </header>
  );
}
