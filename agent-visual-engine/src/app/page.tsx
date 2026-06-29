import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center gap-6 px-6 text-center">
      <p className="text-xs uppercase tracking-[0.2em] text-neutral-500">Agent Visual Engine</p>
      <h1 className="text-balance text-2xl font-semibold tracking-tight text-neutral-100">
        First visual proof asset
      </h1>
      <Link
        href="/preview"
        className="rounded-full border border-white/10 bg-white/5 px-5 py-2.5 text-sm font-medium text-neutral-200 transition-colors hover:bg-white/10"
      >
        Open /preview →
      </Link>
    </main>
  );
}
