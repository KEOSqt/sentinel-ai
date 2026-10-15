import Link from "next/link";
import { ApiErrorState } from "@/components/api-error-state";
import { apiGet, type Finding } from "@/lib/api";
import { EmptyState, SeverityBadge } from "@/lib/ui";

export const instant = false;

export default async function FindingsPage() {
  const result = await apiGet<Finding[]>("/api/v1/findings");

  if (!result.ok) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold text-white">Findings</h1>
        <ApiErrorState errors={[result.error]} />
      </div>
    );
  }

  const findings = result.data;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-white">Findings</h1>
      {findings.length === 0 ? (
        <EmptyState
          title="No findings yet"
          hint="Upload an Nmap XML file on the Scan page, then run the analysis to generate findings."
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <caption className="sr-only">
              Security findings ordered by risk score, highest first
            </caption>
            <thead>
              <tr className="text-left text-slate-500">
                <th scope="col" className="pb-2">Severity</th>
                <th scope="col" className="pb-2">Title</th>
                <th scope="col" className="pb-2">Asset</th>
                <th scope="col" className="pb-2">Risk</th>
                <th scope="col" className="pb-2">Confidence</th>
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
                  <td className="py-2 font-mono text-slate-300">{f.asset?.ip ?? "—"}</td>
                  <td className="py-2">{f.risk_score}</td>
                  <td className="py-2">{f.confidence}</td>
                  <td className="py-2">{f.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}