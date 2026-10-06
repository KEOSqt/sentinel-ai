"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function ReportsPage() {
  const [scanId, setScanId] = useState("");
  const [report, setReport] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function generate() {
    setBusy(true);
    setError("");
    setReport("");
    try {
      let id = scanId.trim();
      if (!id) {
        const scansRes = await fetch(`${API_URL}/api/v1/scans`);
        const scans = await scansRes.json();
        if (!Array.isArray(scans) || scans.length === 0) throw new Error("No scans available");
        id = scans[0].id;
      }
      const res = await fetch(`${API_URL}/api/v1/reports`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scan_id: id }),
      });
      if (!res.ok) throw new Error(`Report failed (${res.status})`);
      const body = await res.json();
      setReport(body.content);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-white">Reports</h1>
      <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-6 space-y-4">
        <input
          value={scanId}
          onChange={(e) => setScanId(e.target.value)}
          placeholder="Scan ID (leave blank for latest)"
          className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
        />
        <button
          onClick={generate}
          disabled={busy}
          className="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-500 disabled:opacity-50"
        >
          {busy ? "Generatingâ€¦" : "Generate Report"}
        </button>
        {error && <p className="text-sm text-red-400">{error}</p>}
      </div>
      {report && (
        <pre className="whitespace-pre-wrap rounded-lg border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
          {report}
        </pre>
      )}
    </div>
  );
}
