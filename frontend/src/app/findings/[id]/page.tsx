import { apiGet, Finding } from "@/lib/api";
import { SeverityBadge } from "@/lib/ui";


export const instant = false;

export default async function FindingDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const finding = await apiGet<Finding>(`/api/v1/findings/${id}`);

  if (!finding) {
    return <p className="text-sm text-slate-500">Finding not found.</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <SeverityBadge severity={finding.severity} />
        <h1 className="text-2xl font-semibold text-white">{finding.title}</h1>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <div><p className="text-xs text-slate-500">Risk Score</p><p className="text-xl text-white">{finding.risk_score}</p></div>
        <div><p className="text-xs text-slate-500">Confidence</p><p className="text-xl text-white">{finding.confidence}</p></div>
        <div><p className="text-xs text-slate-500">Asset</p><p className="text-xl font-mono text-white">{finding.asset?.ip ?? "—"}</p></div>
        <div><p className="text-xs text-slate-500">Status</p><p className="text-xl text-white">{finding.status}</p></div>
      </div>

      <section>
        <h2 className="mb-1 text-lg font-medium text-white">Description</h2>
        <p className="text-sm text-slate-300">{finding.description || "—"}</p>
      </section>

      <section>
        <h2 className="mb-1 text-lg font-medium text-white">Rationale</h2>
        <p className="text-sm text-slate-300">{finding.rationale}</p>
      </section>

      <section>
        <h2 className="mb-1 text-lg font-medium text-white">Affected Service</h2>
        <p className="text-sm text-slate-300">
          {finding.affected_service
            ? `${finding.affected_service.service} on ${finding.affected_service.port}/${finding.affected_service.protocol} ${finding.affected_service.version ?? ""}`
            : "—"}
        </p>
      </section>

      <section>
        <h2 className="mb-1 text-lg font-medium text-white">Evidence</h2>
        <ul className="list-disc space-y-1 pl-5 text-sm text-slate-300">
          {finding.evidence.map((e, i) => (
            <li key={i}>{e.source} / {e.evidence_type}: <code>{JSON.stringify(e.data)}</code></li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="mb-1 text-lg font-medium text-white">Remediation</h2>
        <p className="text-sm text-slate-300">{finding.remediation}</p>
      </section>

      {finding.references.length > 0 && (
        <section>
          <h2 className="mb-1 text-lg font-medium text-white">References</h2>
          <ul className="list-disc pl-5 text-sm text-sky-400">
            {finding.references.map((r) => (
              <li key={r}><a href={r}>{r}</a></li>
            ))}
          </ul>
        </section>
      )}

      {finding.ai_analysis && (
        <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
          <h2 className="mb-2 text-lg font-medium text-white">AI Analysis</h2>
          <p className="mb-2 text-sm text-slate-300">{finding.ai_analysis.summary}</p>
          <p className="mb-2 text-sm text-slate-300">{finding.ai_analysis.risk_assessment}</p>
          {finding.ai_analysis.attack_paths.length > 0 && (
            <>
              <h3 className="text-sm font-medium text-slate-400">Attack Paths</h3>
              <ul className="list-disc pl-5 text-sm text-slate-300">
                {finding.ai_analysis.attack_paths.map((p, i) => <li key={i}>{p}</li>)}
              </ul>
            </>
          )}
          <h3 className="mt-2 text-sm font-medium text-slate-400">Recommendations</h3>
          <ul className="list-disc pl-5 text-sm text-slate-300">
            {finding.ai_analysis.recommendations.map((r, i) => <li key={i}>{r}</li>)}
          </ul>
        </section>
      )}
    </div>
  );
}
