import Link from "next/link";

export default function NotFound() {
  return (
    <div className="rounded-lg border border-dashed border-slate-800 bg-slate-900/40 px-4 py-10 text-center">
      <p className="text-sm font-medium text-slate-300">Page not found</p>
      <Link className="mt-3 inline-block text-sm text-sky-400 hover:underline" href="/">
        Back to overview
      </Link>
    </div>
  );
}