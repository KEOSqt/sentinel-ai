"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { ApiErrorState } from "@/components/api-error-state";
import { apiGet, type Finding, type FindingStatus, type ApiError } from "@/lib/api";
import { useRetry } from "@/lib/use-retry";
import { EmptyState, PageSkeleton, SeverityBadge, StatusBadge } from "@/lib/ui";

const FILTERS: { value: FindingStatus | null; label: string }[] = [
  { value: null, label: "All" },
  { value: "open", label: "Open" },
  { value: "acknowledged", label: "Acknowledged" },
  { value: "resolved", label: "Resolved" },
];

export default function FindingsPage() {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const { attempt, retry } = useRetry();

  function handleRetry() {
    setLoading(true);
    setError(null);
    retry();
  }

  function handleFilterClick() {
    setLoading(true);
    setError(null);
  }

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const status = searchParams.get("status");
      const active = (["open", "acknowledged", "resolved"] as const).find((s) => s === status);
      const query = active ? `?status=${active}` : "";
      const result = await apiGet<Finding[]>(`/api/v1/findings${query}`);
      if (cancelled) return;
      if (!result.ok) {
        setError(result.error);
      } else {
        setFindings(result.data);
      }
      setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, [attempt, pathname, searchParams]);

  if (loading) {
    return <PageSkeleton />;
  }

  if (error !== null) {
    const status = searchParams.get("status");
    const active = (["open", "acknowledged", "resolved"] as const).find((s) => s === status);
    return (
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-semibold text-white">Findings</h1>
          <nav aria-label="Filter findings by status" className="flex gap-2">
            {FILTERS.map((f) => {
              const selected = f.value === active;
              return (
                <Link
                  key={f.label}
                  href={f.value ? `/findings?status=${f.value}` : "/findings"}
                  onClick={handleFilterClick}
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
        <ApiErrorState errors={[error]} onRetry={handleRetry} />
      </div>
    );
  }

  const status = searchParams.get("status");
  const active = (["open", "acknowledged", "resolved"] as const).find((s) => s === status);

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
              onClick={handleFilterClick}
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
                  <td className="py-2 font-mono text-slate-300">
                    {f.asset?.ip ? (
                      <Link className="text-sky-400 hover:underline" href={`/assets/${encodeURIComponent(f.asset.ip)}`}>
                        {f.asset.ip}
                      </Link>
                    ) : (
                      "—"
                    )}
                  </td>
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
