"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiPost } from "@/lib/api";

/**
 * Runs the analysis for one scan — first time or again after a new upload of
 * similar evidence. Findings, counts and the AI analysis are all rendered by
 * the server component, so a successful run just pulls the new server state in.
 */
export function ScanAnalysisActions({ scanId, analysed }: { scanId: string; analysed: boolean }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function run() {
    setBusy(true);
    setError("");

    const result = await apiPost<{ scan_id: string }>(`/api/v1/analyze`, { scan_id: scanId });
    if (!result.ok) {
      setError(result.error.message);
    } else {
      router.refresh();
    }
    setBusy(false);
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        type="button"
        onClick={run}
        disabled={busy}
        className="rounded-md bg-sky-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-sky-500 disabled:opacity-50"
      >
        {busy ? "Analysing…" : analysed ? "Re-run analysis" : "Run analysis"}
      </button>
      {busy && <span className="text-xs text-slate-500">Correlating evidence…</span>}
      {error && <p className="text-sm text-red-400">{error}</p>}
    </div>
  );
}
