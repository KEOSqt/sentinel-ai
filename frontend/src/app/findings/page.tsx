import Link from "next/link";
import { ApiErrorState } from "@/components/api-error-state";
import { apiGet, type Finding, type FindingStatus } from "@/lib/api";
import { EmptyState, SeverityBadge, StatusBadge } from "@/lib/ui";

export const instant = false;

const FILTERS: { value: FindingStatus | null; label: string }[] = [
  { value: null, label: "All" },
  { value: "open", label: "Open" },
  { value: "acknowledged", label: "Acknowledged" },
  { value: "resolved", label: "Resolved" },
];

export default async function FindingsPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string }>;
}) {
  const params = await searchParams;
  const active = (["open", "acknowledged", "resolved"] as const).find((s) => s === params.status);
  const query = active ? `?status=${active}` : "";

  const result = await apiGet<Finding[]>(`/api/v1/findings${query}`);

  const header = (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <h1 className="text-2xl font-semibold text-white">Findings</h1>
      <nav aria-label="Filter findings by status" className="flex gap-2">
        {FILTERS.map((f) => {
          const selected = f.value === active;
          return (
            <Link
              key={f.label}
              href={f.value ? `/findings?status=${f.value}` : "/findings"}
              aria-current={selected ? "page" : undefined}
              className={`rounded-md border px-3 py-1 text-xs font-medium ${
                selected
                  ? "border-sky-500/60 bg-sky-500/20 text-sky-200"
                  : "border-slate-800 text-slate-400 hover:border-slate-600 hover:text-slate-200"
              }`}
            >
              {f.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );

  if (!result.ok) {
    return (
      <div className="space-y-6">
        {header}
        <ApiErrorState errors={[result.error]} />
      </div>
    );
  }

  const findings = result.data;

  return (
    <div className="space-y-6">
      {header}

      {findings.length === 0 ? (
        <EmptyState
          title={active ? `No ${active} findings` : "No findings yet"}
          hint={
            active
              ? "Try a different status filter."
              : "Upload an Nmap XML file on the Scan page, then run the analysis to generate findings."
          }
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
                  <td className="py-2"><StatusBadge status={f.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}