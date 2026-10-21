"use client";

import { useState } from "react";
import Link from "next/link";
import { apiGet, apiPost, apiDelete, type ApiError, type Report, type ReportSummary, type Scan } from "@/lib/api";

interface ReportsPanelProps {
  initialReports: ReportSummary[];
  scans: Scan[];
}

export default function ReportsPanel({ initialReports, scans }: ReportsPanelProps) {
  const [reports, setReports] = useState<ReportSummary[]>(initialReports);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [scanId, setScanId] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);

  async function generate() {
    setBusy(true);
    setError(null);
    setStatus("");

    const id = scanId ?? scans[0]?.id ?? "";
    if (!id) {
      setError({ kind: "network", message: "No scans available to report on." });
      setBusy(false);
      return;
    }

    try {
      const res = await apiPost<Report>("/api/v1/reports", { scan_id: id });
      if (!res.ok) {
        setError(res.error);
        return;
      }
      const body = res.data;
      setSelectedId(body.id);
      setSelectedReport(body);
      setStatus("Report generated.");
      setReports((prev) => [{ id: body.id, scan_id: body.scan_id, created_at: body.created_at }, ...prev]);
    } catch (err) {
      setError({ kind: "network", message: err instanceof Error ? err.message : "Unknown error" });
    } finally {
      setBusy(false);
    }
  }

  async function openReport(reportId: string) {
    setError(null);
    setStatus("");

    const res = await apiGet<Report>(`/api/v1/reports/${reportId}`);
    if (!res.ok) {
      setError(res.error);
      setSelectedReport(null);
      return;
    }
    setSelectedReport(res.data);
  }

  async function deleteReport(reportId: string) {
    if (!window.confirm("Delete this report? This cannot be undone.")) return;

    const res = await apiDelete<null>(`/api/v1/reports/${reportId}`);
    if (!res.ok) {
      setError(res.error);
      return;
    }

    setReports((prev) => prev.filter((r) => r.id !== reportId));
    if (selectedId === reportId) {
      setSelectedId(null);
      setSelectedReport(null);
    }
  }

  async function copyToClipboard(content: string) {
    try {
      await navigator.clipboard.writeText(content);
      setStatus("Copied to clipboard.");
    } catch {
      setError({ kind: "network", message: "Clipboard access denied." });
    }
  }

  async function download(content: string, scanId: string) {
    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `sentinel-report-${scanId.slice(0, 8)}.md`;
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
          <label htmlFor="scan-select" className="block text-xs uppercase tracking-wide text-slate-500">
            Scan
          </label>
          <select
            id="scan-select"
            value={scanId ?? ""}
            onChange={(e) => setScanId(e.target.value || null)}
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-sky-500"
          >
            <option value="">Latest scan</option>
            {scans.map((s) => (
              <option key={s.id} value={s.id}>
                {s.filename ?? s.id.slice(0, 8)} — {s.created_at ? new Date(s.created_at).toLocaleString() : "—"}
              </option>
            ))}
          </select>
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
        </div>

        {status && <p className="text-sm text-slate-300">{status}</p>}
        {error && <p className="text-sm text-red-400">{error.message}</p>}
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
                    <td className="py-2 font-mono text-slate-300">
                      <Link className="text-sky-400 hover:underline" href={`/scans/${r.scan_id}`}>
                        {r.scan_id.slice(0, 8)}
                      </Link>
                    </td>
                    <td className="py-2">
                      <div className="flex gap-1">
                        <button
                          type="button"
                          onClick={() => openReport(r.id)}
                          className="text-sky-400 hover:underline text-sm"
                        >
                          View
                        </button>
                        <button
                          type="button"
                          onClick={() => deleteReport(r.id)}
                          className="text-red-400 hover:underline text-sm"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selectedReport && (
        <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-6">
          <div className="flex items-baseline justify-between mb-3">
            <h2 className="text-lg font-medium text-white">Report</h2>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => download(selectedReport.content, selectedReport.scan_id)}
                className="rounded-md border border-slate-700 px-3 py-1.5 text-xs font-medium text-slate-200 hover:border-slate-500"
              >
                Download .md
              </button>
              <button
                type="button"
                onClick={() => copyToClipboard(selectedReport.content)}
                className="rounded-md border border-slate-700 px-3 py-1.5 text-xs font-medium text-slate-200 hover:border-slate-500"
              >
                Copy
              </button>
              <button
                type="button"
                onClick={() => deleteReport(selectedReport.id)}
                className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-1.5 text-xs font-medium text-red-300 hover:bg-red-500/20"
              >
                Delete
              </button>
            </div>
          </div>
          <div className="prose prose-slate max-w-none text-sm text-slate-300">
            {renderMarkdown(selectedReport.content)}
          </div>
        </section>
      )}
    </div>
  );
}

function renderMarkdown(markdown: string): React.ReactNode {
  const lines = markdown.split("\n");
  const blocks: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.startsWith("```")) {
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      i++;
      blocks.push(
        <pre key={blocks.length} className="rounded-md border border-slate-700 bg-slate-950 p-3 font-mono text-xs overflow-x-auto">
          <code>{codeLines.join("\n")}</code>
        </pre>
      );
      continue;
    }

    if (/^[-*_]{3,}$/.test(line.trim())) {
      blocks.push(<hr key={blocks.length} className="my-4 border-slate-800" />);
      i++;
      continue;
    }

    const headerMatch = line.match(/^(#{1,6})\s(.+)$/);
    if (headerMatch) {
      const level = headerMatch[1].length;
      const text = headerMatch[2];
      const Tag = `h${level}` as keyof React.JSX.IntrinsicElements;
      blocks.push(
        <Tag key={blocks.length} className="my-3 font-semibold text-white">
          {text}
        </Tag>
      );
      i++;
      continue;
    }

    if (/^[-*+]\s/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*+]\s/.test(lines[i])) {
        items.push(lines[i].replace(/^[-*+]\s/, ""));
        i++;
      }
      blocks.push(
        <ul key={blocks.length} className="list-disc space-y-1 pl-5 text-slate-300">
          {items.map((item, idx) => (
            <li key={idx}>{item}</li>
          ))}
        </ul>
      );
      continue;
    }

    if (line.trim() === "") {
      i++;
      continue;
    }

    const paraLines: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !lines[i].startsWith("```") &&
      !/^[-*+]\s/.test(lines[i]) &&
      !/^#{1,6}\s/.test(lines[i]) &&
      !/^[-*_]{3,}$/.test(lines[i].trim())
    ) {
      paraLines.push(lines[i]);
      i++;
    }
    blocks.push(
      <p key={blocks.length} className="my-2 text-slate-300">
        {paraLines.join(" ")}
      </p>
    );
  }

  return <>{blocks}</>;
}
