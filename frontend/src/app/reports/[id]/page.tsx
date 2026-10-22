"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { notFound, useRouter, useParams } from "next/navigation";
import { apiDelete, apiGet, type ApiError, type Report } from "@/lib/api";
import { Markdown } from "@/lib/markdown";
import { useRetry } from "@/lib/use-retry";
import { PageSkeleton } from "@/lib/ui";

export default function ReportDetailPage() {
  const { id } = useParams();
  const idStr = (Array.isArray(id) ? id[0] : id) ?? "";
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [notFoundRoute, setNotFoundRoute] = useState(false);
  const { attempt, retry } = useRetry();

  const router = useRouter();

  function handleRetry() {
    setLoading(true);
    setError(null);
    retry();
  }

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const result = await apiGet<Report>(`/api/v1/reports/${encodeURIComponent(idStr!)}`);
      if (cancelled) return;
      if (!result.ok) {
        if (result.error.kind === "http" && result.error.status === 404) {
          setNotFoundRoute(true);
        } else {
          setError(result.error);
        }
      } else {
        setReport(result.data);
      }
      setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, [attempt, idStr]);

  if (notFoundRoute) {
    notFound();
  }

  if (loading) {
    return <PageSkeleton />;
  }

  if (error !== null) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold text-white">Report</h1>
        <p className="text-sm text-slate-400">{idStr.slice(0, 8)}</p>
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-6">
          <h2 className="text-lg font-medium text-red-200">Failed to load report</h2>
          <p className="mt-1 text-sm text-red-300">{error.message}</p>
          <button
            type="button"
            onClick={handleRetry}
            className="mt-3 rounded-md bg-red-500/20 px-3 py-1.5 text-xs font-medium text-red-100 hover:bg-red-500/30"
          >
            Retry
          </button>
        </div>
        <Link className="inline-block text-sm text-sky-400 hover:underline" href="/reports">
          Back to reports
        </Link>
      </div>
    );
  }

  const content = report!.content;

  function download() {
    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `sentinel-report-${report!.scan_id.slice(0, 8)}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  async function copyToClipboard() {
    try {
      await navigator.clipboard.writeText(content);
    } catch {
      // clipboard access denied; fall back silently
    }
  }

  async function del() {
    if (!window.confirm("Delete this report? This cannot be undone.")) return;
    const result = await apiDelete<null>(`/api/v1/reports/${idStr}`);
    if (!result.ok) {
      setError(result.error);
      return;
    }
    router.push("/reports");
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-baseline gap-3">
        <h1 className="text-2xl font-semibold text-white">Report</h1>
        <span className="text-slate-400">{report!.scan_id.slice(0, 8)}</span>
        <span className="text-sm text-slate-500">generated {report!.created_at ? new Date(report!.created_at).toLocaleString() : "—"}</span>
        <Link className="text-sky-400 hover:underline" href={`/scans/${report!.scan_id}`}>
          Open scan
        </Link>
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={download}
          className="rounded-md border border-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:border-slate-500"
        >
          Download .md
        </button>
        <button
          type="button"
          onClick={copyToClipboard}
          className="rounded-md border border-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:border-slate-500"
        >
          Copy to clipboard
        </button>
        <button
          type="button"
          onClick={del}
          className="rounded-md border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm font-medium text-red-300 hover:bg-red-500/20"
        >
          Delete
        </button>
      </div>

      <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-6">
        <h2 className="mb-3 text-lg font-medium text-white">Report</h2>
        <div className="prose prose-slate max-w-none text-sm text-slate-300">
          <Markdown content={content} />
        </div>
      </section>

      <Link className="inline-block text-sm text-sky-400 hover:underline" href="/reports">
        Back to reports
      </Link>
    </div>
  );
}
