"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function ScanPage() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [scanId, setScanId] = useState<string>("");
  const [busy, setBusy] = useState(false);

  async function run() {
    if (!file) {
      setError("Choose an Nmap XML file first.");
      return;
    }
    setBusy(true);
    setError("");
    setStatus("Uploadingâ€¦");
    try {
      const form = new FormData();
      form.append("file", file);
      const upload = await fetch(`${API_URL}/api/v1/evidence/nmap`, { method: "POST", body: form });
      if (!upload.ok) {
        const detail = await upload.json().catch(() => ({}));
        throw new Error(detail.detail ?? `Upload failed (${upload.status})`);
      }
      const uploadBody = await upload.json();
      setScanId(uploadBody.scan_id);
      setStatus(`Parsed ${uploadBody.asset_count} asset(s). Running analysisâ€¦`);

      const analysis = await fetch(`${API_URL}/api/v1/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scan_id: uploadBody.scan_id }),
      });
      if (!analysis.ok) throw new Error(`Analysis failed (${analysis.status})`);
      const analysisBody = await analysis.json();
      setStatus(`Analysis complete: ${analysisBody.finding_count} finding(s).`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setStatus("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-white">Scan</h1>
      <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-6 space-y-4">
        <p className="text-sm text-slate-400">Upload an Nmap XML file to normalize evidence, correlate findings, score risk, and generate AI analysis.</p>
        <input
          type="file"
          accept=".xml"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="block text-sm text-slate-300"
        />
        <button
          onClick={run}
          disabled={busy}
          className="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-500 disabled:opacity-50"
        >
          {busy ? "Workingâ€¦" : "Upload & Analyze"}
        </button>
        {status && <p className="text-sm text-slate-300">{status}</p>}
        {error && <p className="text-sm text-red-400">{error}</p>}
        {scanId && (
          <div className="flex gap-4 text-sm">
            <a className="text-sky-400 hover:underline" href="/findings">View findings</a>
            <a className="text-sky-400 hover:underline" href="/assets">View assets</a>
            <a className="text-sky-400 hover:underline" href="/reports">Reports</a>
          </div>
        )}
      </div>
    </div>
  );
}
