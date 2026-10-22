"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { notFound, useParams } from "next/navigation";
import { ApiErrorState } from "@/components/api-error-state";
import { FindingTriage } from "@/components/finding-triage";
import { apiGet, type ApiError, type Finding } from "@/lib/api";
import { useRetry } from "@/lib/use-retry";
import { PageSkeleton, SeverityBadge, StatusBadge } from "@/lib/ui";

export default function FindingDetailPage() {
  const { id } = useParams();
  const idStr = Array.isArray(id) ? id[0] : id;
  const [finding, setFinding] = useState<Finding | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [notFoundRoute, setNotFoundRoute] = useState(false);
  const { attempt, retry } = useRetry();

  function handleRetry() {
    setLoading(true);
    setError(null);
    retry();
  }

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const result = await apiGet<Finding>(`/api/v1/findings/${idStr}`);
      if (cancelled) return;
      if (!result.ok) {
        if (result.error.kind === "http" && result.error.status === 404) {
          setNotFoundRoute(true);
        } else {
          setError(result.error);
        }
      } else {
        setFinding(result.data);
      }
      setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, [attempt, idStr]);

  if (notFoundRoute) {
    notFound();
  }

  if (loading) {
    return <PageSkeleton />;
  }

  if (error !== null) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold text-white">Finding</h1>
        <ApiErrorState errors={[error]} onRetry={handleRetry} />
        <Link className="inline-block text-sm text-sky-400 hover:underline" href="/findings">
          Back to findings
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <SeverityBadge severity={finding!.severity} />
        <h1 className="text-2xl font-semibold text-white">{finding!.title}</h1>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <div><p className="text-xs text-slate-500">Risk Score</p><p className="text-xl text-white">{finding!.risk_score}</p></div>
        <div><p className="text-xs text-slate-500">Confidence</p><p className="text-xl text-white">{finding!.confidence}</p></div>
        <div>
          <p className="text-xs text-slate-500">Asset</p>
          <p className="text-xl font-mono">
            {finding!.asset?.ip ? (
              <Link className="text-white hover:text-sky-400 hover:underline" href={`/assets/${encodeURIComponent(finding!.asset.ip)}`}>
                {finding!.asset.ip}
              </Link>
            ) : (
              <span className="text-white">—</span>
            )}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Status</p>
          <p className="mt-2 text-xl">
            <StatusBadge status={finding!.status} />
          </p>
        </div>
      </div>

      <FindingTriage
        key={finding!.id}
        findingId={finding!.id}
        initialStatus={finding!.status}
        initialNote={finding!.triage_note ?? ""}
      />

      <section>
        <h2 className="mb-1 text-lg font-medium text-white">Description</h2>
        <p className="text-sm text-slate-300">{finding!.description || "—"}</p>
      </section>

      <section>
        <h2 className="mb-1 text-lg font-medium text-white">Rationale</h2>
        <p className="text-sm text-slate-300">{finding!.rationale}</p>
      </section>

      <section>
        <h2 className="mb-1 text-lg font-medium text-white">Affected Service</h2>
        <p className="text-sm text-slate-300">
          {finding!.affected_service
            ? `${finding!.affected_service.service} on ${finding!.affected_service.port}/${finding!.affected_service.protocol} ${finding!.affected_service.version ?? ""}`
            : "—"}
        </p>
      </section>

      <section>
        <h2 className="mb-1 text-lg font-medium text-white">Evidence</h2>
        <ul className="list-disc space-y-1 pl-5 text-sm text-slate-300">
          {finding!.evidence.map((e, i) => (
            <li key={i}>{e.source} / {e.evidence_type}: <code>{JSON.stringify(e.data)}</code></li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="mb-1 text-lg font-medium text-white">Remediation</h2>
        <p className="text-sm text-slate-300">{finding!.remediation}</p>
      </section>

      {finding!.references.length > 0 && (
        <section>
          <h2 className="mb-1 text-lg font-medium text-white">References</h2>
          <ul className="list-disc pl-5 text-sm text-sky-400">
            {finding!.references.map((r) => (
              <li key={r}>
                <a href={r} target="_blank" rel="noreferrer noopener">{r}</a>
              </li>
            ))}
          </ul>
        </section>
      )}

      {finding!.ai_analysis && (
        <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
          <h2 className="mb-2 text-lg font-medium text-white">AI Analysis</h2>
          <p className="mb-2 text-sm text-slate-300">{finding!.ai_analysis.summary}</p>
          <p className="mb-2 text-sm text-slate-300">{finding!.ai_analysis.risk_assessment}</p>
          {finding!.ai_analysis.attack_paths.length > 0 && (
            <>
              <h3 className="text-sm font-medium text-slate-400">Attack Paths</h3>
              <ul className="list-disc pl-5 text-sm text-slate-300">
                {finding!.ai_analysis.attack_paths.map((p, i) => <li key={i}>{p}</li>)}
              </ul>
            </>
          )}
          <h3 className="mt-2 text-sm font-medium text-slate-400">Recommendations</h3>
          <ul className="list-disc pl-5 text-sm text-slate-300">
            {finding!.ai_analysis.recommendations.map((r, i) => <li key={i}>{r}</li>)}
          </ul>
        </section>
      )}
    </div>
  );
}
