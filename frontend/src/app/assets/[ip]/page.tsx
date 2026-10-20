import Link from "next/link";
import { notFound } from "next/navigation";
import { ApiErrorState } from "@/components/api-error-state";
import { apiGet, type AssetDetail } from "@/lib/api";
import { Card, EmptyState, SeverityBadge, StatusBadge } from "@/lib/ui";

export const instant = false;

function when(value?: string | null) {
  return value ? new Date(value).toLocaleString() : "—";
}

export default async function AssetDetailPage({
  params,
}: {
  params: Promise<{ ip: string }>;
}) {
  const { ip } = await params;
  const result = await apiGet<AssetDetail>(`/api/v1/assets/${encodeURIComponent(ip)}`);

  // A real 404 from the backend means the host genuinely is unknown to us.
  // Anything else is an infrastructure problem and must not be reported as
  // "not found".
  if (!result.ok) {
    if (result.error.kind === "http" && result.error.status === 404) notFound();
    return (
      <div className="space-y-6">
        <h1 className="font-mono text-2xl font-semibold text-white">{ip}</h1>
        <ApiErrorState errors={[result.error]} />
        <Link className="inline-block text-sm text-sky-400 hover:underline" href="/assets">
          Back to assets
        </Link>
      </div>
    );
  }

  const { asset, findings, scans, counts, first_seen, last_seen } = result.data;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-baseline gap-3">
        <h1 className="font-mono text-2xl font-semibold text-white">{asset.ip}</h1>
        {asset.hostname && <span className="text-slate-400">{asset.hostname}</span>}
        {asset.os && <span className="text-sm text-slate-500">{asset.os}</span>}
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card title="Open" value={counts.open} />
        <Card title="Acknowledged" value={counts.acknowledged} />
        <Card title="Resolved" value={counts.resolved} />
        <Card title="Scans" value={scans.length} subtitle={`first seen ${when(first_seen)}`} />
      </div>

      <p className="text-xs text-slate-500">Last seen {when(last_seen)}</p>

      <section>
        <h2 className="mb-2 text-lg font-medium text-white">Services</h2>
        {asset.services.length === 0 ? (
          <EmptyState title="No services recorded" hint="No scan has reported an open port for this host yet." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <caption className="sr-only">Open services discovered on this host</caption>
              <thead>
                <tr className="text-left text-slate-500">
                  <th scope="col" className="pb-2">Port</th>
                  <th scope="col" className="pb-2">Service</th>
                  <th scope="col" className="pb-2">Product</th>
                  <th scope="col" className="pb-2">State</th>
                </tr>
              </thead>
              <tbody>
                {asset.services.map((s) => (
                  <tr key={`${s.port}-${s.protocol}`} className="border-t border-slate-800">
                    <td className="py-2 font-mono text-slate-200">
                      {s.port}/{s.protocol}
                    </td>
                    <td className="py-2">{s.service}</td>
                    <td className="py-2 text-slate-300">
                      {s.product ?? "—"}
                      {s.version ? <span className="text-slate-500"> {s.version}</span> : null}
                    </td>
                    <td className={`py-2 ${s.state === "open" ? "text-emerald-400" : "text-slate-500"}`}>{s.state}</td>
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
            title="No findings for this host"
            hint="Findings appear once a scan containing this asset has been analysed."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <caption className="sr-only">Findings raised against this host, highest risk first</caption>
              <thead>
                <tr className="text-left text-slate-500">
                  <th scope="col" className="pb-2">Severity</th>
                  <th scope="col" className="pb-2">Title</th>
                  <th scope="col" className="pb-2">Service</th>
                  <th scope="col" className="pb-2">Risk</th>
                  <th scope="col" className="pb-2">Status</th>
                  <th scope="col" className="pb-2">Scan</th>
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
                      {f.affected_service ? `${f.affected_service.port}/${f.affected_service.protocol}` : "—"}
                    </td>
                    <td className="py-2">{f.risk_score}</td>
                    <td className="py-2"><StatusBadge status={f.status} /></td>
                    {/* The same title can be raised by several scans, so link to the one that raised it. */}
                    <td className="py-2 font-mono text-xs text-slate-500">
                      {f.scan_id ? (
                        <Link className="text-sky-400 hover:underline" href={`/scans/${f.scan_id}`}>
                          {f.scan_id.slice(0, 8)}
                        </Link>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-2 text-lg font-medium text-white">Scan history</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <caption className="sr-only">Scans that observed this host, newest first</caption>
            <thead>
              <tr className="text-left text-slate-500">
                <th scope="col" className="pb-2">Scanned</th>
                <th scope="col" className="pb-2">Source</th>
                <th scope="col" className="pb-2">File</th>
                <th scope="col" className="pb-2">Status</th>
                <th scope="col" className="pb-2">Assets</th>
                <th scope="col" className="pb-2">Findings</th>
              </tr>
            </thead>
            <tbody>
              {scans.map((s) => (
                <tr key={s.id} className="border-t border-slate-800">
                  <td className="py-2 text-slate-300">{when(s.created_at)}</td>
                  <td className="py-2">{s.source}</td>
                  <td className="py-2 text-slate-300">{s.filename ?? "—"}</td>
                  <td className="py-2">{s.status}</td>
                  <td className="py-2">{s.asset_count}</td>
                  <td className="py-2">{s.finding_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <Link className="inline-block text-sm text-sky-400 hover:underline" href="/assets">
        Back to assets
      </Link>
    </div>
  );
}
