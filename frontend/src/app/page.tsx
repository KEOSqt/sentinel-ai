import { apiGet, Asset, Finding, Scan } from "@/lib/api";
import { Card, SeverityBadge } from "@/lib/ui";


export const instant = false;

export default async function OverviewPage() {
  const [assets, findings, scans] = await Promise.all([
    apiGet<Asset[]>("/api/v1/assets"),
    apiGet<Finding[]>("/api/v1/findings"),
    apiGet<Scan[]>("/api/v1/scans"),
  ]);

  const assetList = assets ?? [];
  const findingList = findings ?? [];
  const scanList = scans ?? [];

  const counts = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"].map((sev) => ({
    severity: sev,
    count: findingList.filter((f) => f.severity === sev).length,
  }));
  const topRisk = findingList.length ? Math.max(...findingList.map((f) => f.risk_score)) : 0;

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold text-white">Security Overview</h1>

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
        {scanList.length === 0 ? (
          <p className="text-sm text-slate-500">No scans yet. Upload Nmap XML on the Scan page.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500">
                <th className="pb-2">Filename</th>
                <th className="pb-2">Status</th>
                <th className="pb-2">Assets</th>
                <th className="pb-2">Findings</th>
                <th className="pb-2">Created</th>
              </tr>
            </thead>
            <tbody>
              {scanList.slice(0, 5).map((s) => (
                <tr key={s.id} className="border-t border-slate-800">
                  <td className="py-2 text-slate-200">{s.filename ?? s.id}</td>
                  <td className="py-2">{s.status}</td>
                  <td className="py-2">{s.asset_count}</td>
                  <td className="py-2">{s.finding_count}</td>
                  <td className="py-2 text-slate-500">{s.created_at ? new Date(s.created_at).toLocaleString() : "â€”"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
