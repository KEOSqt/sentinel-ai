"use client";

import Link from "next/link";
import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type SourceKind = "file" | "paste";

export default function ScanPage() {
  const [file, setFile] = useState<File | null>(null);
  const [xmlText, setXmlText] = useState<string>("");
  const [sourceName, setSourceName] = useState<string>("");
  const [sourceKind, setSourceKind] = useState<SourceKind>("file");
  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [scanId, setScanId] = useState<string>("");
  const [busy, setBusy] = useState(false);

  async function run() {
    const source = sourceKind === "file" ? file : xmlText.trim();
    if (!source) {
      setError(
        sourceKind === "file"
          ? "Choose an Nmap XML file first."
          : "Paste Nmap XML content first.",
      );
      return;
    }

    const baseName = sourceName.trim() || (file ? file.name : "paste");
    const name = baseName.toLowerCase().endsWith(".xml") ? baseName : `${baseName}.xml`;
    setBusy(true);
    setError("");
    setStatus("Uploading…");

    try {
      const form = new FormData();
      if (sourceKind === "file" && file) {
        form.append("file", file, name);
      } else {
        const blob = new Blob([xmlText.trim()], { type: "application/xml" });
        form.append("file", blob, name);
      }

      const upload = await fetch(`${API_URL}/api/v1/evidence/nmap`, {
        method: "POST",
        body: form,
      });
      if (!upload.ok) {
        const detail = await upload.json().catch(() => ({}));
        throw new Error(detail.detail ?? `Upload failed (${upload.status})`);
      }
      const uploadBody = await upload.json();
      setScanId(uploadBody.scan_id);
      setStatus(`Parsed ${uploadBody.asset_count} asset(s). Running analysis…`);

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
        <p className="text-sm text-slate-400">
          Upload an Nmap XML file or paste the XML content below to normalize evidence, correlate findings,
          score risk, and generate AI analysis.
        </p>

        {/* Source selector */}
        <div className="flex items-start gap-4">
          <div className="flex flex-col gap-2">
            <button
              type="button"
              onClick={() => {
                setSourceKind("file");
                setXmlText("");
              }}
              className={`flex items-center gap-2 rounded-md border px-3 py-2 text-sm font-medium text-left ${
                sourceKind === "file"
                  ? "border-sky-500/60 bg-sky-500/20 text-sky-200"
                  : "border-slate-700 text-slate-300 hover:border-slate-600 hover:text-slate-200"
              }`}
            >
              <span className="w-4 h-4">📎</span> Attach file
            </button>
            <button
              type="button"
              onClick={() => {
                setSourceKind("paste");
                setFile(null);
              }}
              className={`flex items-center gap-2 rounded-md border px-3 py-2 text-sm font-medium text-left ${
                sourceKind === "paste"
                  ? "border-sky-500/60 bg-sky-500/20 text-sky-200"
                  : "border-slate-700 text-slate-300 hover:border-slate-600 hover:text-slate-200"
              }`}
            >
              <span className="w-4 h-4">📋</span> Paste XML
            </button>
          </div>
        </div>

        {/* File attachment area */}
        {sourceKind === "file" && (
          <div className="border border-dashed border-slate-700 rounded-lg p-4 bg-slate-950/50">
            <input
              type="file"
              accept=".xml"
              id="nmap-file"
              className="sr-only"
              onChange={(e) => {
                setFile(e.target.files?.[0] ?? null);
                setXmlText("");
              }}
            />
            <label htmlFor="nmap-file" className="flex flex-col items-center gap-2 cursor-pointer">
              <span className="text-lg">📁</span>
              <span className="font-medium text-slate-200">
                {file ? file.name : "Click to attach an Nmap XML file"}
              </span>
              <span className="text-xs text-slate-500">
                .xml only • will be used as the scan name
              </span>
            </label>
            {file && (
              <div className="mt-2 flex items-center gap-2">
                <span className="text-xs text-slate-400">File name:</span>
                <input
                  type="text"
                  value={sourceName}
                  onChange={(e) => setSourceName(e.target.value)}
                  placeholder="e.g. office-floor-3.xml"
                  className="flex-1 rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                />
              </div>
            )}
          </div>
        )}

        {/* Paste area */}
        {sourceKind === "paste" && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <label className="text-xs uppercase tracking-wide text-slate-500">XML content</label>
              <span className="text-xs text-slate-500">Paste full Nmap XML output</span>
            </div>
            <textarea
              value={xmlText}
              onChange={(e) => {
                setXmlText(e.target.value);
                setFile(null);
              }}
              rows={8}
              placeholder="Paste Nmap XML scan output here…"
              className="block w-full text-sm text-slate-300 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-xs focus:outline-none focus:border-sky-500"
            />
            <div className="flex items-center gap-2">
              <label className="text-xs uppercase tracking-wide text-slate-500">Scan name</label>
              <input
                type="text"
                value={sourceName}
                onChange={(e) => setSourceName(e.target.value)}
                placeholder="e.g. office-floor-3"
                className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              />
              <span className="text-xs text-slate-500">.xml will be added automatically</span>
            </div>
          </div>
        )}

        <button
          onClick={run}
          disabled={busy}
          className="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-500 disabled:opacity-50"
        >
          {busy ? "Working…" : "Upload & Analyze"}
        </button>

        {status && <p className="text-sm text-slate-300">{status}</p>}
        {error && <p className="text-sm text-red-400">{error}</p>}
        {scanId && (
          <div className="flex gap-4 text-sm">
            <Link className="text-sky-400 hover:underline" href={`/scans/${scanId}`}>
              Open this scan
            </Link>
            <Link className="text-sky-400 hover:underline" href="/findings">View findings</Link>
            <Link className="text-sky-400 hover:underline" href="/assets">View assets</Link>
            <Link className="text-sky-400 hover:underline" href="/reports">Reports</Link>
          </div>
        )}
      </div>
    </div>
  );
}
