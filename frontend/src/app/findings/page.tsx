import { apiGet, Finding } from "@/lib/api";
import { SeverityBadge } from "@/lib/ui";


export const instant = false;

export default async function FindingsPage() {
  const findings = (await apiGet<Finding[]>("/api/v1/findings")) ?? [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-white">Findings</h1>
      {findings.length === 0 ? (
        <p className="text-sm text-slate-500">No findings yet.</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500">
              <th className="pb-2">Severity</th>
              <th className="pb-2">Title</th>
              <th className="pb-2">Asset</th>
              <th className="pb-2">Risk</th>
              <th className="pb-2">Confidence</th>
              <th className="pb-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {findings.map((f) => (
              <tr key={f.id} className="border-t border-slate-800">
                <td className="py-2"><SeverityBadge severity={f.severity} /></td>
                <td className="py-2">
                  <a className="text-sky-400 hover:underline" href={`/findings/${f.id}`}>{f.title}</a>
                </td>
                <td className="py-2 font-mono text-slate-300">{f.asset?.ip ?? "â€”"}</td>
                <td className="py-2">{f.risk_score}</td>
                <td className="py-2">{f.confidence}</td>
                <td className="py-2">{f.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
