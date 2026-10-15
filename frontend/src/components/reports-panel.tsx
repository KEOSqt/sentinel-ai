"use client";

import { useState } from "react";
import { apiGet, apiPost, apiUrl, type Report, type ReportSummary } from "@/lib/api";

export function ReportsPanel({ initialReports }: { initialReports: ReportSummary[] }) {
  const [scanId, setScanId] = useState("");
  const [reports, setReports] = useState<ReportSummary[]>(initialReports);
  const [selected, setSelected] = useState<Report | null>(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function generate() {
    setBusy(true);
    setError("");
    setStatus("");
    try {
      let id = scanId.trim();
      if (!id) {
        const scansRes = await fetch(apiUrl("/api/v1/scans"));
        if (!scansRes.ok) throw new Error(`Could not load scans (${scansRes.status})`);
        const scans = await scansRes.json();
        if (!Array.isArray(scans) || scans.length === 0) throw new Error("No scans available");
        id = scans[0].id;
      }
      const res = await apiPost<Report>("/api/v1/reports", { scan_id: id });
      if (!res.ok) {
        setError(res.error.message);
        return;
      }
      const body = res.data;
      setSelected(body);
      setStatus("Report generated.");
      // Prepend locally rather than refetching the list.
      setReports((prev) => [{ id: body.id, scan_id: body.scan_id, created_at: body.created_at }, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setBusy(false);
    }
  }

  async function open(reportId: string) {
    setError("");
    setStatus("");
    const res = await apiGet<Report>(`/api/v1/reports/${reportId}`);
    if (!res.ok) {
      setError(res.error.message);
      return;
    }
    setSelected(res.data);
  }

  function download() {
    if (!selected) return;
    const blob = new Blob([selected.content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `sentinel-report-${selected.scan_id.slice(0, 8)}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      <div className="space-y-4 rounded-lg border border-slate-800 bg-slate-900/60 p-6">
        <p className="text-sm text-slate-400">
          Generate a markdown security report for a scan, or reopen one you generated earlier.
        </p>
        <div className="space-y-1">
          <label htmlFor="scan-id" className="block text-xs uppercase tracking-wide text-slate-500">
            Scan ID
          </label>
          <input
            id="scan-id"
            value={scanId}
            onChange={(e) => setScanId(e.target.value)}
            placeholder="Leave blank for the latest scan"
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
          />
        </div>
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={generate}
            disabled={busy}
            className="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-500 disabled:opacity-50"
          >
            {busy ? "Generating…" : "Generate Report"}
          </button>
          {selected && (
            <button
              type="button"
              onClick={download}
              className="rounded-md border border-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:border-slate-500"
            >
              Download .md
            </button>
          )}
        </div>
        {status && <p className="text-sm text-slate-300">{status}</p>}
        {error && <p className="text-sm text-red-400">{error}</p>}
      </div>

      <section>
        <h2 className="mb-3 text-lg font-medium text-white">Previous reports</h2>
        {reports.length === 0 ? (
          <p className="text-sm text-slate-500">No reports generated yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <caption className="sr-only">Reports generated so far, newest first</caption>
              <thead>
                <tr className="text-left text-slate-500">
                  <th scope="col" className="pb-2">Created</th>
                  <th scope="col" className="pb-2">Scan</th>
                  <th scope="col" className="pb-2">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {reports.map((r) => (
                  <tr key={r.id} className="border-t border-slate-800">
                    <td className="py-2 text-slate-500">
                      {r.created_at ? new Date(r.created_at).toLocaleString() : "—"}
                    </td>
                    <td className="py-2 font-mono text-slate-300">{r.scan_id}</td>
                    <td className="py-2">
                      <button
                        type="button"
                        onClick={() => open(r.id)}
                        className="text-sky-400 hover:underline"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selected && (
        <section>
          <h2 className="mb-2 text-lg font-medium text-white">Preview</h2>
          <pre className="whitespace-pre-wrap rounded-lg border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
            {selected.content}
          </pre>
        </section>
      )}
    </div>
  );
}