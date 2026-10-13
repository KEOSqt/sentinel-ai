"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";
import type { ApiError } from "@/lib/api";

/**
 * Shown when the backend could not be reached or returned an error. Distinct
 * from `EmptyState`, which means the backend answered and had nothing to show.
 */
export function ApiErrorState({
  title = "Cannot reach the Sentinel-AI backend",
  errors,
}: {
  title?: string;
  errors: ApiError[];
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  return (
    <div role="alert" className="rounded-lg border border-red-500/40 bg-red-500/10 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium text-red-200">{title}</p>
          <ul className="mt-1 space-y-0.5 text-xs text-red-200/70">
            {errors.map((error, i) => (
              <li key={`${error.kind}-${i}`}>
                <code className="font-mono">{error.status ?? error.kind}</code> {error.message}
              </li>
            ))}
          </ul>
          <p className="mt-2 text-xs text-red-200/60">
            Start the API with <code className="font-mono">docker compose up</code> or{" "}
            <code className="font-mono">uvicorn app.main:app</code>, then retry.
          </p>
        </div>
        <button
          type="button"
          onClick={() => startTransition(() => router.refresh())}
          disabled={pending}
          className="shrink-0 rounded-md bg-red-500/20 px-3 py-1.5 text-xs font-medium text-red-100 hover:bg-red-500/30 disabled:opacity-50"
        >
          {pending ? "Retrying…" : "Retry"}
        </button>
      </div>
    </div>
  );
}