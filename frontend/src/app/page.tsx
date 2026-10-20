import { ApiErrorState } from "@/components/api-error-state";
import { apiGet, type ApiError, type Asset, type Finding, type Scan } from "@/lib/api";
import { Card, EmptyState, SeverityBadge } from "@/lib/ui";
import Link from "next/link";

export const instant = false;

const SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"] as const;

export default async function OverviewPage() {
  const [assetsResult, findingsResult, scansResult] = await Promise.all([
    apiGet<Asset[]>("/api/v1/assets"),
    apiGet<Finding[]>("/api/v1/findings"),
    apiGet<Scan[]>("/api/v1/scans"),
  ]);

  const results = [assetsResult, findingsResult, scansResult];
  const failures = results.filter((r) => !r.ok).map((r) => (r as { ok: false; error: ApiError }).error);
  const totalFailure = failures.length === results.length;

  if (totalFailure) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold text-white">Security Overview</h1>
        <ApiErrorState errors={failures} />
      </div>
    );
  }

  const assetList = assetsResult.ok ? assetsResult.data : [];
  const findingList = findingsResult.ok ? findingsResult.data : [];
  const scanList = scansResult.ok ? scansResult.data : [];

  const counts = SEVERITIES.map((sev) => ({
    severity: sev,
    count: findingList.filter((f) => f.severity === sev).length,
  }));
  const topRisk = findingList.length ? Math.max(...findingList.map((f) => f.risk_score)) : 0;

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold text-white">Security Overview</h1>

      {failures.length > 0 && <ApiErrorState title="Some data could not be loaded" errors={failures} />}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card title="Top Risk Score" value={topRisk} />
        <Card title="Assets" value={assetList.length} />
        <Card title="Findings" value={findingList.length} />
        <Card title="Scans" value={scanList.length} />
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
        {scansResult.ok && scanList.length === 0 ? (
          <EmptyState
            title="No scans yet"
            hint="Upload an Nmap XML file on the Scan page to populate this dashboard."
          />
        ) : scansResult.ok ? (
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
                {scanList.slice(0, 5).map((s) => (
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
        ) : (
          <ApiErrorState title="Recent scans unavailable" errors={[(scansResult as { ok: false; error: ApiError }).error]} />
        )}
      </section>
    </div>
  );
}