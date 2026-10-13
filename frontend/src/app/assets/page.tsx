import { apiGet, Asset } from "@/lib/api";


export const instant = false;

export default async function AssetsPage() {
  const assets = (await apiGet<Asset[]>("/api/v1/assets")) ?? [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-white">Assets</h1>
      {assets.length === 0 ? (
        <p className="text-sm text-slate-500">No assets discovered yet.</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500">
              <th className="pb-2">IP</th>
              <th className="pb-2">Hostname</th>
              <th className="pb-2">OS</th>
              <th className="pb-2">Services</th>
            </tr>
          </thead>
          <tbody>
            {assets.map((a) => (
              <tr key={a.id} className="border-t border-slate-800 align-top">
                <td className="py-2 font-mono text-slate-200">{a.ip}</td>
                <td className="py-2">{a.hostname ?? "â€”"}</td>
                <td className="py-2">{a.os ?? "â€”"}</td>
                <td className="py-2">
                  <ul className="space-y-1">
                    {a.services.map((s) => (
                      <li key={`${s.port}-${s.protocol}`} className="text-slate-300">
                        <span className="font-mono">{s.port}/{s.protocol}</span> {s.service}
                        {s.version ? <span className="text-slate-500"> â€” {s.version}</span> : null}
                        <span className={`ml-2 text-xs ${s.state === "open" ? "text-emerald-400" : "text-slate-500"}`}>{s.state}</span>
                      </li>
                    ))}
                  </ul>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
