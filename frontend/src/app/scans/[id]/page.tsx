"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { notFound, useParams } from "next/navigation";
import { ApiErrorState } from "@/components/api-error-state";
import { ScanAnalysisActions } from "@/components/scan-analysis-actions";
import { apiGet, type AIAnalysis, type ApiError, type ScanDetail } from "@/lib/api";
import { useRetry } from "@/lib/use-retry";
import { Card, EmptyState, PageSkeleton, SeverityBadge, StatusBadge } from "@/lib/ui";

function when(value?: string | null) {
  return value ? new Date(value).toLocaleString() : "—";
}

function AnalysisLists({ analysis }: { analysis: AIAnalysis }) {
  const lists = [
    { title: "Priority findings", items: analysis.priority_findings },
    { title: "Attack paths", items: analysis.attack_paths },
    { title: "Recommendations", items: analysis.recommendations },
    { title: "Missing information", items: analysis.missing_information },
  ].filter((l) => l.items.length > 0);

  if (lists.length === 0) return null;
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {lists.map((list) => (
        <div key={list.title} className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
          <h3 className="mb-2 text-sm font-medium text-white">{list.title}</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-slate-300">
            {list.items.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

export default function ScanDetailPage() {
  const { id } = useParams();
  const idStr = Array.isArray(id) ? id[0] : id;
  const [data, setData] = useState<ScanDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [notFoundRoute, setNotFoundRoute] = useState(false);
  const { attempt, retry } = useRetry();

  function handleRetry() {
    setLoading(true);
    setError(null);
    retry();
  }

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const result = await apiGet<ScanDetail>(`/api/v1/scans/${encodeURIComponent(idStr!)}`);
      if (cancelled) return;
      if (!result.ok) {
        if (result.error.kind === "http" && result.error.status === 404) {
          setNotFoundRoute(true);
        } else {
          setError(result.error);
        }
      } else {
        setData(result.data);
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
        <h1 className="font-mono text-2xl font-semibold text-white">{idStr!.slice(0, 8)}</h1>
        <ApiErrorState errors={[error]} onRetry={handleRetry} />
        <Link className="inline-block text-sm text-sky-400 hover:underline" href="/">
          Back to overview
        </Link>
      </div>
    );
  }

  const { scan, analysis, assets, findings, counts } = data!;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-baseline gap-3">
        <h1 className="text-2xl font-semibold text-white">{scan.filename ?? scan.id}</h1>
        <span className="text-slate-400">{scan.status}</span>
        <span className="text-sm text-slate-500">scanned {when(scan.created_at)}</span>
        {/* The filename can repeat across uploads, so the id is always shown. */}
        <span className="font-mono text-xs text-slate-500">{scan.id.slice(0, 8)}</span>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card title="Assets" value={assets.length} />
        <Card title="Findings" value={findings.length} />
        <Card title="Open" value={counts.open} />
        <Card title="AI analysis" value={analysis ? "Complete" : "Not run"} />
      </div>

      <section>
        <div className="mb-2 flex flex-wrap items-center gap-3">
          <h2 className="text-lg font-medium text-white">AI analysis</h2>
          <ScanAnalysisActions scanId={scan.id} analysed={analysis !== null} />
        </div>
        {analysis === null ? (
          <EmptyState
            title="No analysis yet"
            hint="This scan's evidence has been ingested but not correlated. Run the analysis to produce findings and the analyst's read."
          />
        ) : (
          <div className="space-y-4">
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
              <p className="text-sm text-slate-200">{analysis.summary}</p>
              {analysis.risk_assessment && (
                <p className="mt-3 text-sm text-slate-400">{analysis.risk_assessment}</p>
              )}
            </div>
            <AnalysisLists analysis={analysis} />
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-2 text-lg font-medium text-white">Assets in this scan</h2>
        {assets.length === 0 ? (
          <EmptyState title="No assets in this scan" hint="The uploaded file did not contain any hosts." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <caption className="sr-only">Hosts observed by this scan</caption>
              <thead>
                <tr className="text-left text-slate-500">
                  <th scope="col" className="pb-2">IP</th>
                  <th scope="col" className="pb-2">Hostname</th>
                  <th scope="col" className="pb-2">OS</th>
                  <th scope="col" className="pb-2">Services</th>
                  <th scope="col" className="pb-2">Exposure</th>
                </tr>
              </thead>
              <tbody>
                {assets.map((a) => (
                  <tr key={a.id} className="border-t border-slate-800">
                    <td className="py-2 font-mono text-slate-200">
                      <Link className="text-sky-400 hover:underline" href={`/assets/${a.ip}`}>{a.ip}</Link>
                    </td>
                    <td className="py-2 text-slate-300">{a.hostname ?? "—"}</td>
                    <td className="py-2 text-slate-300">{a.os ?? "—"}</td>
                    <td className="py-2">{a.services.length}</td>
                    <td className="py-2">{a.exposure}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-2 text-lg font-medium text-white">Findings</h2>
        {findings.length === 0 ? (
          <EmptyState
            title="No findings from this scan"
            hint="Findings appear once this scan has been analysed."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <caption className="sr-only">Findings raised by this scan, highest risk first</caption>
              <thead>
                <tr className="text-left text-slate-500">
                  <th scope="col" className="pb-2">Severity</th>
                  <th scope="col" className="pb-2">Title</th>
                  <th scope="col" className="pb-2">Asset</th>
                  <th scope="col" className="pb-2">Service</th>
                  <th scope="col" className="pb-2">Risk</th>
                  <th scope="col" className="pb-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {findings.map((f) => (
                  <tr key={f.id} className="border-t border-slate-800">
                    <td className="py-2"><SeverityBadge severity={f.severity} /></td>
                    <td className="py-2">
                      <Link className="text-sky-400 hover:underline" href={`/findings/${f.id}`}>{f.title}</Link>
                    </td>
                    <td className="py-2 font-mono text-slate-300">
                      {f.asset ? (
                        <Link className="text-sky-400 hover:underline" href={`/assets/${f.asset.ip}`}>{f.asset.ip}</Link>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="py-2 font-mono text-slate-300">
                      {f.affected_service ? `${f.affected_service.port}/${f.affected_service.protocol}` : "—"}
                    </td>
                    <td className="py-2">{f.risk_score}</td>
                    <td className="py-2"><StatusBadge status={f.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <Link className="inline-block text-sm text-sky-400 hover:underline" href="/">
        Back to overview
      </Link>
    </div>
  );
}
