"use client";

export default function GlobalError({ error, retry }: { error: Error & { digest?: string }; retry: () => void }) {
  return (
    <html lang="en">
      <body className="flex min-h-screen items-center justify-center bg-slate-950 p-8 font-sans text-slate-200">
        <div role="alert" className="max-w-lg rounded-lg border border-red-500/40 bg-red-500/10 p-6">
          <h1 className="text-lg font-semibold text-red-200">Sentinel-AI crashed</h1>
          <p className="mt-2 text-sm text-red-200/70">{error.message}</p>
          {error.digest && <p className="mt-1 font-mono text-xs text-red-200/60">Reference: {error.digest}</p>}
          <button
            type="button"
            onClick={() => retry()}
            className="mt-4 rounded-md bg-red-500/20 px-4 py-2 text-sm font-medium text-red-100 hover:bg-red-500/30"
          >
            Reload
          </button>
        </div>
      </body>
    </html>
  );
}