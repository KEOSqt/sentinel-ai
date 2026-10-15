"use client";

import { useEffect } from "react";

export default function AppError({ error, retry }: { error: Error & { digest?: string }; retry: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div role="alert" className="rounded-lg border border-red-500/40 bg-red-500/10 p-6">
      <h2 className="text-lg font-medium text-red-200">Something went wrong rendering this page.</h2>
      {error.digest && <p className="mt-1 font-mono text-xs text-red-200/60">Reference: {error.digest}</p>}
      <button
        type="button"
        onClick={() => retry()}
        className="mt-4 rounded-md bg-red-500/20 px-4 py-2 text-sm font-medium text-red-100 hover:bg-red-500/30"
      >
        Try again
      </button>
    </div>
  );
}