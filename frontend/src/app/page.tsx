"use client";

import { useEffect, useState } from "react";
import { ApiErrorState } from "@/components/api-error-state";
import { apiGet, type ApiError, type Asset, type Finding, type Scan } from "@/lib/api";
import { Card, EmptyState, PageSkeleton, SeverityBadge } from "@/lib/ui";
import Link from "next/link";

const SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"] as const;

export default function OverviewPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);
  const [failures, setFailures] = useState<ApiError[]>([]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const [assetsResult, findingsResult, scansResult] = await Promise.all([
        apiGet<Asset[]>("/api/v1/assets"),
        apiGet<Finding[]>("/api/v1/findings"),
        apiGet<Scan[]>("/api/v1/scans"),
      ]);
      if (cancelled) return;
      const allFailures = [assetsResult, findingsResult, scansResult]
        .filter((r) => !r.ok)
        .map((r) => (r as { ok: false; error: ApiError }).error);
      if (allFailures.length === 3) {
        setFailures(allFailures);
      } else {
        if (assetsResult.ok) setAssets(assetsResult.data);
        if (findingsResult.ok) setFindings(findingsResult.data);
        if (scansResult.ok) setScans(scansResult.data);
      }
      setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return <PageSkeleton />;
  }

  if (failures.length > 0 && (assets.length === 0 && findings.length === 0 && scans.length === 0)) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold text-white">Security Overview</h1>
        <ApiErrorState errors={failures} />
      </div>
    );
  }

  const partialFailures = (assets.length === 0 || findings.length === 0 || scans.length === 0) ? failures : [];

  const counts = SEVERITIES.map((sev) => ({
    severity: sev,
    count: findings.filter((f) => f.severity === sev).length,
  }));
  const topRisk = findings.length ? Math.max(...findings.map((f) => f.risk_score)) : 0;

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold text-white">Security Overview</h1>

      {partialFailures.length > 0 && (
        <ApiErrorState title="Some data could not be loaded" errors={partialFailures} />
      )}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card title="Top Risk Score" value={topRisk} />
        <Card title="Assets" value={assets.length} />
        <Card title="Findings" value={findings.length} />
        <Card title="Scans" value={scans.length} />
      </div>

      <section>
        <h2 className="mb-3 text-lg font-medium text-white">Findings by Severity</h2>
        <div className="flex flex-wrap gap-3">
          {counts.map((c) => (
            <div key={c.severity} className="rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3">
              <SeverityBadge severity={c.severity} />
              <p className="mt-2 text-xl font-semibold text-white">{c.count}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-medium text-white">Recent Scans</h2>
        {scans.length === 0 ? (
          <EmptyState
            title="No scans yet"
            hint="Upload an Nmap XML file on the Scan page to populate this dashboard."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <caption className="sr-only">Most recent scans and their result counts</caption>
              <thead>
                <tr className="text-left text-slate-500">
                  <th scope="col" className="pb-2">Filename</th>
                  <th scope="col" className="pb-2">Status</th>
                  <th scope="col" className="pb-2">Assets</th>
                  <th scope="col" className="pb-2">Findings</th>
                  <th scope="col" className="pb-2">Created</th>
                </tr>
              </thead>
              <tbody>
                {scans.slice(0, 5).map((s) => (
                  <tr key={s.id} className="border-t border-slate-800">
                    <td className="py-2 text-slate-200">
                      <Link className="text-sky-400 hover:underline" href={`/scans/${s.id}`}>{s.filename ?? s.id}</Link>
                    </td>
                    <td className="py-2">{s.status}</td>
                    <td className="py-2">{s.asset_count}</td>
                    <td className="py-2">{s.finding_count}</td>
                    <td className="py-2 text-slate-500">{s.created_at ? new Date(s.created_at).toLocaleString() : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
