import { ApiErrorState } from "@/components/api-error-state";
import { apiGet, type Asset } from "@/lib/api";
import { EmptyState } from "@/lib/ui";

export const instant = false;

export default async function AssetsPage() {
  const result = await apiGet<Asset[]>("/api/v1/assets");

  if (!result.ok) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold text-white">Assets</h1>
        <ApiErrorState errors={[result.error]} />
      </div>
    );
  }

  const assets = result.data;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-white">Assets</h1>
      {assets.length === 0 ? (
        <EmptyState
          title="No assets discovered yet"
          hint="Upload an Nmap XML file on the Scan page to discover hosts and services."
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <caption className="sr-only">
              Discovered assets with hostname, operating system, and open services
            </caption>
            <thead>
              <tr className="text-left text-slate-500">
                <th scope="col" className="pb-2">IP</th>
                <th scope="col" className="pb-2">Hostname</th>
                <th scope="col" className="pb-2">OS</th>
                <th scope="col" className="pb-2">Services</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((a) => (
                <tr key={a.id} className="border-t border-slate-800 align-top">
                  <td className="py-2 font-mono text-slate-200">{a.ip}</td>
                  <td className="py-2">{a.hostname ?? "—"}</td>
                  <td className="py-2">{a.os ?? "—"}</td>
                  <td className="py-2">
                    <ul className="space-y-1">
                      {a.services.map((s) => (
                        <li key={`${s.port}-${s.protocol}`} className="text-slate-300">
                          <span className="font-mono">{s.port}/{s.protocol}</span> {s.service}
                          {s.version ? <span className="text-slate-500"> — {s.version}</span> : null}
                          <span className={`ml-2 text-xs ${s.state === "open" ? "text-emerald-400" : "text-slate-500"}`}>{s.state}</span>
                        </li>
                      ))}
                    </ul>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}